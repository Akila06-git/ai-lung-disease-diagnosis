#!/usr/bin/env bash
set -e

echo "Setting up Lung Disease Detector (backend + frontend)..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT/backend"

python -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "Copying .env.example to .env (please edit values)..."
  cp .env.example .env || true
fi

python manage.py migrate

cd "$PROJECT_ROOT/frontend"
npm install

echo "Setup complete. You can now run the backend and frontend."

