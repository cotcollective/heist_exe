#!/usr/bin/env bash
# setup.sh — First run HEIST.EXE
# Usage: bash setup.sh
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

banner() {
  echo ""
  echo -e "${CYAN}  ██╗  ██╗███████╗██╗███████╗████████╗${RESET}"
  echo -e "${CYAN}  ██║  ██║██╔════╝██║██╔════╝╚══██╔══╝${RESET}"
  echo -e "${CYAN}  ███████║█████╗  ██║███████╗   ██║   ${RESET}"
  echo -e "${CYAN}  ██╔══██║██╔══╝  ██║╚════██║   ██║   ${RESET}"
  echo -e "${CYAN}  ██║  ██║███████╗██║███████║   ██║   ${RESET}"
  echo -e "${CYAN}  ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝   ╚═╝   ${RESET}"
  echo -e "${CYAN}         E X E  — Urban Mission Platform${RESET}"
  echo ""
}

step() { echo -e "${CYAN}  ▶ $1${RESET}"; }
ok()   { echo -e "${GREEN}  ✓ $1${RESET}"; }
warn() { echo -e "${YELLOW}  ⚠ $1${RESET}"; }
fail() { echo -e "${RED}  ✗ $1${RESET}"; exit 1; }

banner

# ── Prérequis ────────────────────────────────────────────────────────────────
step "Vérification des prérequis..."
command -v docker      >/dev/null 2>&1 || fail "Docker non trouvé. Installe Docker Desktop."
command -v docker-compose >/dev/null 2>&1 || fail "docker-compose non trouvé."
ok "Docker disponible — $(docker --version | cut -d' ' -f3 | tr -d ',')"

# ── .env ────────────────────────────────────────────────────────────────────
step "Configuration de l'environnement..."
if [ ! -f .env ]; then
  cp .env.example .env

  # Générer une SECRET_KEY aléatoire solide
  if command -v openssl >/dev/null 2>&1; then
    SECRET=$(openssl rand -hex 32)
  else
    SECRET=$(cat /dev/urandom | head -c 32 | xxd -p | tr -d '\n')
  fi

  sed -i.bak "s/change-this-in-prod-minimum-32-chars/$SECRET/" .env
  rm -f .env.bak

  # Demander l'ADMIN_KEY
  echo ""
  read -p "  Clé admin (laisser vide = 'admin-dev-2077'): " ADMIN_INPUT
  ADMIN_KEY="${ADMIN_INPUT:-admin-dev-2077}"
  sed -i.bak "s/admin-secret-key-change-me/$ADMIN_KEY/" .env
  rm -f .env.bak

  ok ".env créé avec SECRET_KEY générée"
  echo "  ADMIN_KEY: ${CYAN}${ADMIN_KEY}${RESET} — garde ça, tu en as besoin pour créer des missions"
else
  ok ".env déjà présent"
  ADMIN_KEY=$(grep ADMIN_KEY .env | cut -d= -f2)
fi

echo ""

# ── Docker build + up ────────────────────────────────────────────────────────
step "Build et démarrage des containers..."
docker-compose up --build -d

echo ""
step "Attente de l'API (max 30s)..."
MAX=30
COUNT=0
until curl -sf http://localhost/api/health >/dev/null 2>&1; do
  sleep 1
  COUNT=$((COUNT+1))
  printf "  . "
  if [ $COUNT -ge $MAX ]; then
    echo ""
    fail "API ne répond pas après ${MAX}s. Lance 'docker-compose logs backend' pour voir l'erreur."
  fi
done
echo ""
ok "API online"

# ── Seed mission ─────────────────────────────────────────────────────────────
echo ""
read -p "  Injecter la mission de démo Tétreaultville? (O/n): " SEED_ANS
SEED_ANS="${SEED_ANS:-O}"
if [[ "$SEED_ANS" =~ ^[Oo]$ ]]; then
  step "Injection mission Tétreaultville..."
  ADMIN_KEY="$ADMIN_KEY" python3 backend/seed.py
fi

# ── Résumé ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  ══════════════════════════════════════════${RESET}"
echo -e "${GREEN}         HEIST.EXE OPÉRATIONNEL${RESET}"
echo -e "${GREEN}  ══════════════════════════════════════════${RESET}"
echo ""
echo "  App       →  http://localhost"
echo "  Swagger   →  http://localhost/api/docs"
echo "  PIN démo  →  2077"
echo ""
echo "  Commandes utiles:"
echo "    make logs     — suivre les logs"
echo "    make seed     — réinjecter la mission"
echo "    make down     — arrêter"
echo ""
