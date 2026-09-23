#!/usr/bin/env bash
set -euo pipefail

: "${API_URL:?Set API_URL to the deployed FastAPI base URL}"
: "${CRON_SECRET:?Set CRON_SECRET to the backend cron secret}"

curl --fail-with-body --silent --show-error \
  --request POST \
  --header "X-Cron-Secret: ${CRON_SECRET}" \
  --header "Content-Type: application/json" \
  "${API_URL%/}/api/v1/cron/weather"
