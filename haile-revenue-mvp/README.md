# Haile Revenue OS

Autonomous weather-triggered revenue prototype for hospitality. Polls real-time weather data, evaluates business conditions, broadcasts offers to Telegram, and tracks campaign performance.

## Problem

Seasonal hospitality businesses (resorts, pools, restaurants) have high capacity during peak weather but struggle to fill it predictably. Manual customer outreach is slow and uncoordinated. Decision-making is reactive, not data-driven.

This prototype demonstrates how to automate the workflow: **monitor external conditions → evaluate opportunity → execute notification → measure results**.

## Solution

Haile Revenue OS is an autonomous system that:
- Polls OpenWeatherMap API every 5 minutes for Adama, Ethiopia weather
- Evaluates if temperature ≥ 28°C (configurable threshold)
- Generates time-rotating promotional copy variations
- Sends broadcasts to all registered leads via Telegram Bot API
- Logs campaign performance (recipients, message ID, status) to SQLite
- Provides a real-time dashboard showing weather, trigger state, and campaign history

## How It Works

```
OpenWeatherMap API
        ↓ (every 5 minutes)
Weather Data (temp, condition, humidity)
        ↓
Condition Evaluation (temp >= 28°C?)
        ↓
Campaign Decision (trigger or wait)
        ↓
Message Generation (rotate 3 variants by hour)
        ↓
Telegram Bot API broadcast
        ↓
Campaign Logged to SQLite (status: sent/queued/failed)
        ↓
Frontend Dashboard (live stats, history)
```

### Key Workflow Features

- **Polling**: Every 5 minutes (configurable via `POLL_INTERVAL_SEC`)
- **Threshold**: 28°C by default (configurable via `TRIGGER_TEMP_C`)
- **Message Variants**: 3 promotional templates rotate by hour to avoid repetition
- **Recording**: Each campaign attempt logged with timestamp, temperature, condition, lead count, message ID, status
- **Manual Testing**: "Fire test campaign" button allows immediate broadcast regardless of temperature
- **Lead Segmentation**: Leads stored by tier (vip, family, regular, price-sensitive) for future targeting

## Architecture

### Backend (FastAPI + Python)

**Single file**: `main.py` contains entire backend logic:
- `fetch_weather()`: Async call to OpenWeatherMap API with error handling
- `send_telegram()`: Async call to Telegram Bot API
- `trigger_loop()`: Background task that polls every `POLL_INTERVAL_SEC` seconds
- Database operations (SQLite context manager)
- API endpoints for frontend
- Error logging and resilience (continues on API failures)

**Database (SQLite)**:
- `weather_snapshot`: Historical weather polls (ts, temp_c, condition, humidity, etc.)
- `campaign`: Campaign log (ts, temp_c, message, status, recipients, message_id)
- `lead`: Lead database (name, tier, telegram_chat_id)

**Error Handling**:
- OpenWeatherMap failure: Logs error, continues polling
- Telegram failure: Logs error, marks campaign as "queued" instead of "sent"
- Missing config: Returns HTTP 500 if API keys not set
- All exceptions caught in `trigger_loop()` to prevent crash

### Frontend (Next.js 14 + React + Tailwind)

**Dashboard** (`app/page.tsx`):
- Live weather display (temperature, condition, icon)
- Trigger status indicator (🔥 ACTIVE when temp ≥ threshold)
- Stats cards (campaigns today, messages sent, total leads, trigger state)
- Campaign history (recent 20 campaigns, status badges, message preview)
- Manual test button with result feedback
- Auto-refresh every 30 seconds

**API Integration** (`lib/api.ts`):
- Calls backend `/api/v1/stats` and `/api/v1/campaigns` endpoints
- Graceful degradation if backend unavailable

### Deployment

- **Backend**: FastAPI runs on Railway (auto-detected Python, uses uvicorn)
- **Frontend**: Next.js static build deployed to Vercel
- **Database**: SQLite file persisted to Railway filesystem
- **External APIs**: OpenWeatherMap (weather), Telegram (messaging)

## Tech Stack

- **Backend**: FastAPI 0.115.5, uvicorn, httpx, pydantic, python-dotenv
- **Frontend**: Next.js 14, React 19, Tailwind CSS, TypeScript
- **Database**: SQLite3
- **External**: OpenWeatherMap API, Telegram Bot API
- **Deployment**: Railway (backend), Vercel (frontend)

## Running Locally

### Backend Setup

```bash
cd haile-revenue-mvp/backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your real values:
```
OPENWEATHER_API_KEY=your_openweathermap_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=@your_channel_id
TRIGGER_TEMP_C=28
POLL_INTERVAL_SEC=300
```

Start the server:
```bash
python main.py
```

Server runs on `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd haile-revenue-mvp/frontend
npm install
cp .env.local.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start dev server:
```bash
npm run dev
```

Open `http://localhost:3000` in your browser.

### Testing the System

