# Haile Revenue OS

Autonomous AI Revenue System for Haile Resort, Adama, Ethiopia.
Polls real-time weather → broadcasts to Telegram when it's the perfect day.

## Quick start

### 1. Backend (Railway)

1. Push this repo to GitHub (already done if you're reading this on GitHub).
2. Go to https://railway.app → **New Project** → **Deploy from GitHub repo** → pick this repo.
3. Set the **Root Directory** to `backend`.
4. In **Variables**, paste your real values (see `backend/.env.example`):
   - `OPENWEATHER_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHANNEL_ID` (e.g. `@haile_resort_deals`)
   - `GEMINI_API_KEY` (optional for now)
5. Railway auto-detects Python, runs `uvicorn main:app --host 0.0.0.0 --port $PORT`.
6. Once deployed, copy your Railway URL: `https://xxx.up.railway.app`

### 2. Frontend (Vercel)

1. Go to https://vercel.com → **New Project** → import the same GitHub repo.
2. Set **Root Directory** to `frontend`.
3. Add env var: `NEXT_PUBLIC_API_URL` = your Railway backend URL (no trailing slash).
4. Click Deploy. You get `https://xxx.vercel.app`.

### 3. Test it

1. Open the Vercel URL in your browser.
2. Hit **"Fire test campaign"** — sends a real message to your Telegram channel.
3. Wait for the next 28°C+ day in Adama, or just watch the dashboard.

## Local development

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # fill in your real values
python main.py
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local  # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## Architecture

- **Backend** (FastAPI, single `main.py`): polls OpenWeatherMap every 5 min, fires
  Telegram broadcasts when temp ≥ 28°C, tracks campaigns in SQLite.
- **Frontend** (Next.js 14 + Tailwind): live dashboard, manual trigger button,
  campaign history.
- **Trigger rule**: `temp_c >= 28` (configurable via `TRIGGER_TEMP_C` env var).
- **Message rotation**: 3 variants cycled by hour so the same copy isn't sent twice.

## Files

```
haile-revenue-os/
├── backend/
│   ├── main.py              # entire backend in one file
│   ├── requirements.txt
│   ├── .env.example
│   ├── Procfile             # for Railway
│   └── railway.json
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx         # the dashboard
│   │   └── globals.css
│   ├── lib/api.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── next.config.js
│   └── .env.local.example
└── README.md
```

## API endpoints

- `GET  /api/v1/health` — health check
- `GET  /api/v1/stats` — dashboard summary
- `GET  /api/v1/weather/current` — live Adama weather
- `GET  /api/v1/campaigns` — campaign history
- `POST /api/v1/campaigns/test` — manual fire
- `GET  /api/v1/leads` — lead list

## Cost

Everything runs on free tiers:
- Railway: $5 free credit / month (covers this easily)
- Vercel: free for personal projects
- OpenWeatherMap: free (1,000 calls / day)
- Telegram: free
- Gemini: free tier (1M tokens / day)

Total: **0 ETB / month** for the MVP.
