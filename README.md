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
| `make e2e` | Playwright end to end suite, runs in the web container |

Without make, run the tools directly:

```bash
ruff check . && ruff format --check . && mypy apps/
pytest --cov=apps --cov-report=term-missing --ignore=tests/e2e
```

The end to end suite drives a real browser. Chromium ships inside the
development image, so `make e2e` needs no extra setup.

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

## CI and deploy

Two pipelines, tech.md section 17.

| Workflow | Trigger | What it does |
|---|---|---|
| `.github/workflows/ci.yml` | pull request | ruff, mypy, pending migration check, pytest with an 80 percent floor, Playwright against the built image, both docker builds |
| `.github/workflows/deploy.yml` | push to `main` | build and push to ghcr, then over ssh: pull, migrate, collectstatic, start, smoke `GET /healthz` |

Before the first deploy, set these repository secrets: `VPS_HOST`, `VPS_USER`,
`VPS_SSH_KEY`, `VPS_PATH`. The registry uses the built in `GITHUB_TOKEN`.

Two one time steps once the repository is on github:

```bash
# 1. Replace @lead in .github/CODEOWNERS with the real handle or team.
#    Github ignores an entry naming an account it cannot resolve.
# 2. Apply branch protection: pull requests only, green CI, linear history.
.github/branch-protection.sh owner/repo
```

## Conventions

Commits follow `tech.md` section 12: English, `type(scope): summary`, imperative,
lower case, no trailing dot. Small commits along the way, not one at the end.
