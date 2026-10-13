# ─────────────────────────────────────────────────────────────────────────────
# BridgeCAD CLI Console — multi-arch Dockerfile
# Targets: linux/amd64  linux/arm64
# Usage:
#   docker run --rm -v $(pwd)/input.xlsx:/work/input.xlsx \
#     bridgecad/cli:0.1.0-rc1 draw gad /work/input.xlsx -o /work/output
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential libcairo2 libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY packages/ packages/
RUN pip install --upgrade pip && \
    for pkg in packages/*/pyproject.toml; do \
        dir="${pkg%/pyproject.toml}"; pip install "$dir"; \
    done && \
    pip install typer rich openpyxl pyyaml ezdxf scipy numpy

# ── Runtime ──────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/packages/bridgecad-core:/app/packages/bridgecad-io:/app/packages/bridgecad-draw:/app/packages/bridgecad-bill:/app/packages/bridgecad-qa:/app/packages/bridgecad-export:/app/packages/bridgecad-plugins:/app/packages/bridgecad-ai:/app/packages/bridgecad-infra

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends libcairo2 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

WORKDIR /app
COPY packages/ packages/
COPY apps/cli-console/ cli/

RUN addgroup --system bridgecad && adduser --system --ingroup bridgecad bridgecad
RUN chown -R bridgecad:bridgecad /app
USER bridgecad

VOLUME ["/work"]
WORKDIR /work

# Default: show help
ENTRYPOINT ["python", "-m", "bridgecad_cli"]
CMD ["--help"]
