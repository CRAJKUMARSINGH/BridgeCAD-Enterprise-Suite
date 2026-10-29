# Minimal image for the CI container smoke test and for docker-compose.
#
# W02 dependency discipline: the image installs the PINNED Suite dependency set
# (requirements.lock) rather than the legacy loose pin set (requirements.txt).
# A build from the lockfile is reproducible; a build from `>=` ranges is not.
# The image's contract is the Suite facade `bridgecad` — the legacy
# `src/bridge_gad` surface is fenced (ADR-0001) and no longer exercised here.
FROM python:3.11-slim

# PYTHONPATH=/app so the repo-root sitecustomize.py fires at interpreter start
# and injects every workspace package (bridgecad_core, …) into sys.path.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

CMD ["python", "-c", "import bridgecad as bc; print('BridgeCAD Suite image OK', bc.__version__)"]
