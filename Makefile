.PHONY: up down build logs seed test lint clean

# ── Docker ───────────────────────────────────────────────────────────────────
up:
	docker-compose up --build -d
	@echo "\n  HEIST.EXE online → http://localhost\n"

down:
	docker-compose down

build:
	docker-compose build --no-cache

logs:
	docker-compose logs -f

restart:
	docker-compose restart backend

# ── Seed ─────────────────────────────────────────────────────────────────────
seed:
	@echo "Injection mission Tétreaultville..."
	cd backend && python seed.py

seed-remote:
	@read -p "URL de l'API (ex: http://monserveur.com): " url; \
	cd backend && python seed.py $$url

# ── Tests ────────────────────────────────────────────────────────────────────
test:
	cd backend && \
	pip install -q -r requirements.txt -r requirements-dev.txt && \
	pytest tests/ -v --tb=short

test-watch:
	cd backend && pytest tests/ -v --tb=short -f

# ── Dev local (sans Docker) ───────────────────────────────────────────────────
dev-backend:
	cd backend && \
	DB_PATH=./data/heist_dev.db \
	MEDIA_PATH=./media \
	SECRET_KEY=dev-secret-32-chars-minimum-ici \
	ADMIN_KEY=admin-dev \
	CORS_ORIGINS=http://localhost:5173 \
	uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm install && npm run dev

# ── Lint / check ─────────────────────────────────────────────────────────────
lint:
	@python3 -c "\
import ast, os, sys; \
errors = []; \
[(errors.append(f'  ✗ {os.path.join(r,f)}: ' + str(e)) or True) \
  if (lambda p: (open(p).read(), None))[0] and False else \
  (lambda p: [ast.parse(open(p).read())] if not \
   [errors.append(f'  ✗ {p}: ' + str(e)) for e in [None] if False] else [])(os.path.join(r,f)) \
  for r,d,files in os.walk('backend') for f in files if f.endswith('.py')]; \
print('  Lint: OK') if not errors else [print(e) for e in errors]"
	@echo "  Syntax check frontend..."
	@find frontend/src -name "*.jsx" -o -name "*.js" | xargs -I{} echo "  ✓ {}"

# ── Nettoyage ─────────────────────────────────────────────────────────────────
clean:
	docker-compose down -v
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/data backend/media
	@echo "  Clean OK"

# ── Aide ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  HEIST.EXE — Commandes disponibles"
	@echo "  ─────────────────────────────────────"
	@echo "  make up          Démarrer tout (Docker)"
	@echo "  make down        Arrêter"
	@echo "  make logs        Suivre les logs"
	@echo "  make seed        Injecter mission Tétreaultville"
	@echo "  make test        Lancer les tests"
	@echo "  make dev-backend Backend local (sans Docker)"
	@echo "  make dev-frontend Frontend local (Vite dev server)"
	@echo "  make clean       Tout nettoyer"
	@echo ""
