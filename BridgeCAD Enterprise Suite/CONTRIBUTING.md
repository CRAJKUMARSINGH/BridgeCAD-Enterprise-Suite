# Contributing to BridgeCAD Enterprise Suite

Thank you for considering a contribution. This document covers the process for reporting bugs, proposing features, and submitting pull requests.

---

## Code of Conduct

Be respectful and constructive. Engineering discussions should stay technical. Personal attacks or harassment will not be tolerated.

---

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/bridgecad/enterprise-suite/issues) first.
2. Open a new issue with:
   - BridgeCAD version (`bridgecad --version`)
   - Python version + OS
   - Minimal reproducer (Excel workbook or fixture JSON if possible)
   - Expected vs actual output
   - Full traceback

### Proposing Features

Open a GitHub Discussion or issue with:
- The IRC/MORTH standard clause you're targeting
- Which bridge type / drawing sheet it affects
- A rough description of the expected output

### Pull Requests

1. **Fork** the repository and create a branch: `git checkout -b feat/my-feature`
2. **Install** dev deps: `pip install -e packages/[all] && pip install -e packages/[dev]`
3. **Install** pre-commit: `pre-commit install`
4. **Write** your code — follow the existing style (ruff-formatted, mypy-checked).
5. **Write** or update tests in `tests/` — the CI gate requires all 34 rc1_smoke checks to pass.
6. **Run** the full suite locally:
   ```bash
   python rc1_smoke.py          # must stay 34/34
   python tests/e2e/run_e2e.py  # must stay 28/28
   ```
7. **Open** a PR against `main`. Fill in the PR template.

---

## Development Setup

```bash
git clone https://github.com/bridgecad/enterprise-suite
cd "BridgeCAD Enterprise Suite"

# Python packages
pip install --upgrade pip
for pkg in packages/*/pyproject.toml; do pip install -e "${pkg%/pyproject.toml}"; done
pip install pytest pytest-cov ruff mypy pre-commit openpyxl ezdxf scipy numpy pyyaml

# Pre-commit hooks
pre-commit install

# Verify everything passes
python rc1_smoke.py
```

### Makefile targets

```bash
make install      # install all packages
make lint         # ruff check
make format       # ruff format
make typecheck    # mypy on core + io + bill
make test         # unit + integration
make test-e2e     # 28-fixture E2E suite
make bench        # performance benchmarks
make docker-up    # dev stack (api + db + redis + minio)
```

---

## Adding a New Bridge-Type Plugin

1. Create a directory: `packages/bridgecad-plugins/bridgecad_plugins/plugins/<plugin_id>/`
2. Add `manifest.json` — copy from `plugins/rcc_tbeam/manifest.json` and edit.
3. Add `defaults.yaml` — typical field values for your bridge type.
4. Add `draw_overrides.py` — implement `describe()`, `get_typical_values()`, `apply_defaults()`.
5. Add an E2E fixture JSON in `tests/e2e/fixtures/`.
6. Run `python tests/e2e/run_e2e.py` — your new fixture must pass.

---

## Adding a Drawing Sheet

1. Create `packages/bridgecad-draw/bridgecad_draw/sheet<N>_<name>.py`.
2. Export a `generate(project, output_path, scale_denom) -> Path` function.
3. Import it in `booklet.py` via the `_SHEET_MANIFEST` list.
4. Update the smoke test assertion from `len(sheets) >= N` to `N+1`.

---

## IRC/MORTH Standards Updates

- YAML data files live in `standards/`.
- Python formula modules live in `packages/bridgecad-core/bridgecad_core/standards/`.
- Every formula must cite the IRC clause in its docstring.
- Do not invent engineering values — use only published standards.

---

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(draw): add sheet3 cross-section parabolic camber
fix(bill): correct pile-cap volume for 2×3 grid layout
docs(readme): add quick-start Docker instructions
test(e2e): add Chambakkara 5×25m PSC fixture
refactor(core): extract _concrete_ordinal into types module
```

Commitizen enforces this via the pre-commit hook.

---

## Code Style

- **Python**: ruff format + ruff lint (line length 110, target py311)
- **TypeScript**: Vite/tsc strict mode, no `any`
- **YAML**: 2-space indent, comments for every section
- **Docstrings**: NumPy style with `Parameters`, `Returns`, `Reference`

---

## Questions?

Open a [GitHub Discussion](https://github.com/bridgecad/enterprise-suite/discussions) or email `dev@bridgecad.io`.
