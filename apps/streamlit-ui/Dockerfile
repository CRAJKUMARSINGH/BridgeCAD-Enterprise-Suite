# ─────────────────────────────────────────────────────────────────────────────
# BridgeCAD Streamlit UI — multi-arch Dockerfile
# Targets: linux/amd64  linux/arm64
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential libcairo2 libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY packages/ packages/
RUN pip install --upgrade pip && \
    for pkg in packages/*/pyproject.toml; do \
        dir="${pkg%/pyproject.toml}"; \
        pip install "$dir"; \
    done && \
    pip install streamlit>=1.37 pandas openpyxl pyyaml ezdxf scipy numpy

# ── Runtime ──────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/packages/bridgecad-core:/app/packages/bridgecad-io:/app/packages/bridgecad-draw:/app/packages/bridgecad-bill:/app/packages/bridgecad-qa:/app/packages/bridgecad-export:/app/packages/bridgecad-plugins:/app/packages/bridgecad-ai:/app/packages/bridgecad-infra

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends libcairo2 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

WORKDIR /app
COPY packages/ packages/
COPY apps/streamlit-ui/ streamlit/

# Streamlit config
RUN mkdir -p /app/.streamlit
COPY apps/streamlit-ui/.streamlit/config.toml /app/.streamlit/config.toml 2>/dev/null || \
    printf '[server]\nheadless = true\nport = 8501\nenableCORS = false\nenableXsrfProtection = false\n' \
    > /app/.streamlit/config.toml

RUN addgroup --system bridgecad && adduser --system --ingroup bridgecad bridgecad
RUN chown -R bridgecad:bridgecad /app
USER bridgecad

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

WORKDIR /app/streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
