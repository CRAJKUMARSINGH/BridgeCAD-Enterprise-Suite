# 🌉 Bridge GAD Generator

**Transform Excel Spreadsheets into Professional AutoCAD Bridge Drawings in Seconds**

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg)](https://streamlit.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## ✨ What Makes This Brilliant?

**Bridge GAD Generator** is a lightning-fast Python tool that automates bridge design drafting. Upload an Excel file with bridge parameters, click generate, and download professional AutoCAD-compatible DXF drawings in under 2 seconds. No manual CAD work, no expensive software licenses, no weeks of drafting time.

Built for civil engineers, contractors, and consultants who need to produce IRC/IS-compliant bridge drawings quickly and accurately. Save 40+ hours per project and eliminate human drafting errors.

**One Excel file in. Professional CAD drawings out. That simple.**

---

## 🚀 Key Features

- ⚡ **Lightning Fast** – Generate complete bridge drawings in 1-2 seconds
- 📐 **Professional Quality** – AutoCAD 2006/2010 DXF format with proper layers and dimensions
- 📋 **5 Built-in Templates** – Start instantly with pre-configured bridge types (12m span, 3×12m continuous, 4×18m girder, box culvert, arch)
- ✅ **Standards Compliant** – Automatic IRC/IS code validation with compliance scoring
- 🎨 **Multi-View Drawings** – Elevation, plan, cross-sections, and detailed pier/abutment geometry
- 📦 **Batch Processing** – Generate dozens of designs at once
- 🌐 **Web Interface** – Clean Streamlit UI, no CAD software needed
- 🔧 **Zero Configuration** – Works out of the box with minimal dependencies

---

## 📸 Demo

> **Coming Soon:** 30-second demo GIF showing Excel upload → DXF generation → AutoCAD import

**What You Get:**
- Detailed elevation views with dimensions
- Plan views with pier/abutment layouts
- Cross-section plots with terrain profiles
- Professional title blocks and annotations
- Multi-span bridge support (1-10 spans)
- Skewed bridge geometry
- Foundation details

---

## ⚡ Quick Start (Under 90 Seconds)

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation & Run

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/bridge-gad-generator.git
cd bridge-gad-generator

# 2. Install dependencies (6 packages only!)
pip install -r requirements_lean.txt

# 3. Launch the app
streamlit run app_lean.py

# 4. Open your browser
# → http://localhost:8501
```

**That's it!** Upload an Excel file or use a template to generate your first bridge drawing.

---

## 📖 How to Use

### Method 1: Use a Template (Fastest)
1. Click the **Templates** tab
2. Select a bridge type (e.g., "Simple Span 12m")
3. Download the Excel template
4. Modify parameters if needed
5. Upload in **Single File** tab
6. Click **Generate** → Download DXF

### Method 2: Custom Excel File
1. Create Excel file with 3 columns: `Value`, `Variable`, `Description`
2. Add required parameters (see [Parameter Guide](#required-parameters))
3. Upload file in **Single File** tab
4. Review quality check results
5. Click **Generate Bridge Design**
6. Download your professional DXF file

### Method 3: Batch Processing
1. Prepare multiple Excel files
2. Upload all files at once
3. Click **Process All**
4. Download ZIP with all DXF files

---

## 🔧 Required Parameters

Your Excel file must include these bridge parameters:

**Basic Geometry:**
- `SCALE1`, `SCALE2` – Drawing scales
- `SKEW` – Bridge skew angle (degrees)
- `DATUM`, `TOPRL` – Reference levels (m)
- `LEFT`, `RIGHT` – Bridge extents (m)
- `NSPAN` – Number of spans
- `LBRIDGE` – Total bridge length (m)
- `SPAN1` – Individual span length (m)

**Structural Elements:**
- `CAPT`, `CAPB`, `CAPW` – Pier cap dimensions (m)
- `PIERTW`, `BATTR`, `PIERST` – Pier geometry (m)
- `SLBTHC`, `SLBTHE`, `SLBTHT` – Slab thickness (m)
- `CCBR` – Carriageway width (m)

**Foundation:**
- `FUTRL`, `FUTD`, `FUTW`, `FUTL` – Footing dimensions (m)
- `ALCW`, `ALCD` – Abutment cap dimensions (m)

**See included templates for complete parameter lists.**

---

## 🛠 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI** | Streamlit 1.38+ | Web interface |
| **CAD Engine** | ezdxf 1.4.2+ | DXF file generation |
| **Data Processing** | pandas 2.3.1+ | Excel parsing |
| **Math** | numpy 1.24+ | Geometry calculations |
| **Excel I/O** | openpyxl 3.1.5+ | Excel file handling |
| **Config** | python-dotenv 1.0+ | Environment management |

**Total: 6 dependencies** (vs 54 in bloated alternatives)

---

## 🗺 Roadmap

### ✅ Completed
- [x] Core Excel → DXF generation
- [x] 5 standard bridge templates
- [x] IRC/IS standards validation (IRC 5, 6, 21, 83, SP:114 via standards.py)
- [x] Batch processing
- [x] Web interface
- [x] Multi-span support
- [x] Phase Two 7-sheet DXF package (IDX, GAD, TYP, ABT, PIER, BRG, DRN)
- [x] 4-sheet enriched Excel template (Parameters, Checklist, OwnerProfiles, SheetIndex)
- [x] 6-row enriched professional title block (STANDARD/LIVE LOAD/Bearing + DRAWN/CHECKED/APPROVED + Project Footer)
- [x] PDF export (print-ready drawings via dxf_to_pdf.py + booklet bundling)
- [x] Phase Two ZIP bundler (XLSX data + CSV manifest + DXF sheets)
- [x] IRC parameter enrichment engine (3.5m per-lane width, parapet height, drainage spacing, cross-fall)
- [x] Owner profile presets (NHAI, PWD, MORTH, RAILWAY)

### 🚧 In Progress
- [ ] SVG export (web display)
- [ ] 3D visualization preview
- [ ] Mobile-responsive UI

### 🔮 Planned
- [ ] Bill of quantities generation
- [ ] Cost estimation
- [ ] Design comparison tool
- [ ] API for programmatic access
- [ ] Desktop app (Electron)
- [ ] Cloud deployment templates

**Want a feature?** [Open an issue](https://github.com/YOUR_USERNAME/bridge-gad-generator/issues) or contribute!

---

## 🤝 How to Contribute

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** thoroughly
5. **Commit** (`git commit -m 'Add amazing feature'`)
6. **Push** (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Contribution Ideas
- Add more bridge templates
- Improve validation rules
- Add export formats (PDF, SVG, PNG)
- Enhance UI/UX
- Write documentation
- Fix bugs
- Optimize performance

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

**TL;DR:** Free to use, modify, and distribute. Commercial use allowed. No warranty.

---

## ❤️ Acknowledgments

**Inspired by:**
- BridgeCanvas – For proving that simple beats complex
- AutoCAD LISP bridge routines – For the geometric algorithms
- Civil engineering community – For feedback and requirements

**Built with:**
- [ezdxf](https://ezdxf.readthedocs.io) – Excellent DXF library
- [Streamlit](https://streamlit.io) – Beautiful web apps in Python
- [pandas](https://pandas.pydata.org) – Data manipulation powerhouse

**Special thanks to:**
- RKS LEGAL – Techno Legal Consultants for domain expertise
- All contributors and testers

---

## 📞 Support & Contact

### RKS LEGAL - Techno Legal Consultants

> Professional & legal service inquiries for RKS LEGAL are routed through
> GitHub issues or the repository discussion board — contact details are
> intentionally kept out of the public source tree.  Use the links below
> and tag your issue with `support` or `rks-legal`.

### Get Help
- 📖 [Documentation](docs/)
- 🐛 [Report Bug](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/issues)
- 💡 [Request Feature](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/issues)
- 💬 [Discussions](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/discussions)

---

## 📊 Project Stats

- **Language:** Python 3.9+
- **Files:** 3 core files (lean architecture)
- **Dependencies:** 6 packages (minimal footprint)
- **Lines of Code:** ~1,500 (focused and maintainable)
- **Generation Speed:** 1-2 seconds per drawing
- **Supported Formats:** DXF (AutoCAD 2006/2010)
- **Bridge Types:** 5 templates + unlimited custom

---

## 🏆 Why Choose This Tool?

### vs Manual CAD Drafting
- ✅ **40+ hours saved** per project
- ✅ **Zero human errors** in calculations
- ✅ **Instant regeneration** when parameters change
- ✅ **Consistent quality** across all drawings

### vs Commercial Software
- ✅ **$0 cost** (vs $5,000+ licenses)
- ✅ **No vendor lock-in**
- ✅ **Open source** – customize freely
- ✅ **Cloud-ready** – deploy anywhere

### vs Other Open-Source Tools
- ✅ **6 dependencies** (vs 50+ in alternatives)
- ✅ **3 core files** (vs 38+ scattered modules)
- ✅ **Actually works** (vs half-broken features)
- ✅ **2-second startup** (vs 10+ seconds)

---

## ⭐ Star This Repo!

**If this tool saves you time, please:**
- ⭐ **Star** this repository
- 🍴 **Fork** it for your projects
- 📢 **Share** with colleagues
- 🐛 **Report** bugs you find
- 💡 **Suggest** features you need

**Every star motivates us to keep improving!**

---

## 🚀 Get Started Now

```bash
git clone https://github.com/YOUR_USERNAME/bridge-gad-generator.git
cd bridge-gad-generator
pip install -r requirements_lean.txt
streamlit run app_lean.py
```

**Your first professional bridge drawing is 90 seconds away!**

---

<div align="center">

**🌉 Bridge GAD Generator**

*Transform Excel into AutoCAD Drawings in Seconds*

**Made with ❤️ by civil engineers, for civil engineers**

[Get Started](#-quick-start-under-90-seconds) • [Documentation](docs/) • [Report Bug](https://github.com/YOUR_USERNAME/bridge-gad-generator/issues) • [Request Feature](https://github.com/YOUR_USERNAME/bridge-gad-generator/issues)

</div>
