---
name: "W02 · Dependency discipline"
about: "Phase 1 — reproducible installs, locked deps, pre-commit"
title: "W02 · Dependency discipline"
labels: "roadmap,phase-1,w02"
---

**Phase:** 1 · Foundation & truth-up
**Week:** 2 – 8 Nov 2026

## Objective
Make "works on my machine" provable.

## Deliverables
- [ ] `pyproject.toml` (PEP 621) with `[project.optional-dependencies].dev`
- [ ] Lockfile committed (uv.lock or poetry.lock)
- [ ] `requirements-streamlit.txt` removed or auto-generated from lock
- [ ] No floating version pins in prod deps
- [ ] `.pre-commit-config.yaml`: ruff format, ruff check, mypy, detect-secrets
- [ ] Dockerfile installing from lockfile
- [ ] CI matrix includes Python 3.11 and 3.12

## Definition of done
- [ ] `docker build` succeeds from scratch, no cache
- [ ] pre-commit blocks a commit with a deliberate lint error and a fake secret
- [ ] `uv sync` (or equivalent) reproduces the exact environment

## Verification
```bash
docker build -t bc-suite .
pre-commit run --all-files
```

## Evidence
