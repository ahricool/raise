#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

echo "Step 1/3: Clean local changes, switch to main, and pull latest code..."
git checkout .
git clean -fd
git switch main || git checkout main
git pull --ff-only

echo "Step 2/3: Stop and clean containers..."
./prod.sh down --remove-orphans

echo "Step 3/3: Start services in detached mode..."
./prod.sh up -d

echo "Deployment completed."
