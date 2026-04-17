#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

echo "Step 1/4: Clean local changes, switch to main, and pull latest code..."
git checkout .
git clean -fd
git switch main || git checkout main
git pull --ff-only

echo "Step 2/4: Stop and clean containers..."
./prod.sh down --remove-orphans

echo "Step 3/4: Pull latest prebuilt image from registry..."
./prod.sh pull server

echo "Step 4/4: Start services in detached mode..."
./prod.sh up -d --force-recreate

echo "Deployment completed."
