#!/usr/bin/env bash
# Start production Docker Compose (built images, no code mount).
# Run from project root: ./prod.sh [up|down|logs|...]

set -e
cd "$(dirname "$0")"

exec docker compose -f docker-compose.yml "$@"
