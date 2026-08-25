# OSK Nawrocki

Website of the driving school Ośrodek Kształcenia i Doskonalenia Zawodowego
Adam Nawrocki, Mariola Nawrocka S.C., Wieluń. Replaces `naukajazdywielun.pl`.

Django 5.1, PostgreSQL 16, Celery and Redis, Django Templates with django-cotton,
HTMX, Tailwind. The full stack is frozen in `tech.md` section 2.

## Read first

| File | Content |
|---|---|
| `tech.md` | Core, single source of truth. Database schema, Celery contracts, URL map, UI components, `Seo` contract, test doctrine, infrastructure. Append only, every contract change bumps the version. |
| `DEV.md` | Part I: skeleton build order and checklists (LEAD mode). Part II: staged task list (DEV mode). |
| `CLAUDE.md` | Session pointer. |

Pin the core version from the `tech.md` header at the start of every session.
Current core version: **v1**.

## Requirements

- Python 3.12
- pip 25.1 or newer, the dev toolchain ships as a PEP 735 dependency group
- Docker and Docker Compose
- GNU make

## Local setup

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows; use .venv/bin/activate on Linux
python -m pip install -U pip
pip install -e . --group dev
```

Runtime dependencies live in `[project.dependencies]`, the dev toolchain in the
`dev` dependency group, both in `pyproject.toml`.

## Commands

| Command | What it does |
|---|---|
| `make up` | start the dev stack: web, db, redis, worker, beat, tailwind |
| `make down` | stop the dev stack |
| `make sh` | shell inside the web container |
| `make migrate` | apply migrations |
| `make seed` | load the shared fixtures, idempotent |
| `make test` | pytest with coverage, e2e excluded |
| `make lint` | `ruff check`, `ruff format --check`, `mypy apps/` |
| `make fmt` | format and autofix |
| `make css` | build Tailwind CSS |
| `make e2e` | Playwright end to end suite, needs `playwright install chromium` once |

Without make, run the tools directly:

```bash
ruff check . && ruff format --check . && mypy apps/
pytest --cov=apps --cov-report=term-missing --ignore=tests/e2e
```

The end to end suite drives a real browser. Install it once inside the web
container:

```bash
docker compose exec -u root web playwright install --with-deps chromium
docker compose exec web playwright install chromium
```

## Test markers

`pytest.ini` defines four markers, run a group with `pytest -m <marker>`:

- `redirects`, legacy URL table from `data/legacy/redirects.csv` answers 301
- `seo`, SEO contract of a public page
- `a11y`, accessibility checks, non-empty `img` alt above all
- `owner_data`, content the owner still owes, blocks the production release

## Settings

Four modules under `config/settings/`, every value read from the environment
through django-environ. `.env.example` lists the variables, tech.md section 10.

| Module | Used by | Notes |
|---|---|---|
| `base.py` | all | shared configuration, development defaults |
| `dev.py` | `docker compose up` | DEBUG on, uncached template loaders, console email, fake clients |
| `prod.py` | gunicorn in the production stack | security baseline from tech.md section 19, WhiteNoise manifest storage, Sentry |
| `test.py` | pytest | fake clients, eager Celery, locmem email |

`prod.py` reads `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` without a
fallback, so production refuses to start on a missing secret.

## Layout

Every app under `apps/` is one vertical slice: models, admin, forms, views, urls,
tasks, templates. Shared code lives in `apps/core/` only. The full tree is in
`tech.md` section 3.

## Conventions

Commits follow `tech.md` section 12: English, `type(scope): summary`, imperative,
lower case, no trailing dot. Small commits along the way, not one at the end.
