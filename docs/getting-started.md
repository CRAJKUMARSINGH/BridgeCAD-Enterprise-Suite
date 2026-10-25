# Getting started

Four paths. Pick one. Path A needs no install at all.

> **First:** the Suite lives at the repo root. If any doc tells you to
> `cd` into a legacy `BridgeCAD Enterprise Suite` directory, it is stale.

## Path A — zero install (verify the repo works)

```bash
git clone https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite.git
cd BridgeCAD-Enterprise-Suite

python -m bridgecad                 # banner + usage
python -m bridgecad info            # interpreter, repo root, workspace paths
python -m bridgecad verify          # day3 (7/7) + day4 (8/8)
```

This works with no `pip install` because `sitecustomize.py` at the repo root
puts `packages/*` and `apps/*` on `sys.path`. **Run from the repo root.**

If you see `ModuleNotFoundError: bridgecad_core`, you are in the wrong directory.

## Path B — development install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
make lint && make test
```

## Path C — full stack in Docker

```bash
cp .env.example .env
docker compose up api              # FastAPI on :8000
curl localhost:8000/health         # {"status":"ok"}
docker compose up                  # + postgres, redis, minio, jaeger
```

## Path D — the four interfaces

```bash
pip install -e apps/cli-console && bridgecad-cli --help
streamlit run apps/streamlit-ui/app.py
cd apps/web-console && npm ci && npm run dev
```

---

## Your first bridge, end to end

**1. Make a workbook.** Do not hand-build one.

```bash
bridgecad-cli template new --type simple_12m -o bridge.xlsx
```

`simple_12m` is a 12 m single-span template. Other built-ins:
`continuous_3x12m`, `girder_4x18m`, `box_culvert_8m`, `arch_24m`.

**2. Validate it before doing any work.**

```bash
bridgecad-cli validate bridge.xlsx
```

Every field comes back `valid`, `warning`, `blocked` or `unsupported`. Fix
`blocked` fields; read `warning` ones.

**3. Generate the drawing set.**

```bash
bridgecad-cli draw booklet bridge.xlsx -o out/
```

Seven DXF sheets: plan, long section, cross section, foundation,
pier/abutment details, bearings/joints, BOQ. Sheet 1 is complete; 2–7 are
scaffolds — see [GUIDE.md §11](../GUIDE.md).

**4. Price it.**

```bash
bridgecad-cli bill gen --input bridge.xlsx --format all
```

**5. Score compliance.**

```bash
bridgecad-cli qa report bridge.xlsx -o out/qa.html
```

**6. Bundle everything.**

```bash
bridgecad-cli export all bridge.xlsx -o out/
```

You get a ZIP with the DXF sheets, BOQ, QA report and `manifest.json`.

---

## What you get, and where

```
out/
├── dxf/           7 sheets
├── pdf/           print-ready
├── boq.xlsx       priced, 8 sections
├── qa.html        compliance report, 0-100 grade
└── manifest.json  versions, standards, input hash, QA findings
```

`manifest.json` is the audit trail. Keep it with the output.

---

## Via the API

```bash
pip install -e apps/api-gateway
uvicorn bridgecad_api.main:app --reload

curl -F file=@bridge.xlsx localhost:8000/draw/gad -o gad.dxf
curl -F file=@bridge.xlsx localhost:8000/qa/report -o qa.html
```

Routers: `/bridges` `/draw` `/bills` `/qa` `/exports` `/plugins` `/health`.
OpenAPI docs at `/docs`.

---

## Next

| Want | Read |
|---|---|
| To understand the workbook | [excel-contract.md](excel-contract.md) |
| To know what standards are enforced | [standards.md](standards.md) |
| To add a bridge type | [plugin-authoring.md](plugin-authoring.md) |
| To ship it | [deployment.md](deployment.md) |
| Something is broken | [troubleshooting.md](troubleshooting.md) |
