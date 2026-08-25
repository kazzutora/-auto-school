# syntax=docker/dockerfile:1
# Production image. Development builds from the Dockerfile in the repo root.
# Build from the repo root: docker build -f deploy/Dockerfile .

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
# PEP 735 dependency groups need pip 25.1 or newer.
RUN pip install --upgrade "pip>=25.1"

# Runtime dependencies only: the dev group never reaches production.
COPY pyproject.toml ./
RUN pip install .



FROM builder AS css

# Same standalone CLI as development, and the same /venv so the content scanner
# sees the crispy-tailwind templates.
ARG TAILWIND_VERSION=3.4.17
RUN apt-get update  && apt-get install -y --no-install-recommends curl ca-certificates  && curl -fsSL -o /usr/local/bin/tailwindcss     "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/tailwindcss-linux-x64"  && chmod 0755 /usr/local/bin/tailwindcss  && apt-get purge -y --auto-remove curl  && rm -rf /var/lib/apt/lists/*

COPY tailwind.config.js ./
COPY static ./static
COPY templates ./templates
COPY apps ./apps
RUN tailwindcss -i static/src/css/app.css -o static/css/app.css --minify


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"

COPY --from=builder /venv /venv

# pg_dump for core.tasks.db_backup, tech.md section 19. Debian ships a client
# older than the server and pg_dump refuses to dump a newer one, so take 16
# from the postgres apt repository. The suite is read from the base image
# rather than hardcoded: pinning the wrong codename silently mixes releases.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/pgdg.gpg && echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] http://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo $VERSION_CODENAME)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && apt-get update && apt-get install -y --no-install-recommends postgresql-client-16 && apt-get purge -y curl gnupg && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 app \
 && useradd --uid 1000 --gid app --home-dir /app --no-create-home app \
 && install -d -o app -g app /app /app/media /app/staticfiles

COPY --chmod=0755 deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chown=app:app . /app
COPY --from=css --chown=app:app /app/static/css/app.css /app/static/css/app.css

WORKDIR /app
USER app
EXPOSE 8000

# collectstatic and migrate run as separate deploy steps, see tech.md section 17.
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--worker-class", "gthread", \
     "--workers", "3", \
     "--threads", "4", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
