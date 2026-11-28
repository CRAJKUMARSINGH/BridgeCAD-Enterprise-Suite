# Deploying the BridgeCAD Python backend

The Netlify frontend at **https://bridge-gad.netlify.app** proxies every
`/api/predict` and `/api/health` request through `netlify/functions/`.
When `FASTAPI_URL` is set, those functions forward the request to your Python
service. Without it, `/api/health` reports `mode: demo` and generation returns HTTP 501.

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
   # Expected: {"status":"ok","version":"…","packages_loaded":[…]}
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
   - Select **PDF** under **Format & variants**.
   - In **Export package**, upload `frontend/public/samples/sample_input.xlsx`
     and choose **Generate via Python engine**.
   - Open the download and verify all 11 pages contain drawings. Repeat with
     **DXF package (ZIP)** and **Plan PNG** to check the archive and raster outputs.
   - The PDF booklet is a fit-to-page review copy. Use the native DXF sheets
     or the dedicated A1 GAD PDF printed at 100% for scale-based measurements.

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

- [ ] Run `python scripts/check_software_launch.py` on the release commit.
- [ ] Open `/#drafting` on the staging site, load a sample preset and check that
      invalid geometry blocks SVG and DXF exports. Correct it and inspect both
      downloaded review drawings. This path needs only the static frontend.
- [ ] Direct gateway `GET /health` returns `status: ok`
- [ ] Netlify `/api/health` returns `mode: live`
- [ ] Upload sample workbook → PDF → 11 non-blank pages download correctly
- [ ] `GET /health` still returns healthy after 20 min idle (Render free sleeps;
      Starter or UptimeRobot ping at 14-min intervals prevents this)

---

## Rollback

Record the frontend deploy ID, gateway revision, and commit SHA before promotion.
If the release fails its smoke checks, republish the previous successful Netlify
deploy and roll the gateway back to the corresponding revision. Check
`/api/health` and download a drawing from the sample workbook to confirm the
restored pair works together. Keep the failed release logs for diagnosis.

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
| `/api/predict` returns HTTP 404 | Gateway deployment lacks the workbook download route | Check `/openapi.json` on the gateway for `POST /predict` and deploy the current gateway build |
| CORS error in browser console | `API_CORS_ORIGINS` mismatch | Set to exact Netlify URL |
