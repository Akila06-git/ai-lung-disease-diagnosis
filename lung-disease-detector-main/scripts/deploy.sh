#!/usr/bin/env bash
set -e

echo "Building and starting Docker services..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/backend"

docker-compose up --build -d

echo "Docker deployment started. Backend on :8000, frontend via Nginx on :80."

