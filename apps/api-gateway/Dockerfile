# ─────────────────────────────────────────────────────────────────────────────
# BridgeCAD API Gateway — multi-arch Dockerfile
# Targets: linux/amd64  linux/arm64
# Build:   docker buildx build --platform linux/amd64,linux/arm64 \
#              -t bridgecad/api:0.1.0-rc1 --push .
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependencies ─────────────────────────────────────────────────
FROM python:3.11-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System libs needed by ezdxf / numpy / cairosvg
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential libcairo2 libcairo2-dev git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install all packages first (better layer caching)
COPY packages/ packages/
RUN pip install --upgrade pip && \
    for pkg in packages/*/pyproject.toml; do \
        dir="${pkg%/pyproject.toml}"; \
        pip install "$dir" --no-deps; \
    done && \
    # re-install with deps to resolve inter-package deps
    for pkg in packages/*/pyproject.toml; do \
        dir="${pkg%/pyproject.toml}"; \
        pip install "$dir"; \
    done

# Install API gateway dependencies
COPY apps/api-gateway/pyproject.toml /build/api-pyproject.toml
RUN pip install fastapi uvicorn[standard] python-multipart pydantic>=2.6 \
        sqlalchemy>=2.0 scipy>=1.12 numpy>=1.26 ezdxf>=1.4 openpyxl>=3.1 \
        pyyaml structlog

# ── Stage 2: runtime ──────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/packages/bridgecad-core:/app/packages/bridgecad-io:/app/packages/bridgecad-draw:/app/packages/bridgecad-bill:/app/packages/bridgecad-qa:/app/packages/bridgecad-export:/app/packages/bridgecad-plugins:/app/packages/bridgecad-ai:/app/packages/bridgecad-infra

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends libcairo2 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed site-packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

WORKDIR /app

# Copy source
COPY packages/ packages/
COPY apps/api-gateway/ app/

WORKDIR /app/app

EXPOSE 8000

# Non-root user for security
RUN addgroup --system bridgecad && adduser --system --ingroup bridgecad bridgecad
RUN chown -R bridgecad:bridgecad /app
USER bridgecad

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "bridgecad_api.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
