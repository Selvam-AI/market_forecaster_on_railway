#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
.venv/bin/uvicorn geopolitical_market_forecaster.main:app --host 0.0.0.0 --port 8000
