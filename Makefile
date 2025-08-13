SHELL := /bin/bash

.PHONY: dev dev-native install backend frontend test clean

install:
	python3 -m venv .venv || true
	. .venv/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt
	cd tegus-frontend && npm install

dev:
	bash scripts/dev.sh

dev-native:
	MODE=native bash scripts/dev.sh

backend:
	. .venv/bin/activate && PYTHONPATH=$(PWD) python3 -m uvicorn run:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd tegus-frontend && npm run start -- --non-interactive

test:
	. .venv/bin/activate && PYTHONPATH=$(PWD) python3 tests/run_all_tests.py

clean:
	rm -rf .venv .venv_installed
	cd tegus-frontend && rm -rf node_modules

# Database migration commands
db-init:
	@echo "Initializing Alembic..."
	@alembic init migrations

db-migrate:
	@echo "Creating new migration..."
	@alembic revision --autogenerate -m "$(message)"

db-upgrade:
	@echo "Applying migrations..."
	@alembic upgrade head

db-downgrade:
	@echo "Downgrading migrations..."
	@alembic downgrade -1

db-current:
	@echo "Current migration version:"
	@alembic current

db-history:
	@echo "Migration history:"
	@alembic history

db-show:
	@echo "Showing migration details:"
	@alembic show $(revision) 