1. Start both backend and frontend locally
2. Open frontend in browser
3. Click **"Fire test campaign"** button
4. Check your Telegram channel — you should receive a message immediately
5. Check the dashboard — a new campaign appears in history
6. Wait for the next poll cycle (5 min default) or manually adjust `TRIGGER_TEMP_C` to current temp to simulate a real trigger

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stats` | Latest weather snapshot, campaign count, lead count, trigger state |
| GET | `/api/v1/campaigns` | Last 20 campaigns (history) |
| POST | `/api/v1/campaigns/test` | Manually trigger campaign regardless of temperature |

## Testing

No automated tests currently exist. Manual testing workflow:

1. **Backend startup**: Confirm no import errors and database initializes
2. **Weather fetch**: Monitor logs for `[weather]` entries showing temp readings
3. **Trigger logic**: Verify trigger only fires when temp ≥ `TRIGGER_TEMP_C`
4. **Database write**: Check SQLite directly: `sqlite3 haile.db "SELECT * FROM campaign"`
5. **Telegram send**: Use test endpoint and verify message arrives in configured channel
6. **Frontend display**: Refresh dashboard and confirm stats update, campaigns appear in history
7. **Error handling**: Disconnect internet or use invalid API key; confirm system logs error and continues

## Failure Handling

### OpenWeatherMap API Down

- **Behavior**: Exception caught in `trigger_loop()`, logged as `[scheduler error]`, loop continues
- **Impact**: No weather data recorded, no trigger decision made for that cycle
- **Recovery**: Automatic retry on next polling interval

### Telegram API Down

- **Behavior**: `send_telegram()` returns `None`, campaign marked as `status: queued`
- **Impact**: Message not sent, but campaign still logged for audit
- **Recovery**: Operator can manually retry or adjust Telegram configuration

### Missing API Keys

- **Behavior**: At startup, FastAPI returns HTTP 500 if keys not set
- **Impact**: Backend does not start; frontend shows no data
- **Recovery**: Set environment variables and restart

### Database Corruption

- **Behavior**: SQLite operations fail, exception caught, logged
- **Impact**: Campaign not recorded; poll continues
- **Recovery**: Delete `haile.db`, backend reinitializes with fresh schema on next start

### Duplicate Trigger Prevention

- **Current**: No explicit deduplication. If the same temperature condition persists across multiple polling intervals, multiple campaigns will be created.
- **Intended behavior** (future): Add timestamp-based deduplication (e.g., only trigger once per hour even if temp stays above threshold).

## Current Limitations

**This is a prototype. The following apply:**

1. **No real revenue generated**: Pricing and offer terms (30 birr, 25 birr, etc.) are mockups. System demonstrates workflow, not production bookings.

2. **Mocked customer fulfillment**: The system sends Telegram messages but does not process customer responses or validate redemption. No booking confirmation, no inventory management.

3. **Free-tier infrastructure**: Relies on free OpenWeatherMap (1,000 calls/day) and free Telegram Bot API. Not production-scale.

4. **No authentication**: All API endpoints are unauthenticated. Anyone with backend URL can call test endpoint.

5. **Single location only**: Hard-coded to Adama, Ethiopia coordinates. Multi-location support would require schema redesign.

6. **No lead acquisition**: Leads are pre-seeded in database. No form for new leads to self-register.

7. **No analytics**: System logs campaigns but provides no ROI analysis, conversion tracking, or A/B testing.

8. **Duplicate campaigns possible**: If temperature stays ≥ 28°C across multiple poll cycles, multiple campaigns fire. This is intentional (real opportunity) but should be configurable.

9. **No rate limiting**: Telegram Bot API has its own limits (30 messages/sec per chat). System does not implement application-level rate limiting.

10. **Time zone dependency**: Uses hardcoded EAT (UTC+3) for Adama. Daylight saving changes not handled.

## Future Improvements

These are realistic next steps:

- **Deduplication**: Track last trigger timestamp; skip if within N hours
- **Lead tiers**: Send different messages to vip, family, regular, price-sensitive segments
- **A/B testing**: Randomly assign variant A or B to each broadcast; track click-through rates
- **Booking integration**: Connect to Telegram inline buttons → redirect to booking form
- **Multi-location**: Add lat/lon parameters to make system reusable for other cities
- **Self-service leads**: Web form for customers to opt-in to Telegram broadcasts
- **Analytics dashboard**: Conversion funnel, cost per booking, ROI by segment
- **Rate limiting**: Queue campaigns if multiple trigger simultaneously
- **Runbook**: Document on-call procedures for API failures, database backup/restore

## Cost

Everything runs on free tiers:

| Service | Free Limit | Status |
|---------|-----------|--------|
| Railway | $5/month | Easily covers this backend |
| Vercel | Unlimited | Free for personal projects |
| OpenWeatherMap | 1,000 calls/day | ~288 calls/day at 5-min polling |
| Telegram Bot | Unlimited | Free |
| SQLite | N/A | File-based, no cost |

**Total monthly cost: $0** (after Railway free credits)

## Deployment (Railway + Vercel)

### Backend on Railway

1. Push this repo to GitHub
2. Go to https://railway.app → **New Project** → **GitHub repo**
3. Select this repo; set **Root Directory** to `haile-revenue-mvp/backend`
4. Add environment variables in Railway dashboard:
   - `OPENWEATHER_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHANNEL_ID`
5. Railway auto-detects Python and runs `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Copy the Railway URL (e.g., `https://haile-backend.up.railway.app`)

### Frontend on Vercel

1. Go to https://vercel.com → **New Project** → import same GitHub repo
2. Set **Root Directory** to `haile-revenue-mvp/frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL=https://haile-backend.up.railway.app` (no trailing slash)
4. Click **Deploy**

## Questions or Issues?

This is a learning prototype. Refer to code comments in `main.py` for implementation details. Logs print to stdout during polling — useful for debugging trigger behavior.

---

**Version**: 0.1  
**Status**: Prototype  
**Built with**: AI-assisted development (code review, testing, error handling)
