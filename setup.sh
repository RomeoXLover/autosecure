#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WEB="$ROOT/web"

cd "$ROOT"

if [[ ! -f config/config.json ]]; then
  if [[ -f config/config.json.example ]]; then
    cp config/config.json.example config/config.json
    echo "[*] Created config/config.json from config.json.example"
    echo "    Edit it now: bot token, owners, domain, web password, mail webhooks."
    echo "    Then re-run ./setup.sh"
    exit 1
  fi
  echo "Missing config/config.json and config/config.json.example"
  exit 1
fi

if [[ ! -f config/bot.json && -f config/bot.json.example ]]; then
  cp config/bot.json.example config/bot.json
  echo "[*] Created config/bot.json from bot.json.example"
fi

PY="${PYTHON:-}"
if [[ -z "$PY" ]]; then
  for candidate in python3.14 python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  done
fi

if [[ ! -d .venv ]]; then
  echo "[*] Creating virtualenv with $PY..."
  "$PY" -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi

if [[ ! -d web/node_modules ]]; then
  echo "[*] Installing web dependencies..."
  (cd web && npm install)
fi

echo "[*] Building frontend..."
(cd web && npm run build)

echo "[*] Starting services with PM2..."
pm2 start ecosystem.config.cjs

echo
echo "[+] AutoSecure is running."
echo "    API:      http://127.0.0.1:8000"
echo "    Web UI:   http://127.0.0.1:3000"
echo "    Bot:      pm2 logs autosecure-bot"
echo "    Status:   pm2 status"
echo
echo "Before the bot works, edit config/config.json with your Discord bot token and owner ID."
echo "For public access, configure cloudflared.yml and run: cloudflared tunnel --config cloudflared.yml run"
