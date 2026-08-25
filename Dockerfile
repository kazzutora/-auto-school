# syntax=docker/dockerfile:1
# Development image. Production builds from deploy/Dockerfile.

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
# PEP 735 dependency groups need pip 25.1 or newer.
RUN pip install --upgrade "pip>=25.1"

# Only the metadata lands in this layer, so editing source never reinstalls
# the dependency tree.
COPY pyproject.toml ./
RUN pip install . --group dev


FROM python:3.12-slim AS dev

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"

COPY --from=builder /venv /venv

# Uid 1000 matches the first login user on a linux host, so bind mounted
# source stays writable from inside the container.
RUN groupadd --gid 1000 app \
 && useradd --uid 1000 --gid app --home-dir /app --no-create-home app \
 && install -d -o app -g app /app /app/media /app/staticfiles

COPY --chmod=0755 deploy/entrypoint.sh /usr/local/bin/entrypoint.sh

# Browser for the e2e suite, baked in so it survives container recreation.
# --with-deps pulls the system libraries chromium needs: without them the
# browser launches and dies immediately. A shared path keeps it readable by
# the app user.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps chromium && chmod -R a+rX /ms-playwright && rm -rf /var/lib/apt/lists/*

WORKDIR /app
USER app
EXPOSE 8000

# Source arrives as a bind mount from docker-compose.yml.
ENTRYPOINT ["entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


FROM dev AS tailwind

# Standalone CLI, per tech.md section 2: no node in the runtime image. Built on
# the dev stage rather than a bare image because the content scanner has to see
# the crispy-tailwind templates that live in /venv.
USER root
ARG TAILWIND_VERSION=3.4.17
RUN apt-get update  && apt-get install -y --no-install-recommends curl ca-certificates  && curl -fsSL -o /usr/local/bin/tailwindcss     "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/tailwindcss-linux-x64"  && chmod 0755 /usr/local/bin/tailwindcss  && apt-get purge -y --auto-remove curl  && rm -rf /var/lib/apt/lists/*
USER app

WORKDIR /app
ENTRYPOINT []
CMD ["tailwindcss", "--help"]
