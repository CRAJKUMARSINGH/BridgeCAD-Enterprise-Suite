# Deploying the BridgeCAD Python backend

The Netlify frontend at **https://bridge-gad.netlify.app** proxies every
`/api/predict` and `/api/health` request through `netlify/functions/`.
When `FASTAPI_URL` is set, those functions forward the request to your Python
service. Without it they return HTTP 501 (`mode: demo`).

This document describes the fastest path to a live backend.

---

## Option A — Render.com (recommended, one click)

Render is the lowest-friction host for a FastAPI service from a public GitHub
repo. The free tier is sufficient for testing; upgrade to Starter ($7/mo) for
always-on production.

### Steps

1. **Push `render.yaml` to `main`** — already committed (`0e599f4`).

2. **Create the Blueprint service.**
   - Log in to <https://dashboard.render.com>.
   - Click **New → Blueprint**.
   - Connect your GitHub repo
     `https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite`.
   - Render detects `render.yaml` automatically. Click **Apply**.
   - Wait for the build to finish (~3–5 min). The service URL will be
     `https://bridgecad-api.onrender.com` (or similar).

3. **Confirm the service is healthy.**
   ```
   curl https://bridgecad-api.onrender.com/health
   # Expected: {"status":"ok","mode":"live","python":"online"}
   ```

4. **Set `FASTAPI_URL` in Netlify.**
   - Netlify → your site → **Site settings → Environment variables**.
   - Add (or update) `FASTAPI_URL = https://bridgecad-api.onrender.com`
     (no trailing slash).
   - Scope it to **Production** only.

5. **Trigger a Netlify redeploy.**
   - Netlify → Deploys → **Trigger deploy → Deploy site**.
   - After the deploy, visit the site and check
     `https://bridge-gad.netlify.app/api/health`:
     ```json
     {"frontend":"online","python":"online","mode":"live"}
     ```

6. **Test the PDF download.**
   - Open the live site.
   - Upload `frontend/public/samples/sample_input.xlsx` on the **Drawing Gen**
     tab.
   - Select **PDF** format, click **Generate GAD DXF Package**.
   - Download the file. Open it and verify all 11 pages contain drawings.

---

## Option B — Railway.app

Railway can also deploy directly from GitHub with a `Procfile`. The `Procfile`
is committed at the repo root.

1. Go to <https://railway.app> → **New Project → Deploy from GitHub repo**.
2. Select `BridgeCAD-Enterprise-Suite`.
3. Railway reads `Procfile` and sets `web: uvicorn bridgecad_api.main:app …`.
4. Set environment variables in the Railway dashboard (same list as Render).
5. Copy the service URL into Netlify `FASTAPI_URL`.

---

## Required environment variables

Set these in the cloud dashboard — never in git:

| Variable | Value |
|---|---|
| `APP_SECRET_KEY` | 64+ random hex chars (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `BRIDGECAD_API_KEYS` | `your-key:admin` — used by API key auth |
| `API_CORS_ORIGINS` | `https://bridge-gad.netlify.app` |
| `ENV` | `production` |
| `LOG_LEVEL` | `INFO` |

Optional (leave blank to disable):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string — blank uses SQLite |
| `REDIS_URL` | Redis for async job queue — blank disables ARQ |

---

## Verification checklist

- [ ] `GET /health` returns `mode: live` and `python: online`
- [ ] Netlify `/api/health` returns `mode: live`
- [ ] Upload sample workbook → PDF → 11 non-blank pages download correctly
- [ ] `GET /health` still returns healthy after 20 min idle (Render free sleeps;
      Starter or UptimeRobot ping at 14-min intervals prevents this)

---

## CORS note

`API_CORS_ORIGINS` must include the Netlify frontend origin exactly.
The gateway's CORS middleware (`apps/api-gateway/bridgecad_api/main.py`) reads
this variable; mismatches produce `403` on cross-origin preflight requests.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/api/health` returns `mode: demo` | `FASTAPI_URL` not set in Netlify | Add the variable and redeploy |
| `/api/predict` returns HTTP 501 | Same as above | Same fix |
| `/api/predict` returns HTTP 502 | Render service sleeping (free tier) | Wait 30 s and retry, or upgrade to Starter |
| `/api/predict` returns HTTP 500 | Python generation error | Check Render service logs |
| PDF downloads but won't open | Content-type mismatch | Confirm the patched `/predict` fast-path is running (`0e599f4`) |
| CORS error in browser console | `API_CORS_ORIGINS` mismatch | Set to exact Netlify URL |
