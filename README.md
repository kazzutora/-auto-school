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
- Docker and Docker Compose
- GNU make

## Local setup

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows; use .venv/bin/activate on Linux
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
| `make e2e` | Playwright end to end suite |

Without make, run the tools directly:

```bash
ruff check . && ruff format --check . && mypy apps/
pytest --cov=apps --cov-report=term-missing --ignore=tests/e2e
```

## Test markers

`pytest.ini` defines four markers, run a group with `pytest -m <marker>`:

- `redirects`, legacy URL table from `data/legacy/redirects.csv` answers 301
- `seo`, SEO contract of a public page
- `a11y`, accessibility checks, non-empty `img` alt above all
- `owner_data`, content the owner still owes, blocks the production release

## Layout

Every app under `apps/` is one vertical slice: models, admin, forms, views, urls,
tasks, templates. Shared code lives in `apps/core/` only. The full tree is in
`tech.md` section 3.

## Conventions

Commits follow `tech.md` section 12: English, `type(scope): summary`, imperative,
lower case, no trailing dot. Small commits along the way, not one at the end.
