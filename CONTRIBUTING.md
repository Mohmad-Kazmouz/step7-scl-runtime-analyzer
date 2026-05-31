# Contributing to step7-scl-runtime-analyzer

Thank you for your interest in contributing! 🎉  
Every contribution — whether a bug fix, new CPU profile, or documentation improvement — is valued.

## How to Contribute

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR-USERNAME/step7-scl-runtime-analyzer.git
cd step7-scl-runtime-analyzer
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
pip install -e .
```

After changing `grammar/SCL.g4`, regenerate the parser:

```bash
python scripts/generate_parser.py
```

Commit the updated files under `src/parser/generated/`.

### 2. Create a Branch

Use a descriptive branch name:

```bash
git checkout -b feature/add-cpu-318-profile
git checkout -b fix/loop-bound-detection
git checkout -b docs/improve-troubleshooting
```

### 3. Make Your Changes

- Follow **PEP 8** code style
- Add or update **docstrings** for all public functions
- Add **unit tests** in `tests/unit/` for new functionality

### 4. Run Tests

```bash
pytest
```

All 52 tests must pass before submitting a Pull Request.

### 5. Commit and Push

Use clear, semantic commit messages:

```bash
git commit -m "feat: add CPU 318-3 PN/DP timing profile"
git commit -m "fix: correct loop back-edge redirection in annotator"
git commit -m "docs: add troubleshooting section to README"
```

### 6. Open a Pull Request

Go to GitHub and open a Pull Request from your branch to `main`.  
Describe **what** you changed and **why**.

---

## Adding a New CPU Profile (No Python needed!)

1. Copy `profiles/s7_300/S7-300-CPU315-2DP.json`
2. Rename it (e.g. `S7-300-CPU318.json`)
3. Update all values from the official [Siemens Instruction List PDF](https://support.industry.siemens.com/)
4. Run `scl-analyzer profiles` to verify it loads correctly
5. Submit a Pull Request

---

## Reporting Bugs

Open an [Issue](https://github.com/Mohmad-Kazmouz/step7-scl-runtime-analyzer/issues) with:
- Python version (`python --version`)
- Operating system
- Full command and error output
- A minimal SCL snippet that reproduces the issue (no proprietary code!)

---

## Code of Conduct

Be respectful and constructive. This is a technical project for engineers — keep discussions focused and professional.
