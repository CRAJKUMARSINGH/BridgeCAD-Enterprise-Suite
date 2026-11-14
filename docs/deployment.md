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

## Capacity / volume smoke test (proxy)

There is no load harness in the repo. Before a release, approximate about a
thousand real requests with a **tier-weighted batch over the built-in
templates** — a practical proxy for volume, not a measured capacity figure.

Corpus: the templates in
[getting-started.md](getting-started.md#your-first-bridge-end-to-end), plus the
28 fixtures in `tests/e2e/fixtures/`.

A single workbook per tier must clear the full pipeline — validate, export (ZIP +
`manifest.json`), BOQ, QA:

```bash
bridgecad-cli validate bridge.xlsx
bridgecad-cli export all bridge.xlsx -o out/
bridgecad-cli bill gen --input bridge.xlsx --format all
bridgecad-cli qa report bridge.xlsx -o out/qa.html
```

The volume proxy is a batch loop weighted to the tier mix — 600 basic,
300 intermediate, 100 advanced. Any non-zero exit, or a run that leaves no
`manifest.json`, fails the exercise:

```bash
# 600 x basic (simple_12m)
for i in $(seq 1 600); do
  bridgecad-cli template new --type simple_12m -o runs/$i.xlsx
  bridgecad-cli export all runs/$i.xlsx -o runs/out/$i/ || exit 1
done
```

Repeat with `continuous_3x12m`/`girder_4x18m` × 300 and `arch_24m` × 100.
Confirm each interface serves the same pipeline first — CLI, API (`/draw`
`/bills` `/qa` `/exports`), Streamlit, React console; see
[getting-started.md](getting-started.md#path-d--the-four-interfaces).

**Pass criteria:** every workbook validates, exports without error, and produces
`manifest.json`. Output still carries *"Generated — not reviewed for
construction."*

## Pre-flight checklist

- [ ] Every secret in `.env` changed from the example
- [ ] `DATABASE_URL` points at postgres
- [ ] `RATE_SCHEDULE_VERSION` pinned
- [ ] TLS certificate in place, nginx config validated
- [ ] Upload limit set in nginx
- [ ] Health probes wired
- [ ] Database backed up
- [ ] `python rc1_smoke.py` green on the release commit
- [ ] Volume smoke test run (see *Capacity / volume smoke test (proxy)*)


## Browser landing page and Netlify frontend

A Netlify static frontend does not execute Python CAD generation. Deploy the
existing backend separately and configure the actual frontend's API base URL
or same-origin proxy. Verify its build command and output directory rather
than copying example values without inspection. Never place secrets in
frontend `VITE_` variables.

Expose drawing selection, sample scenario, existing-workbook import, layout
choice, variable help, verification status and the manual from the landing
page. Disable unsupported drawing/export choices and disconnected Generate
controls. Preserve approximation warnings and show job failures.

Before release, test desktop, mobile and keyboard journeys through a real
staging backend: choose implemented drawing, change inputs, validate, preview,
generate, download and inspect manifest. Retain frontend/backend commit IDs,
fixtures, logs, per-view reference acceptance and rollback targets. Configure
CORS, health checks, request/job limits and authenticated artifact downloads.
The supplied P.W.D. reference is marked in-house use only; keep it private.
No Netlify deployment or complete browser-generation journey was executed in
this audit. The companion Site publication failed at the hosting provider.

See [the supplementary workflow guide](BRIDGECAD_SUPPLEMENTARY_PATCH.md) and
[the uploaded-instruction ledger](V_INSTRUCTIONS_APPLIED.md).


### Explicit development health mode

Vite now proxies `/api/health` to the configured local backend by default. For a deliberate static-demo development session, set `VITE_DEMO_HEALTH=1` in `frontend/.env.local` (or the shell) before starting Vite. This switch only enables a demo health response; it does not enable Python generation. Never put private credentials in VITE_ variables. Production health remains handled by the deployment backend.
