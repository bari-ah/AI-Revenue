# External weather cron

The backend no longer starts a long-running polling task in FastAPI. This is deliberate: Vercel, Railway autoscaling, and other serverless/container platforms may stop idle processes or run multiple replicas.

Schedule `weather-cron.sh` every five minutes using Supabase Edge Functions, GitHub Actions, Railway Cron, Render Cron Jobs, or any external scheduler. Configure:

- `API_URL`: the deployed FastAPI base URL
- `CRON_SECRET`: the same random secret configured in the backend

Example GitHub Actions schedule:

```yaml
name: Revenue weather trigger
on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:
jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash haile-revenue-mvp/cron/weather-cron.sh
        env:
          API_URL: ${{ secrets.REVENUE_API_URL }}
          CRON_SECRET: ${{ secrets.REVENUE_CRON_SECRET }}
```

For Supabase, create a scheduled Edge Function that sends the same `POST` request with the `X-Cron-Secret` header. Do not expose `SUPABASE_SERVICE_ROLE_KEY` or `CRON_SECRET` to the browser.
