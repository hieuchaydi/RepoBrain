# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPOBRAIN_REPO=/workspace \
    REPOBRAIN_WEB_HOST=0.0.0.0 \
    REPOBRAIN_WEB_PORT=8765

WORKDIR /app

ARG REPOBRAIN_PIP_EXTRAS=""

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY webapp/dist ./webapp/dist
COPY docker/entrypoint.sh /usr/local/bin/repobrain-docker

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel \
    && if [ -n "${REPOBRAIN_PIP_EXTRAS}" ]; then python -m pip install ".[${REPOBRAIN_PIP_EXTRAS}]"; else python -m pip install .; fi \
    && chmod +x /usr/local/bin/repobrain-docker

VOLUME ["/workspace"]
EXPOSE 8765

ENTRYPOINT ["repobrain-docker"]
CMD ["web"]

FROM node:22-slim AS web-build

WORKDIR /app/webapp
COPY webapp/package.json webapp/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline --no-audit
COPY webapp/ ./
RUN npm run build

FROM runtime-base AS runtime-webbuild
COPY --from=web-build /app/webapp/dist ./webapp/dist

FROM runtime-base AS runtime
