# How to use — in video form

> **Status:** W01 follow-up · drafted 2026-10-29.
> A walkthrough you can *watch*: the storyboard below is the shot list for the
> "How to use" video, and the player is wired to it. The written companion is
> the [user manual](Bridge_GAD_User_Manual.md).

![How-to-use walkthrough — cover frame](https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=engineering%20desk%20with%20a%20CAD%20workstation%20showing%20a%20seven-sheet%20bridge%20general%20arrangement%20drawing%20package%20on%20screen%2C%20blueprint%20style%2C%20professional%20software%20tutorial%20thumbnail&image_size=landscape_16_9)

## The video

```html
<video controls width="100%"
       poster="https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=engineering%20desk%20with%20a%20CAD%20workstation%20showing%20a%20seven-sheet%20bridge%20general%20arrangement%20drawing%20package%20on%20screen%2C%20blueprint%20style%2C%20professional%20software%20tutorial%20thumbnail&image_size=landscape_16_9">
  <source src="assets/how-to-use.mp4" type="video/mp4">
  Your browser does not support embedded video —
  the storyboard below covers the same ground.
</video>
```

Until the rendered `assets/how-to-use.mp4` is committed, follow the storyboard.

## Storyboard (the script)

| # | Time | On screen | Narration |
|---|---|---|---|
| 1 | 0:00–0:15 | Title card: *One workbook in. Seven sheets out.* | "BridgeCAD turns one parametric Excel workbook into a standards-compliant drawing package, a priced BOQ and a QA report." |
| 2 | 0:15–0:45 | `python -m bridgecad verify` scrolling its 7/7 and 8/8 checks | "No install needed. Clone, then run one command — the acceptance verifiers tell you the repo is healthy." |
| 3 | 0:45–1:30 | Opening `bridge.xlsx`; the 14 sheets, yellow inputs highlighted | "The workbook is the only contract. Fill the yellow cells; calculated cells stay locked." |
| 4 | 1:30–2:30 | `bridgecad-cli draw booklet bridge.xlsx -o out/` → seven DXFs open in a viewer | "One command draws all seven sheets — plan, long section, cross sections, foundation, pier and abutment, bearings and joints, BOQ." |
| 5 | 2:30–3:15 | The priced BOQ and the QA compliance grade | "Every BOQ line carries its inputs; the QA engine scores the project out of 100 against 150 rules." |
| 6 | 3:15–4:00 | `manifest.json` with the *"Generated — not reviewed for construction."* notice | "Until CI is green and every sheet is engineer-reviewed, the manifest says so plainly. This is a release candidate." |
| 7 | 4:00–4:30 | Streamlit console tabs and the React console pages | "Prefer a GUI? The Streamlit console and the React web app drive the same engine." |
| 8 | 4:30–5:00 | Closing card: links to the guide and the manual | "Read the guide next — and the user manual for the field detail." |

## The manual, on screen

The video closes on the generated user manual. Read it in full here:

- [**User manual** — Bridge_GAD_User_Manual.md](Bridge_GAD_User_Manual.md)
- [PDF edition](Bridge_GAD_User_Manual.pdf)

## Next

- Quick start → [getting-started.md](getting-started.md)
- The authoritative guide → [GUIDE.md](../GUIDE.md)
- What may and may not be claimed → [GUIDE.md §11](../GUIDE.md)
