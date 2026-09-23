"""Production FastAPI entry point for Haile Revenue OS.

Weather polling is intentionally request-driven. Deploy cron/weather-cron.sh
(or an equivalent Supabase/Vercel/Railway scheduled job) to call the protected
/api/v1/cron/weather endpoint every five minutes. This avoids relying on a
long-lived asyncio task, which is unsafe on serverless platforms.
"""

from __future__ import annotations

import asyncio
import hmac
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from schemas import (
    CampaignRecord,
    CronRunResponse,
    StatsResponse,
    TestCampaignRequest,
    TestCampaignResponse,
    WeatherSnapshot,
)
from supabase_repository import ConfigurationError, SupabaseRepository, get_repository

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("haile-revenue")

OWM_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
CRON_SECRET = os.getenv("CRON_SECRET", "").strip()
TRIGGER_TEMP_C = float(os.getenv("TRIGGER_TEMP_C", "28"))
ADAMA_LAT = float(os.getenv("ADAMA_LAT", "8.5407"))
ADAMA_LON = float(os.getenv("ADAMA_LON", "39.2700"))
POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "300"))
EAT = timezone(timedelta(hours=3))

allowed_origins = [origin.strip().rstrip("/") for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
if not allowed_origins:
    raise RuntimeError("CORS_ORIGINS must contain at least one explicit origin")

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app = FastAPI(title="Haile Revenue OS API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Cron-Secret"],
)


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(_: Request, exc: ConfigurationError) -> JSONResponse:
    logger.error("Backend configuration error: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "Backend service is not configured"})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Invalid request payload", "errors": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def repository() -> SupabaseRepository:
    return get_repository()


def verify_cron_secret(x_cron_secret: str | None = Header(default=None)) -> None:
    if not CRON_SECRET or not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron credentials")


async def fetch_weather() -> WeatherSnapshot:
    if not OWM_API_KEY:
        raise ConfigurationError("OPENWEATHER_API_KEY is required")
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": ADAMA_LAT, "lon": ADAMA_LON, "appid": OWM_API_KEY, "units": "metric"},
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    main = payload.get("main", {})
    weather = payload.get("weather", [{}])[0]
    return WeatherSnapshot(
        ts=datetime.now(EAT).isoformat(),
        temp_c=float(main["temp"]),
        feels_like_c=float(main["feels_like"]) if main.get("feels_like") is not None else None,
        condition=str(weather.get("main", "Unknown")),
        description=str(weather.get("description", "")),
        humidity=int(main["humidity"]) if main.get("humidity") is not None else None,
    )


async def send_telegram(text: str) -> int | None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        return None
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": "HTML"},
        )
    if response.status_code != 200:
        logger.warning("Telegram request failed with status %s", response.status_code)
        return None
    result = response.json().get("result", {})
    message_id = result.get("message_id")
    return int(message_id) if message_id is not None else None


def make_message(weather: WeatherSnapshot) -> str:
    variants = [
        f"🔥 <b>Adama is {weather.temp_c:.0f}°C right now</b>\n\nPool is empty. Drinks are cold. Music is on.\n\nShow this message at Haile Resort for 30 birr entry (was 50).\nValid until 6 PM. First 100 guests.",
        f"☀️ <b>Perfect day alert: {weather.temp_c:.0f}°C, {weather.description}</b>\n\nHaile Resort pool is calling.\n\n<b>25 birr day pass</b> for the next 3 hours.",
        f"🌡️ <b>It's {weather.temp_c:.0f}°C in Adama</b>\n\nFree cocktail with any pool entry today.\nShow this message — entry is 30 birr (down from 50).",
    ]
    return variants[datetime.now(EAT).hour % len(variants)]


async def run_weather_cycle(repo: SupabaseRepository, target_segment: str) -> tuple[WeatherSnapshot, int | None, bool]:
    weather = await fetch_weather()
    inserted = await asyncio.to_thread(repo.insert_weather, weather.model_dump(exclude_none=True))
    snapshot = WeatherSnapshot.model_validate(inserted)
    if snapshot.temp_c < TRIGGER_TEMP_C:
        return snapshot, None, False
    message_id = await send_telegram(make_message(snapshot))
    recipients = await asyncio.to_thread(repo.count_leads)
    campaign = {
        "ts": snapshot.ts,
        "temp_c": snapshot.temp_c,
        "condition": snapshot.condition,
        "target_segment": target_segment,
        "message": make_message(snapshot),
        "telegram_message_id": message_id,
        "status": "sent" if message_id is not None else "queued",
        "recipients": recipients,
    }
    created = await asyncio.to_thread(repo.insert_campaign, campaign)
    return snapshot, int(created["id"]), True


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/stats", response_model=StatsResponse)
@limiter.limit("60/minute")
async def get_stats(request: Request, repo: SupabaseRepository = Depends(repository)) -> StatsResponse:
    latest = await asyncio.to_thread(repo.latest_weather)
    today = datetime.now(EAT).date().isoformat()
    campaigns_today = await asyncio.to_thread(repo.count_campaigns_today, f"{today}T00:00:00+03:00")
    total_leads = await asyncio.to_thread(repo.count_leads)
    if latest is None:
        return StatsResponse(total_leads=total_leads, campaigns_today=campaigns_today, messages_sent_today=campaigns_today, next_check_seconds=POLL_INTERVAL_SEC)
    snapshot = WeatherSnapshot.model_validate(latest)
    return StatsResponse(
        temp_c=snapshot.temp_c,
        condition=snapshot.condition,
        last_check=snapshot.ts,
        campaigns_today=campaigns_today,
        messages_sent_today=campaigns_today,
        total_leads=total_leads,
        next_check_seconds=POLL_INTERVAL_SEC,
        trigger_active=snapshot.temp_c >= TRIGGER_TEMP_C,
    )


@app.get("/api/v1/campaigns", response_model=list[CampaignRecord])
@limiter.limit("60/minute")
async def get_campaigns(request: Request, repo: SupabaseRepository = Depends(repository)) -> list[CampaignRecord]:
    rows = await asyncio.to_thread(repo.recent_campaigns)
    return [CampaignRecord.model_validate(row) for row in rows]


@app.post("/api/v1/campaigns/test", response_model=TestCampaignResponse)
@limiter.limit("5/minute")
async def trigger_test_campaign(
    request: Request,
    payload: TestCampaignRequest,
    repo: SupabaseRepository = Depends(repository),
) -> TestCampaignResponse:
    snapshot, _, _ = await run_weather_cycle(repo, payload.target_segment)
    recipients = await asyncio.to_thread(repo.count_leads)
    return TestCampaignResponse(status="success", temp_c=snapshot.temp_c, recipients=recipients)


@app.post("/api/v1/cron/weather", response_model=CronRunResponse, dependencies=[Depends(verify_cron_secret)])
@limiter.limit("20/hour")
async def run_cron_weather(request: Request, repo: SupabaseRepository = Depends(repository)) -> CronRunResponse:
    snapshot, campaign_id, triggered = await run_weather_cycle(repo, "regular,family,vip")
    return CronRunResponse(status="completed", triggered=triggered, campaign_id=campaign_id, snapshot=snapshot)
