# OSK Ostrycharz

Website of the driving school OSK Ostrycharz, ul. Sieradzka 122C, Wieluń. Replaces
`oskostrycharz.pl`, a one-page site with anchor navigation.

The school teaches one category — B — three ways: standard, accelerated over two
weeks, and on an automatic gearbox. It publishes its prices, which is rare, and
it publishes how many of its candidates pass at the first attempt, which is the
strongest thing a driving school can say about itself. Both were buried in the
middle of the old single page with no url of their own. `tech.md` section 1.

Django 5.1, PostgreSQL 16, Celery and Redis, Django Templates with django-cotton,
HTMX, Tailwind. The full stack is frozen in `tech.md` section 2.

## Read first

| File | Content |
|---|---|
| `tech.md` | Core, single source of truth. Database schema, Celery contracts, URL map, UI components, `Seo` contract, test doctrine, infrastructure. Append only, every contract change bumps the version. |
| `DEV.md` | Part I: skeleton build order and checklists (LEAD mode). Part II: staged task list (DEV mode). |
| `OSTRYCHARZ.md` | This client's data as transcribed from their own site, what was wrong with it, and the prompts that built this. |
| `CLAUDE.md` | Session pointer. |

Pin the core version from the `tech.md` header at the start of every session.
Current core version: **v24**.

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
  (and the half of it that is anchors, which the browser has to resolve)
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

## Two schools, one box

This repository is a fork of the engine that runs a second driving school on the
same server. Nothing is shared at runtime and nothing may become shared:

- `COMPOSE_PROJECT_NAME` namespaces every volume, network and container. Leave
  it at `osk-ostrycharz`; with the default `osk` the two stacks mount the same
  `pgdata` volume and one client's database answers for the other.
- `POSTGRES_PORT` and `WEB_PORT` differ per stack, or whichever comes up second
  cannot bind.
- there is one pair of ports 80 and 443 on the box. One stack keeps its Caddy
  and terminates TLS for both; the other runs without one and is reached by
  container name over a shared network:

  ```bash
  docker network create osk-edge          # once, on the box

  docker compose --env-file .env     -f deploy/docker-compose.prod.yml     -f deploy/docker-compose.edge.yml     up -d --scale caddy=0
  ```

  Then paste `deploy/Caddyfile.second-site` into the live `Caddyfile` of the
  stack that does own the edge and reload it. Caddy picks the block by the Host
  header, so neither school ever sees the other's requests and each gets its own
  certificate.

The rule for anything that differs between the two schools: it lives in the
database or in `.env`, never in a template. A `{% if school == "ostrycharz" %}`
in a template is a branch that becomes unmanageable at the third client — at the
fourth, this stops being a fork and becomes multi-tenant.

## Production

The production stack keeps its secrets in `.env` at the repo root, the same file
the development stack uses, and needs `--env-file .env` to find it: compose
resolves the project directory from the location of the compose file, so without
the flag it would look in `deploy/`. That same rule is what puts the backups in
`deploy/backups`. `deploy.yml` passes the flag already; pass it in a manual call
too:

```bash
docker compose --env-file .env -f deploy/docker-compose.prod.yml up -d
```

The database password is written once, as `POSTGRES_PASSWORD`; both compose
files build `DATABASE_URL` from it and ignore any `DATABASE_URL` left in `.env`.

On a machine with the checkout but no ghcr login, leave `WEB_IMAGE` empty and
the stack builds the image locally instead of pulling it:

```bash
docker compose --env-file .env -f deploy/docker-compose.prod.yml up -d --build
```

`/healthz` answers 200 only when postgres and redis both respond, and 503 with
the failing dependency named otherwise. The deploy smoke step and the container
healthcheck both use it.

`core.tasks.db_backup` runs at 02:00 and writes `deploy/backups/osk-YYYYMMDD.sql.gz`,
keeping fourteen days. The dated filename is the idempotency key, so a second
run the same day does nothing.

A backup nobody has restored is not a backup. tech.md section 19 asks for one
manual restore before the domain moves:

```bash
# on the vps, from the application directory
compose="docker compose -f deploy/docker-compose.prod.yml"
$compose stop web worker beat
$compose exec -T db dropdb -U osk osk
$compose exec -T db createdb -U osk osk
gzip -dc deploy/backups/osk-YYYYMMDD.sql.gz | $compose exec -T db psql -U osk -d osk
$compose start web worker beat
curl -sf http://localhost/healthz
```

Confirm Sentry is receiving events:

```bash
docker compose -f deploy/docker-compose.prod.yml run --rm web python manage.py sentry_check
```

## Conventions

Commits follow `tech.md` section 12: English, `type(scope): summary`, imperative,
lower case, no trailing dot. Small commits along the way, not one at the end.
