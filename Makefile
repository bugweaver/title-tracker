COMPOSE_BASE := -f docker-compose.yml
COMPOSE_DEV := $(COMPOSE_BASE) -f docker-compose.override.yml
COMPOSE_PROD := $(COMPOSE_BASE) -f docker-compose.prod.yml

.PHONY: up down dev logs migrate migration build shell-backend shell-db

# Run the application in detached mode (Production)
up:
	docker compose $(COMPOSE_PROD) up -d --build

# Run the application in foreground (Development)
dev:
	docker compose $(COMPOSE_DEV) up --build

# Stop the application
down:
	docker compose down --remove-orphans

# View logs
logs:
	docker compose logs -f

# Build the application
build:
	docker compose $(COMPOSE_PROD) build

# Apply database migrations
migrate:
	docker compose $(COMPOSE_DEV) exec backend alembic upgrade head

# Create a new migration (usage: make migration MSG="message")
migration:
	docker compose $(COMPOSE_DEV) exec backend alembic revision --autogenerate -m "$(MSG)"

# Access backend shell
shell-backend:
	docker compose $(COMPOSE_DEV) exec backend /bin/bash

# Access database shell
shell-db:
	docker compose $(COMPOSE_DEV) exec db psql -U bugweaver -d title_tracker

# Create two default users (bugweaver, alice)
create-users:
	docker compose $(COMPOSE_DEV) exec backend python src/scripts/create_users.py

# --- CI/CD & Local Development Helpers ---

# Install dependencies locally
install:
	cd backend && uv sync
	cd frontend && bun install

# Run linters
lint:
	cd backend && uv run ruff check .
	cd frontend && bun run lint

# Run formatters
format:
	cd backend && uv run ruff format .
	cd frontend && bun run format

# Run tests (currently only frontend type-check as backend has no tests)
test:
	cd frontend && bun run type-check
