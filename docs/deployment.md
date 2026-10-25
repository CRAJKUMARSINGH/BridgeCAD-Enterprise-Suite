# Deployment

## Local

```bash
cp .env.example .env
docker compose up api                 # API on :8000
docker compose up                     # + postgres, redis, minio, jaeger
```

Dev compose includes Jaeger for tracing. Prod compose does not.

## Production

```bash
cp .env.example .env      # then edit every secret
docker compose -f docker-compose.prod.yml up -d
```

Services: api · streamlit · web · postgres · redis · minio · nginx.

`nginx/prod.conf` handles SSL termination, WebSocket upgrade for Streamlit,
and a 50 MB upload limit. Keep the upload limit in sync with the app-side cap
once it lands (see `GUIDE.md` §8 — currently open).

## Images

Multi-arch (`linux/amd64` + `linux/arm64`), 2-stage builds, non-root users,
healthchecks on api and streamlit. Published to ghcr.io by `release.yml`.

## Environment

All config is environment-driven. `.env.example` documents 60+ variables across:
database DSN, redis URL, S3/MinIO credentials, API keys and role ladder,
OTel/Jaeger endpoint, upload limits, rate-schedule version pin.

**Secrets rules**

- `.env` is never committed. `.env.example` always is.
- Rotate API keys via `bridgecad_infra.auth.generate_api_key()`.
- Roles are a strict ladder: `admin > engineer > viewer`. No per-resource ACLs yet.

## Required env vars in production

| Var | Notes |
|---|---|
| `DATABASE_URL` | postgres, not sqlite |
| `REDIS_URL` | cache + queue |
| `S3_ENDPOINT` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` | artifact storage |
| `API_KEY_SALT` | constant-time verification |
| `RATE_SCHEDULE_VERSION` | pin it — rates are versioned data |

## Health and readiness

```bash
curl localhost:8000/health
```

Returns `{"status":"ok"}`. Use it for both liveness and readiness probes. It
does not touch the database — a db outage should not restart the api.

## Observability

- **Logs** — structlog JSON in prod, stdlib in dev. Correlate on request ID.
- **Metrics** — Prometheus scrape endpoint.
- **Traces** — OTel collector → Jaeger.

## Backups

Postgres holds project records, bridge records and generation history.
`manifest.json` artifacts live in S3/MinIO. Back up both. Test a restore before
you need one.

## Scaling

API and Streamlit are stateless — scale horizontally. Long jobs go through the
arq queue, so add workers rather than api replicas if the bottleneck is
generation, not requests.

## Upgrade

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Alembic migrations run on api start. **Back up the database first** — migrations
are forward-only.

## Rollback

Pin image tags by digest, not `latest`. Roll back by re-pinning and redeploying.
Schema rollback needs a restore unless the migration is additive.

## Kubernetes

A Helm chart is planned (`charts/bridgecad/`). Until then, the prod compose file
maps cleanly onto a Deployment + Service + Ingress, with postgres and redis as
managed services.

## Pre-flight checklist

- [ ] Every secret in `.env` changed from the example
- [ ] `DATABASE_URL` points at postgres
- [ ] `RATE_SCHEDULE_VERSION` pinned
- [ ] TLS certificate in place, nginx config validated
- [ ] Upload limit set in nginx
- [ ] Health probes wired
- [ ] Database backed up
- [ ] `python rc1_smoke.py` green on the release commit
