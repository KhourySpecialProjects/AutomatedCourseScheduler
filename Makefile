.PHONY: help \
	be-install be-dev be-lint be-format be-format-fix be-test be-seed \
	fe-install fe-dev fe-build fe-generate fe-lint fe-lint-fix fe-test fe-test-watch \
	docker-up docker-down docker-build

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# ── Backend ──────────────────────────────────────────────────────────────────

be-install: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

be-dev: ## Start backend dev server (hot reload)
	cd backend && uvicorn app.main:app --reload

be-lint: ## Run ruff linter on backend
	cd backend && ruff check .

be-lint-fix: ## Run ruff linter on backend and fix
	cd backend && ruff check . --fix

be-format: ## Check backend formatting (shows diff of changes needed)
	cd backend && ruff format --check --diff .

be-format-fix: ## Auto-fix backend formatting with ruff
	cd backend && ruff format .

be-seed: ## Seed the database with development data
	cd backend && python3 seed.py

be-test: ## Run backend tests
	cd backend && pytest

# ── Frontend ─────────────────────────────────────────────────────────────────

fe-install: ## Install frontend dependencies
	cd frontend && npm install

fe-dev: ## Start frontend dev server on port 3000
	cd frontend && npm run dev

fe-build: ## Build frontend for production
	cd frontend && npm run build

fe-generate: ## Regenerate TypeScript API client from OpenAPI spec
	cd frontend && npm run generate

fe-lint: ## Run ESLint on frontend
	cd frontend && npm run lint

fe-lint-fix: ## Run ESLint with auto-fix on frontend
	cd frontend && npm run lint:fix

fe-test: ## Run frontend tests (single run)
	cd frontend && npm test

fe-test-watch: ## Run frontend tests in watch mode
	cd frontend && npm run test:watch

# ── Docker ───────────────────────────────────────────────────────────────────

docker-up: ## Start all services with Docker Compose
	docker compose up

docker-build: ## Rebuild and start all services with Docker Compose
	docker compose up --build

docker-down: ## Stop all Docker Compose services
	docker compose down
