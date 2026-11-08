# Bridge_GAD User Manual (LEGACY)

> ⚠️ **SUPERSEDED — DO NOT USE.** This page describes a **different, older product**
> (a standalone `Bridge_GAD_Setup.exe` with a menubar and no Python). The current
> software is the **BridgeCAD Enterprise Suite** — a Python/Streamlit/CLI/FastAPI
> suite driven by an Excel workbook.
>
> **Read the current manual instead:** [USER-MANUAL.md](USER-MANUAL.md).
> This file is retained for historical reference only.

**Software:** Bridge_GAD  
**Version:** 2.0.0  
**Author:** Er. Rajkumar Singh Chauhan  
**Institution:** Institution of Engineers (India), Udaipur Local Centre  
**License:** Open Engineering Utility (Educational Use)

---

## Introduction

Bridge_GAD is an automated tool for **Bridge General Arrangement Drawing (GAD) generation**,
developed to assist engineers, designers, and students in quickly preparing
standard bridge layout drawings.

It simplifies:
- Superstructure and substructure parameter inputs
- Span geometry generation
- Abutment, pier, and bearing detail configuration
- Export of computed layouts to CAD formats

---

## System Requirements
- Windows 10 or later (64-bit)
- Minimum 4 GB RAM
- Python not required (standalone .exe)
- Optional: AutoCAD for DWG viewing

---

## Installation

1. Download `Bridge_GAD_Setup.exe` from  
   [GitHub Releases](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/releases)
2. Run the installer and follow on-screen instructions.
3. Launch Bridge_GAD from Desktop or Start Menu.

---

## Graphical User Interface (GUI)

Upon launch, the splash screen appears with project credits.

### Main Modules
- **Input Panel:** Define bridge geometry and loading parameters  
- **Analysis Engine:** Performs structural computation  
- **Output Tab:** Exports results and drawings

### Menubar
- **File → Open/Save Project**
- **Help → About**
- **Help → Check for Updates**

---

## Command-Line Mode (Optional)

If you prefer terminal usage, you can run:

```
Bridge_GAD.exe --input project.json --output results/
```

---

## Updating

The application automatically checks for new versions from GitHub.
You can also check manually via **Help → Check for Updates**.

---

## Credits

Developed and maintained by  
**Er. Rajkumar Singh Chauhan, Retd. Addl. Chief Engineer, PWD Rajasthan**  
For academic and professional use under the  
**Institution of Engineers (India), Udaipur Local Centre**.

---