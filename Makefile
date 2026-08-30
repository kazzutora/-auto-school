COMPOSE := docker compose

.DEFAULT_GOAL := help
.PHONY: help up down sh migrate seed test lint fmt css e2e

help:
	grep -E '^[a-z0-9][a-z0-9-]*:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

up: ## start the dev stack: web, db, redis, worker, beat, tailwind
	$(COMPOSE) up -d

down: ## stop the dev stack
	$(COMPOSE) down

sh: ## shell inside the web container
	$(COMPOSE) exec web bash

migrate: ## apply migrations
	$(COMPOSE) exec web python manage.py migrate

seed: ## load the shared fixtures, idempotent
	$(COMPOSE) exec web python -m scripts.seed

test: ## pytest with coverage, e2e excluded
	pytest --cov=apps --cov-report=term-missing --ignore=tests/e2e

lint: ## ruff check, ruff format check, mypy
	ruff check .
	ruff format --check .
	mypy apps/

fmt: ## format and autofix
	ruff format .
	ruff check --fix .

messages: ## rebuild locale/*.po from the source and compile them
	docker compose exec web python manage.py makemessages -l pl -l ru -l uk --no-obsolete --no-wrap
	docker compose exec web python manage.py compilemessages

css: ## build tailwind css
	$(COMPOSE) run --rm tailwind tailwindcss -i static/src/css/app.css -o static/css/app.css --minify

e2e: ## playwright end to end suite, runs in the web container
	$(COMPOSE) exec web pytest tests/e2e
