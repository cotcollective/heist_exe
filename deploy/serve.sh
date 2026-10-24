#!/usr/bin/env bash
# Sert HEIST.EXE sur un seul port : API + frontend bâti + service worker.
# C'est la cible à donner à un tunnel (cloudflared, ngrok, autre).
#
#   ./deploy/serve.sh              # port 8000 par défaut
#   PORT=8090 ./deploy/serve.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8000}"

# Charge .env s'il existe — sans écraser ce qui est déjà dans l'environnement.
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT/.env"
  set +a
fi

if [ -z "${ADMIN_KEY:-}" ]; then
  echo "ERREUR : ADMIN_KEY manquante. L'administration répondrait 503." >&2
  echo "         Renseigne-la dans $ROOT/.env" >&2
  exit 64
fi

# Python : venv local si présent, sinon celui du système.
if [ -z "${PYTHON:-}" ]; then
  for candidate in "$ROOT/backend/venv/bin/python" "$ROOT/.venv/bin/python" \
                   "/mnt/WIN1TB/heist_venv/bin/python"; do
    [ -x "$candidate" ] && PYTHON="$candidate" && break
  done
fi
if [ -z "${PYTHON:-}" ]; then
  echo "ERREUR : aucun interpréteur Python trouvé. Définis PYTHON=..." >&2
  exit 65
fi

# Le frontend doit être bâti : le backend le sert depuis frontend/dist.
if [ ! -f "$ROOT/frontend/dist/index.html" ]; then
  echo "→ build du frontend (dist absent)"
  ( cd "$ROOT/frontend" && npm install --no-audit --no-fund && npm run build )
fi

export DB_PATH="${DB_PATH:-$ROOT/data/heist.db}"
export MEDIA_PATH="${MEDIA_PATH:-$ROOT/media}"
mkdir -p "$(dirname "$DB_PATH")" "$MEDIA_PATH"

echo "→ HEIST.EXE sur http://127.0.0.1:$PORT"
echo "  base    : $DB_PATH"
echo "  admin   : /admin (clé = ADMIN_KEY)"
echo "  monde   : /world"

cd "$ROOT/backend"
exec "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
