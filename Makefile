.PHONY: help up down restart logs shell migrate seed test lint clean test-openai

help:
	@echo "Agentic Ticket System - Dev Commands"
	@echo "up            Start all services"
	@echo "down          Stop all services"
	@echo "logs          Tail all logs"
	@echo "logs-backend  Tail backend logs"
	@echo "shell         Open backend shell"
	@echo "shell-db      Open psql shell"
	@echo "migrate       Run Alembic migrations"
	@echo "migrate-new   Create new migration  (msg=<name>)"
	@echo "seed          Seed initial data"
	@echo "test          Run tests"
	@echo "lint          Lint with ruff"
	@echo "clean         Remove all volumes"
	@echo "init-qdrant   Init Qdrant collections"
	@echo "init-minio    Init MinIO buckets"
	@echo "test-openai   Test OpenAI connection"
	@echo "cost-report   Show LLM token cost logs"

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f worker

shell:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U ticket_user -d ticket_db

migrate:
	docker compose exec backend alembic upgrade head

migrate-new:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

migrate-down:
	docker compose exec backend alembic downgrade -1

seed:
	docker compose exec backend python -m app.scripts.seed_data

test:
	docker compose exec backend pytest tests/ -v --tb=short

lint:
	docker compose exec backend ruff check app/ --fix

format:
	docker compose exec backend ruff format app/

clean:
	docker compose down -v --remove-orphans

init-qdrant:
	docker compose exec backend python -m app.scripts.init_qdrant

init-minio:
	docker compose exec backend python -m app.scripts.init_minio

reindex:
	docker compose exec backend python -m app.scripts.reindex_embeddings

test-openai:
	docker compose exec backend python -c "import asyncio; from app.services.llm_service import classify_ticket; print(asyncio.run(classify_ticket('VPN not connecting', 'Cannot connect to VPN since this morning')))"

cost-report:
	docker compose logs worker | grep "[LLM]" | tail -50

ps:
	docker compose ps
