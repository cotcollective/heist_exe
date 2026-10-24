#!/usr/bin/env bash
# Déploie le frontend sur Surge, en pointant l'API vers le tunnel.
#
#   ./deploy/surge.sh heist-exe.surge.sh
#   API=https://chasse.legarsdeschandails.store ./deploy/surge.sh mon-domaine.surge.sh
#
# Surge ne sert que du statique : l'API reste sur la machine, derrière le
# tunnel. Conséquence à garder en tête — deux cibles à garder cohérentes, et
# si l'API tombe, le site se charge mais rien ne répond.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMAIN="${1:-}"
API="${API:-https://chasse.legarsdeschandails.store}"

if [ -z "$DOMAIN" ]; then
  echo "usage: $0 <domaine.surge.sh>" >&2
  exit 64
fi

if [ ! -f "$ROOT/.env" ]; then
  echo "→ .env absent : Surge n'en a pas besoin, on continue." >&2
fi

echo "→ build avec API=$API"
cd "$ROOT/frontend"
VITE_API_BASE="$API" npm run build

# Surge sert 200.html pour toute route inconnue : c'est ainsi qu'un SPA
# garde ses URLs propres (/world, /hunt, /start…).
cp dist/index.html dist/200.html

# Le CNAME dit à Surge quel domaine posséder pour ce dossier.
printf '%s\n' "$DOMAIN" > dist/CNAME

echo "→ envoi vers $DOMAIN"
npx --yes surge ./dist --domain "$DOMAIN"

echo
echo "Fait : https://$DOMAIN"
echo
echo "Côté serveur, autoriser cette origine :"
echo "  CORS_ORIGINS=\"https://$DOMAIN,http://localhost:5173\""
echo "puis  sudo systemctl restart heist"
