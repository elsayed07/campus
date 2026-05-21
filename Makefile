.DEFAULT_GOAL := help
DC := docker compose
EXEC := $(DC) exec django uv run

.PHONY: help build up down logs shell migrate makemigrations superuser seed test lint format type check prod-build prod-up prod-down

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

build: ## Build dev images
	$(DC) build

up: ## Start dev stack
	$(DC) up -d

down: ## Stop dev stack
	$(DC) down

logs: ## Tail django logs
	$(DC) logs -f django

shell: ## Django shell
	$(EXEC) python manage.py shell

migrate: ## Apply migrations
	$(EXEC) python manage.py migrate

makemigrations: ## Create migrations
	$(EXEC) python manage.py makemigrations

superuser: ## Create a superuser
	$(EXEC) python manage.py createsuperuser

seed: ## Seed realistic demo data
	$(EXEC) python manage.py seed

test: ## Run the test suite
	$(EXEC) pytest -q

lint: ## Ruff lint
	$(EXEC) ruff check .

format: ## Black + Ruff format
	$(EXEC) black . && $(EXEC) ruff check --fix .

type: ## Pyright type check
	$(EXEC) pyright

check: lint type test ## Lint + type + test

prod-build: ## Build production images
	$(DC) -f docker-compose.prod.yml build

prod-up: ## Start production stack
	$(DC) -f docker-compose.prod.yml up -d

prod-down: ## Stop production stack
	$(DC) -f docker-compose.prod.yml down
