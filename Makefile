COMPOSE := docker compose

.DEFAULT_GOAL := help
.PHONY: help up down sh migrate seed test lint fmt css budget photos optimize-photos watermark-demo e2e

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

css: ## build tailwind css: the stylesheet and the motion layer
	$(COMPOSE) run --rm tailwind tailwindcss -i static/src/css/app.css -o static/css/app.css --minify
	# The motion layer is plain css, but the same cli minifies it and strips the
	# comments out of the served copy. It warns that the u- safelist matches
	# nothing on this input, which is true and harmless: the file generates no
	# utilities. Nothing to chase.
	$(COMPOSE) run --rm tailwind tailwindcss -i static/src/css/motion.css -o static/css/motion.css --minify

photos: ## download the photographs listed in scripts/photos.txt, REDESIGN.md D.5
	./scripts/fetch_photos.sh

optimize-photos: ## crop, convert and weigh them, unstamped, REDESIGN.md D.6
	python scripts/optimize_photos.py

watermark-demo: ## the same for the owner's demo; stock is stamped ZDJĘCIE POGLĄDOWE, D.2
	python scripts/optimize_photos.py --watermark

budget: ## the three asset gates: size, contrast, font coverage
	$(COMPOSE) exec -T web python scripts/check_budget.py
	$(COMPOSE) exec -T web python scripts/check_contrast.py
	$(COMPOSE) exec -T web python scripts/check_fonts.py

e2e: ## playwright end to end suite, runs in the web container
	$(COMPOSE) exec web pytest tests/e2e
