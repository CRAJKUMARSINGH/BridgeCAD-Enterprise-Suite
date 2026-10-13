# 🤝 Contributing to Bridge GAD Generator

**Thank you for considering contributing!** Every contribution helps make bridge engineering faster and easier for everyone.

We welcome all types of contributions: bug fixes, new features, documentation improvements, templates, and more.

---

## 🚀 Quick Start

### 1. Fork & Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/bridge-gad-generator.git
cd bridge-gad-generator
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements_lean.txt

# Install dev dependencies (optional)
pip install -r requirements-dev.txt
```

### 3. Make Your Changes

```bash
# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes
# ... edit files ...

# Test your changes
streamlit run app_lean.py

# Commit
git add .
git commit -m "Add amazing feature"

# Push
git push origin feature/amazing-feature
```

### 4. Open a Pull Request

Go to GitHub and open a PR from your branch to `main`. That's it!

---

## 💡 Contribution Ideas

### 🐛 Bug Fixes
- Fix calculation errors
- Resolve UI issues
- Improve error handling
- Fix documentation typos

### ✨ New Features
- Add more bridge templates
- Support additional export formats (PDF, SVG, PNG)
- Enhance validation rules
- Add design comparison tools
- Implement cost estimation
- Create mobile-responsive UI

### 📚 Documentation
- Improve README clarity
- Add code examples
- Create video tutorials
- Write blog posts
- Translate to other languages

### 🎨 Templates
- Create new bridge type templates
- Add regional standard variations
- Provide example Excel files
- Document parameter ranges

### 🧪 Testing
- Write unit tests
- Add integration tests
- Test with real-world data
- Validate against standards

---

## 📋 Code Guidelines

### Style
- **Keep it simple** – Follow the lean philosophy (no bloat!)
- **Use clear names** – `calculate_pier_width()` not `cpw()`
- **Add comments** – Explain *why*, not *what*
- **Format code** – Use Black or similar formatter
- **Type hints** – Add them for function parameters

### Example
```python
def calculate_span_length(
    total_length: float,
    num_spans: int,
    pier_width: float = 1.2
) -> float:
    """
    Calculate individual span length for multi-span bridge.
    
    Args:
        total_length: Total bridge length in meters
        num_spans: Number of spans
        pier_width: Width of each pier in meters (default: 1.2m)
    
    Returns:
        Individual span length in meters
    """
    effective_length = total_length - (num_spans - 1) * pier_width
    return effective_length / num_spans
```

### Testing
```bash
# Test your changes manually
streamlit run app_lean.py

# If you added tests (optional but appreciated):
pytest tests/

# Check code style (optional):
black app_lean.py
flake8 app_lean.py
```

---

## 🎯 Pull Request Process

### Before Submitting
- [ ] Code works locally
- [ ] No new errors or warnings
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Title Format
```
[Type] Brief description

Examples:
[Feature] Add PDF export support
[Fix] Resolve pier calculation error
[Docs] Improve installation instructions
[Template] Add box culvert 10m template
```

### PR Description Template
```markdown
## What does this PR do?
Brief description of changes

## Why is this needed?
Problem it solves or feature it adds

## How to test?
Steps to verify the changes work

## Screenshots (if UI changes)
[Add screenshots here]

## Checklist
- [ ] Tested locally
- [ ] Documentation updated
- [ ] No breaking changes
```

---

## 🐛 Reporting Bugs

### Before Reporting
1. Check if it's already reported in [Issues](https://github.com/YOUR_USERNAME/bridge-gad-generator/issues)
2. Try with the latest version
3. Test with a minimal example

### Bug Report Template
```markdown
**Describe the bug**
Clear description of what's wrong

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. Upload file '...'
4. See error

**Expected behavior**
What should happen instead

**Screenshots**
If applicable, add screenshots

**Environment:**
- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- App version: [e.g., 1.0.0]

**Additional context**
Any other relevant information
```

---

## 💡 Requesting Features

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you thought about

**Additional context**
Mockups, examples, or references

**Would you like to implement this?**
Yes/No/Maybe
```

---

## 🏗️ Architecture Guidelines

### Keep It Lean
This project follows the **lean philosophy**:
- ✅ Minimal dependencies (currently 6)
- ✅ Simple architecture (3 core files)
- ✅ Direct code (no over-abstraction)
- ✅ Fast startup (< 2 seconds)

### Before Adding Dependencies
Ask yourself:
1. Is this absolutely necessary?
2. Can we implement it ourselves in < 50 lines?
3. Is the dependency well-maintained?
4. Does it add significant value?

**If in doubt, discuss in an issue first!**

### File Organization
```
bridge-gad-generator/
├── app_lean.py              # Main Streamlit app
├── requirements_lean.txt    # Minimal dependencies
├── src/bridge_gad/          # Core logic (if needed)
│   ├── bridge_generator.py  # DXF generation
│   ├── geometry.py          # Calculations
│   └── templates.py         # Bridge templates
└── tests/                   # Tests (optional)
```

---

## 🎓 Learning Resources

### New to Contributing?
- [First Contributions Guide](https://github.com/firstcontributions/first-contributions)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

### Bridge Engineering
- IRC (Indian Roads Congress) standards
- IS (Indian Standards) codes
- AutoCAD DXF format specification
- ezdxf documentation

### Python/Streamlit
- [Streamlit Documentation](https://docs.streamlit.io)
- [ezdxf Documentation](https://ezdxf.readthedocs.io)
- [pandas Documentation](https://pandas.pydata.org/docs/)

---

## 🌟 Recognition

Contributors will be:
- Listed in README acknowledgments
- Mentioned in release notes
- Credited in commit history
- Appreciated forever! ❤️

---

## 📞 Questions?

- 💬 [Open a Discussion](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/discussions)
- 🐛 [Report an Issue](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/issues)
- 🔒 Private / support: Use a private issue or repository discussion — personal contact details are kept out of source files in this public repository.

---

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

**TL;DR:** Be respectful, inclusive, and professional. We're all here to build something useful together.

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**Thank you for making bridge engineering better for everyone!** 🌉

Every contribution, no matter how small, makes a difference. We appreciate your time and effort!

---

<div align="center">

**Ready to contribute?**

[Fork the Repo](https://github.com/YOUR_USERNAME/bridge-gad-generator/fork) • [Open an Issue](https://github.com/YOUR_USERNAME/bridge-gad-generator/issues) • [Start a Discussion](https://github.com/YOUR_USERNAME/bridge-gad-generator/discussions)

</div>
