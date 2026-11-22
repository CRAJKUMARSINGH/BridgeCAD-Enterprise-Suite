# BridgeCAD Enterprise Suite

Bridge General Arrangement Drawing (GAD) generation, QA, BOQ and export suite.

## ⚠️ STANDING ORDER — repository layout

1. **All code files live in folders** (`packages/`, `apps/`, `scripts/`, `tests/`, ...).
   No new code files at the repository root.
2. **The only exception is `CODE-JUNCTION/`.**
3. **`CODE-JUNCTION/` holds ONLY new enhancement guides and patches**, waiting to be
   applied. Once a patch is applied, tested and merged into its proper folder,
   **its guide and patch are DELETED from `CODE-JUNCTION/`.**

## Original LISP and dirt-wall references

- [YogiPWD: explanation of Shri P. M. Baviskar's solid-slab GAD AutoLISP](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html?m=1).
  The preserved files are in `ATTACHED ASSETS/`. Preservation and static inventory
  are distinct from an executable, validated port.
- [Prewallcivil: dirt wall in bridge abutment](https://prewallcivil.com/dirt-wall-in-bridge-abutment/).
  Use this as contextual reading about retained fill and drainage, not as an
  approved dimensional, reinforcement or construction-joint specification.
- [LISP preservation and accuracy work](docs/LISP_FIDELITY_AND_DIRT_WALL.md):
  implemented changes, compatibility API and the remaining acceptance tests.

## Quick start

```bash
pip install -e packages/bridgecad-core -e packages/bridgecad-draw -e packages/bridgecad-ai
streamlit run apps/streamlit-ui/app.py
python -m pytest -q tests/draw
```

## Drawing review

```bash
python -m bridgecad_ai.drawing_review sheet.dxf requirements.json        # rule checks
LOVABLE_API_KEY=... python -m bridgecad_ai.drawing_review sheet.dxf requirements.json --ai
```
Or use the **🔎 Drawing Review** tab in the Streamlit app.
