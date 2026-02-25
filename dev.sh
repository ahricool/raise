#!/usr/bin/env bash
# Start development Docker Compose (code mounted, uvicorn --reload).
# Run from project root: ./dev.sh [up|down|logs|...]

set -e
cd "$(dirname "$0")"

exec docker compose -f docker-compose.dev.yml "$@"
