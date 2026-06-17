"""
Haile Revenue OS — backend MVP
Polls Adama weather every 5 min, broadcasts to Telegram when temp >= 28°C.
"""
import asyncio
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

# ---------- Config ----------
OWM_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TRIGGER_TEMP_C = float(os.getenv("TRIGGER_TEMP_C", "28"))
ADAMA_LAT = float(os.getenv("ADAMA_LAT", "8.5407"))
ADAMA_LON = float(os.getenv("ADAMA_LON", "39.2700"))
POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "300"))
DB_PATH = os.getenv("DB_PATH", "./haile.db")

EAT = timezone(timedelta(hours=3))


# ---------- DB ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS weather_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            temp_c REAL,
            feels_like_c REAL,
            condition TEXT,
            description TEXT,
            humidity INTEGER
        );
        CREATE TABLE IF NOT EXISTS campaign (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            temp_c REAL,
            condition TEXT,
            target_segment TEXT,
            message TEXT,
            telegram_message_id INTEGER,
            status TEXT,
            recipients INTEGER
        );
        CREATE TABLE IF NOT EXISTS lead (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            tier TEXT DEFAULT 'regular',
            telegram_chat_id TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_campaign_ts ON campaign(ts);
        CREATE INDEX IF NOT EXISTS idx_lead_tier ON lead(tier);
        """)
        # Seed some leads if empty (for the demo)
        cur = conn.execute("SELECT COUNT(*) c FROM lead")
        if cur.fetchone()["c"] == 0:
            sample = [
                ("Abebe K.", "vip", "@abebe_vip"),
                ("Sara M.", "family", "@sara_m"),
                ("Daniel T.", "regular", "@daniel_t"),
                ("Hanna G.", "regular", "@hanna_g"),
                ("Yonas B.", "price-sensitive", "@yonas_b"),
                ("Meron A.", "vip", "@meron_a"),
                ("Bekele F.", "family", "@bekele_f"),
                ("Tigist H.", "regular", "@tigist_h"),
            ]
            now = datetime.now(EAT).isoformat()
            conn.executemany(
                "INSERT INTO lead (name, tier, telegram_chat_id, created_at) VALUES (?, ?, ?, ?)",
                [(n, t, c, now) for n, t, c in sample],
            )


# ---------- Models ----------
class Weather(BaseModel):
    temp_c: float
    feels_like_c: Optional[float] = None
    condition: str
    description: str
    humidity: Optional[int] = None
    ts: str


class Campaign(BaseModel):
    id: int
    ts: str
    temp_c: float
    condition: str
    target_segment: str
    message: str
    status: str
    recipients: int


class Stats(BaseModel):
    temp_c: Optional[float] = None
    condition: Optional[str] = None
    last_check: Optional[str] = None
    campaigns_today: int = 0
    messages_sent_today: int = 0
    total_leads: int = 0
    next_check_seconds: int = POLL_INTERVAL_SEC
    trigger_active: bool = False


# ---------- Weather ----------
async def fetch_weather() -> Weather:
    """Call OpenWeatherMap for Adama, return normalized Weather."""
    if not OWM_API_KEY:
        raise HTTPException(500, "OPENWEATHER_API_KEY not set")
    url = "https://openweathermap.org"
    params = {
        "lat": ADAMA_LAT,
        "lon": ADAMA_LON,
        "appid": OWM_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        p = r.json()
    return Weather(
        temp_c=p["main"]["temp"],
        feels_like_c=p["main"].get("feels_like"),
        condition=p["weather"][0]["main"] if p.get("weather") else "Unknown",
        description=p["weather"][0]["description"] if p.get("weather") else "",
        humidity=p["main"].get("humidity"),
        ts=datetime.now(EAT).isoformat(),
    )


# ---------- Telegram ----------
async def send_telegram(text: str) -> Optional[int]:
    """Post a message to the configured Telegram channel. Returns message_id."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        return None
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            url,
            json={"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": "HTML"},
        )
    if r.status_code == 200:
        return r.json().get("result", {}).get("message_id")
    return None


