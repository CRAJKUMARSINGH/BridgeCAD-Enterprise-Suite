# BridgeCAD — video guide and user manual

Watch the 2-minute-8-second silent captioned tutorial in learn.html. Chapter timestamps are available in the player. Open learn.html through the deployed Site or a local HTTP server for reliable video captions. The complete instructions are also reproduced here.

## 1. Know your drawing paths

Open: **Start here**.

Open the landing page. Use the capability map to choose the browser workspace or the Python catalogue. A configured link or button click is not proof of generation.

- Browser: three drawing views and two deck families.
- Python: 15 catalogue configurations and nine-sheet packages.
- A static website cannot launch your local Python process.

## 2. Select a drawing family

Open: **Drawing catalogue**.

Open Drawing catalogue. Choose a configuration by foundation and superstructure. Read its reference-page mapping. Do not assume the browser renderer supports every Python configuration.

- Match foundation and superstructure to your project.
- Read the configuration ID and reference PDF page.
- Types 004, 014 and 015 remain approximate.

## 3. Vary inputs carefully

Open: **Variables & layout**.

In Variables & layout, set skew_deg to 25 and inspect the comparison table. A value of 35 is outside the current 0–30 degree range. The Python resolver must still check dependent dimensions and engineering constraints.

- Example: choose BR-I-2022-001, then set skew to 25°.
- Unedited controls retain the catalogue baseline.
- Check units, limits and derived engineering constraints.

## 4. Choose media and layout

Open: **Variables & layout**.

Paper and orientation control PNG export when the render-media CLI patch is installed. Proposed CAD scale does not create paper-space viewports or change DXF geometry. Choose scale for readability and inspect every view.

- Select A0–A4 and landscape or portrait for PNG media.
- Proposed scale estimates elevation fit only.
- Inspect notes, dimensions, sections and title block separately.

## 5. Save a repeatable scenario

Open: **Saved scenarios**.

Save the scenario, open Saved scenarios and use Load & compare. Export a JSON backup before moving devices or clearing browser data. Imported scenarios need review and a Python dry run before generation.

- Give the study a clear name, such as Skew 25 study.
- Save, reload, and compare with the baseline.
- Export a backup: scenarios live in this browser only.

## 6. Run the real generator

Open: **Python / local checkout**.

Inspect the local generator help for supported flags. Run the prepared dry run first. When it succeeds, run generation deliberately and retain output paths, resolved inputs and exit codes. Baseline runs can overwrite the existing corpus.

- Copy the prepared CLI command with dry run enabled.
- Run it in an isolated local checkout, not the webpage.
- Keep exit codes and params.resolved.json.

## 7. Verify against the PDF

Open: **Verification**.

Open generated DXF and rendered sheets alongside GENERAL ARRANGEMENT DRAWINGS.pdf. Compare span arrangement, levels, skew, foundations, dimensions, notes, title block and scales. Record each discrepancy as a bug or enrichment task; perfect fidelity remains unverified.

- Compare corresponding views at aligned scale.
- Check geometry, dimensions, labels and sheet composition.
- Record gaps; generated does not mean approved.

## 8. Test integration and release

Open: **Browser & Netlify**.

Confirm units, datum, slope direction, parameter names and error handling across integrations. For the existing frontend Netlify setup, verify base frontend, build npm run build and publish dist. Deploying static pages does not deploy a Python backend.

- Test each app independently and retain evidence.
- Check Slope-Logic-Manager → Dwg-Param-Mapper contracts.
- Wire Bridge-Design-Suite only after end-to-end checks.

## Start offline

Extract the ZIP, then run `python -m http.server 8080` in its folder. Open `http://localhost:8080/learn.html`. The back/try links expect the full BridgeCAD deployment; use the video and this manual offline. For direct MP4 playback, use a video player; the VTT captions may need to be loaded separately.

This tutorial does not certify generated drawings or reference fidelity.