# ---------- Copywriter (simple, no Gemini needed for MVP) ----------
def make_message(weather: Weather) -> str:
    """Generate a varied broadcast message. In production this would call Gemini."""
    variants = [
        (
            f"🔥 <b>Adama is {weather.temp_c:.0f}°C right now</b>\n\n"
            f"Pool is empty. Drinks are cold. Music is on.\n\n"
            f"Show this message at Haile Resort for 30 birr entry (was 50).\n"
            f"Valid until 6 PM. First 100 guests.\n\n"
            f"📍 See you by the pool."
        ),
        (
            f"☀️ <b>Perfect day alert: {weather.temp_c:.0f}°C, {weather.description}</b>\n\n"
            f"Don't waste it indoors. Haile Resort pool is calling.\n\n"
            f"<b>25 birr day pass</b> for the next 3 hours.\n"
            f"Bring a friend, both pay 40 instead of 50.\n\n"
            f"📍 <i>Haile Resort, Adama</i>"
        ),
        (
            f"🌡️ <b>It's {weather.temp_c:.0f}°C in Adama</b>\n\n"
            f"Our pool is at the perfect temperature. Yours should be too.\n\n"
            f"Free cocktail with any pool entry today.\n"
            f"Show this message — entry is 30 birr (down from 50).\n\n"
            f"📍 <b>Haile Resort</b> — open until 9 PM"
        ),
    ]
    # Rotate by hour so consecutive broadcasts use different copy
    idx = datetime.now(EAT).hour % len(variants)
    return variants[idx]


# ---------- Trigger loop ----------
async def trigger_loop(stop_event: asyncio.Event):
    """Background task: poll weather, fire campaign if temp >= threshold."""
    print(f"[scheduler] started. Polling every {POLL_INTERVAL_SEC}s, trigger at {TRIGGER_TEMP_C}°C")
    while not stop_event.is_set():
        try:
            w = await fetch_weather()
            with db() as conn:
                conn.execute(
                    "INSERT INTO weather_snapshot (ts, temp_c, feels_like_c, condition, description, humidity) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (w.ts, w.temp_c, w.feels_like_c, w.condition, w.description, w.humidity),
                )
            triggered = w.temp_c >= TRIGGER_TEMP_C
            print(f"[weather] {w.temp_c:.1f}°C {w.condition} | triggered={triggered}")
            if triggered:
                message = make_message(w)
                msg_id = await send_telegram(message)
                with db() as conn:
                    # Count leads in target segment (use 'regular' for the broadcast)
                    n = conn.execute(
                        "SELECT COUNT(*) c FROM lead WHERE tier IN ('regular', 'family', 'vip')"
                    ).fetchone()["c"]
                    status = "sent" if msg_id else "queued"
                    conn.execute(
                        "INSERT INTO campaign (ts, temp_c, condition, target_segment, message, telegram_message_id, status, recipients) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (w.ts, w.temp_c, w.condition, "regular,family,vip", message, msg_id, status, n),
                    )
        except Exception as e:
            print(f"[scheduler error] {e}")
        await asyncio.sleep(POLL_INTERVAL_SEC)


# ---------- Lifespan Config ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    stop_event = asyncio.Event()
    task = asyncio.create_task(trigger_loop(stop_event))
    yield
    stop_event.set()
    await task


# ---------- FastAPI Server Initialization ----------
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- API Router Endpoints ----------
@app.get("/api/v1/stats", response_model=Stats)
async def get_stats():
    with db() as conn:
        w = conn.execute("SELECT * FROM weather_snapshot ORDER BY id DESC LIMIT 1").fetchone()
        today = datetime.now(EAT).strftime("%Y-%m-%d")
        c_today = conn.execute("SELECT COUNT(*) c FROM campaign WHERE ts LIKE ?", (f"{today}%",)).fetchone()["c"]
        total_leads = conn.execute("SELECT COUNT(*) c FROM lead").fetchone()["c"]
        
    if not w:
        return Stats(total_leads=total_leads)
        
    return Stats(
        temp_c=w["temp_c"],
        condition=w["condition"],
        last_check=w["ts"],
        campaigns_today=c_today,
        messages_sent_today=c_today,
        total_leads=total_leads,
        trigger_active=(w["temp_c"] >= TRIGGER_TEMP_C)
    )


@app.get("/api/v1/campaigns")
async def get_campaigns():
    with db() as conn
            rows = conn.execute("SELECT * FROM campaign ORDER BY id DESC LIMIT 20").fetchall()
             return [dict(r) for r in rows]
@app.post("/api/v1/campaigns/test")
async def trigger_test_campaign():
    try:
        w = await fetch_weather()
        message = make_message(w)
        msg_id = await send_telegram(message)
        
        with db() as conn:
            n = conn.execute("SELECT COUNT(*) c FROM lead").fetchone()["c"]
            conn.execute(
                "INSERT INTO campaign (ts, temp_c, condition, target_segment, message, telegram_message_id, status, recipients) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (w.ts, w.temp_c, w.condition, "all-test", message, msg_id, "sent" if msg_id else "failed", n)
            )
        return {"status": "success", "telegram_message_id": msg_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
