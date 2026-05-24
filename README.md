# ⏱️ step7-scl-runtime-analyzer

> **Static Worst-Case Execution Time (WCET) analyzer for Siemens S7-300 SCL function blocks.**  
> No PLC connection required — pure static analysis directly from your `.scl` source file.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-31%20passed-brightgreen)](#testing)
[![Platform](https://img.shields.io/badge/Platform-Siemens%20S7--300-orange)](https://new.siemens.com/)

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Supported CPUs](#supported-cpus)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Analysis](#basic-analysis)
  - [Usage with Different CPUs](#usage-with-different-cpus)
  - [Export Options](#export-options)
  - [All CLI Options](#all-cli-options)
- [Understanding the Output](#understanding-the-output)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)

---

## About the Project

**step7-scl-runtime-analyzer** is a command-line tool for PLC engineers and automation software developers working with **Siemens S7-300** hardware programmed in **SCL (Structured Control Language)**.

Unlike runtime profiling — which requires an active PLC connection, a running program, and STEP 7 / SIMATIC Manager access — this tool performs **100% static analysis** directly on the exported `.scl` source file.

It uses an **ANTLR-based SCL parser**, a **Control Flow Graph (CFG)**, and **dominator-based loop resolution** to calculate:

- ✅ **WCET** (Worst-Case Execution Time) — the maximum time the FB can ever take
- ✅ **BCET** (Best-Case Execution Time) — the minimum time
- ✅ **Hotspots** — the most time-consuming code blocks with optimization hints
- ✅ **Pass/Fail** verdict against your configured PLC cycle time

CPU-specific timing profiles are derived from the **official Siemens S7-300 Instruction List** document, ensuring results reflect real hardware behavior.

---

## Features

| Feature | Description |
|---|---|
| 🔍 **Static Analysis** | No PLC or STEP 7 installation needed |
| 📐 **WCET / BCET** | Worst-case and best-case execution time |
| 🔁 **Loop Support** | FOR, WHILE, REPEAT loops with static bound resolution |
| 🧠 **Hotspot Detection** | Top time-consuming blocks with optimization hints |
| 🏭 **Multi-CPU Support** | CPU 314, 315-2 DP, 317F-3 PN/DP (extensible) |
| 📊 **Multiple Export Formats** | JSON, HTML, CSV, plain text |
| ⏱️ **Pass/Fail Verdict** | Validates against configured PLC cycle time |
| 🧪 **Fully Tested** | 31 unit and integration tests |

---

## Technology Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **SCL Parser** | ANTLR 4.13 (custom SCL grammar) |
| **Graph Analysis** | NetworkX 3.3 (CFG, longest path, dominators) |
| **CLI Interface** | Click 8.1 |
| **Terminal Output** | Rich 13.7 (tables, panels, colors) |
| **Data Validation** | Pydantic 2.7 (CPU profile schema) |
| **Report Templates** | Jinja2 3.1 (HTML export) |
| **Testing** | pytest 8.2 + pytest-cov |

---

## Supported CPUs

The following Siemens S7-300 CPU profiles are included, with instruction timings taken directly from the **Siemens S7-300 Instruction List** (Siemens document A5E00261439):

| Profile Name | CPU Model | Clock | Order Number |
|---|---|---|---|
| `S7-300-CPU314` | CPU 314 | 60 MHz | 6ES7 314-1AG14-0AB0 |
| `S7-300-CPU315-2DP` | CPU 315-2 DP | 80 MHz | 6ES7 315-2AH14-0AB0 |
| `S7-300-CPU317F-3` | CPU 317F-3 PN/DP | 120 MHz | 6ES7 317-2FK14-0AB0 |

### Key Instruction Timings per CPU

| Instruction | CPU 314 (60 MHz) | CPU 315-2 DP (80 MHz) | CPU 317F-3 (120 MHz) |
|---|---|---|---|
| LOAD (DB) | 160 ns | 120 ns | 40 ns |
| STORE (DB) | 140 ns | 110 ns | 40 ns |
| ADD / SUB | 120 ns | 90 ns | 30 ns |
| MUL | 150 ns | 120 ns | 40 ns |
| DIV | 270 ns | 210 ns | 80 ns |
| MOD | 230 ns | 180 ns | 70 ns |
| SQRT | 4220 ns | 3240 ns | 1260 ns |
| SIN | 3900 ns | 3000 ns | 1200 ns |
| COS | 4750 ns | 3650 ns | 1500 ns |
| CALL (FC/FB) | 2600 ns | 2000 ns | 780 ns |

> **Adding a new CPU:** Simply create a new `.json` file in `profiles/s7_300/` following the same structure as the existing profiles. No code changes required.

---

## Installation

### Prerequisites

- **Python 3.10 or higher** — [Download here](https://www.python.org/downloads/)
- **pip** (included with Python)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Mohmad-Kazmouz/step7-scl-runtime-analyzer.git
cd step7-scl-runtime-analyzer

# 2. Create a virtual environment (recommended)
python -m venv .venv

# 3. Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install the package in development mode
pip install -e .
```

After installation, the `scl-analyzer` command is available in your terminal.

---

## Usage

### Basic Analysis

```bash
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms
```

**Example output:**
```
SCL Runtime Analyzer v1.0.0  |  Zielplattform: Siemens S7-300
--------------------------------------------------------------
[OK] CPU-Profil geladen: CPUProfile(S7-300-CPU315-2DP, 80.0MHz)
[OK] Parsing abgeschlossen: FB 'FB4200'
[OK] CFG erstellt: 218 Bloecke (Schleifen aufgeloest)

+-------------------+----------+
| Kennzahl          |     Wert |
+-------------------+----------+
| WCET (Worst Case) | 0.245 ms |
| BCET (Best Case)  | 0.000 ms |
| Zykluszeit        |  10.0 ms |
| Sicherheitspuffer |    97.5% |
| Bewertung         |     PASS |
+-------------------+----------+

                        Top Hotspots
+---+-----------+----------+--------+--------------------------+
| # | Zeilen    |   Latenz | Anteil | Hinweis                  |
+---+-----------+----------+--------+--------------------------+
| 1 | 1205-1373 | 0.078 ms |    32% | Intensiver DB-Zugriff... |
+---+-----------+----------+--------+--------------------------+
```

---

### Usage with Different CPUs

#### CPU 314 (60 MHz) — Slower, older hardware

```bash
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU314 --cycle-time 20ms
```

Use this profile for older CPU 314 installations where execution times are significantly higher.

#### CPU 315-2 DP (80 MHz) — Standard mid-range CPU

```bash
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms
```

The most common S7-300 CPU in the field. Suitable for the majority of applications.

#### CPU 317F-3 PN/DP (120 MHz) — High-performance fail-safe CPU

```bash
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU317F-3 --cycle-time 5ms
```

Use this profile for high-speed applications using the CPU 317F-3 PN/DP with Firmware V3.2. This CPU runs at 120 MHz and is significantly faster than the 315 series.

#### Comparing results across CPUs

```bash
# Run analysis on all three profiles and export to CSV
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU314       --cycle-time 10ms --export csv --output result_314.csv
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP   --cycle-time 10ms --export csv --output result_315.csv
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU317F-3    --cycle-time 10ms --export csv --output result_317.csv
```

#### Loops with many iterations (WHILE / REPEAT)

By default, WHILE and REPEAT loops without static bounds are assumed to execute a **maximum of 100 iterations**. You can change this:

```bash
# Set max iterations to 500 for conservative safety analysis
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms --max-iter 500
```

---

### Export Options

Export results to different formats for reporting or integration:

```bash
# HTML report (for documentation / sharing)
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms --export html --output report.html

# JSON (for integration with other tools)
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms --export json --output report.json

# CSV (for Excel / spreadsheet analysis)
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms --export csv --output report.csv

# Plain text
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms --export text --output report.txt
```

---

### All CLI Options

The CLI provides two main commands: `analyze` for running the static analysis, and `profiles` for displaying available CPU models.

```bash
scl-analyzer [COMMAND] [OPTIONS]
```

---

#### 1. `scl-analyzer profiles`
Lists all available S7-300 CPU profiles loaded into the database, displaying their name, clock rate, and hardware order number.

**Example:**
```bash
scl-analyzer profiles
```

---

#### 2. `scl-analyzer analyze SCL_FILE [OPTIONS]`
Performs the core static analysis on the specified `.scl` file.

##### **Arguments:**
*   `SCL_FILE` (Required): The path to the SCL file containing the function block (FB) to analyze.

##### **Options:**
*   `--cpu TEXT` (Required)
    *   **Description:** The target CPU profile to run the analysis against.
    *   **Examples:** `S7-300-CPU314`, `S7-300-CPU315-2DP`, `S7-300-CPU317F-3`.
    *   **Use Case:** Switch between different PLC hardware profiles to see if the block can run within budget on a slower CPU or requires upgrading to a faster CPU.
*   `--cycle-time TEXT` (Required)
    *   **Description:** The target cycle time/interval. If the calculated WCET exceeds this value, the tool returns a `FAIL` verdict (and exits with status code `1` for CI/CD integrations). Supports units `ms` (milliseconds) and `s` (seconds). If no unit is provided, milliseconds is assumed.
    *   **Examples:** `10ms`, `500ms`, `0.5s`, `20` (interpreted as `20ms`).
    *   **Use Case:** Setting the cycle boundary to guarantee that the execution time of the block is always within the target cycle time of the task (e.g. 10ms task cycle).
*   `--export TEXT` (Optional)
    *   **Description:** Export format for the analysis report.
    *   **Allowed Values:** `json`, `html`, `csv`, `text`.
    *   **Use Case:** Generate professional HTML reports for sharing, CSV files for Excel spreadsheet analysis, or JSON for integration into build pipelines.
*   `--output PATH` (Optional)
    *   **Description:** Destination path for the exported report. If omitted, the report is saved in the current directory as `report_<scl_filename>.<format>`.
    *   **Use Case:** Standardize report storage locations during automated builds.
*   `--max-iter INTEGER` (Optional)
    *   **Description:** Set the maximum number of loop iterations for dynamically bounded loops (`WHILE` and `REPEAT`). Default value is `100`.
    *   **Use Case:** Adjust the loop limit depending on the design parameters of your algorithm to get accurate WCET estimations.

---

### Detailed Guide: How `--max-iter` works

Since static analysis operates without running the code, it faces the **halting problem** and cannot automatically determine how many times loops will execute if their bounds depend on runtime data. 

To solve this, the analyzer classifies loops into two categories:

#### A. Statically Bounded Loops (Resolved Automatically)
Loops with constant/static boundaries (typically `FOR` loops) are automatically parsed and resolved by the tool. Their bounds are extracted directly from the SCL syntax and do not use `--max-iter`.
*   **Example:**
    ```scl
    FOR i := 1 TO 10 DO
        temp_sum := temp_sum + data[i];
    END_FOR;
    ```
    *   *Bound Resolution:* The parser knows this will iterate **exactly 10 times**. It ignores `--max-iter` and calculates execution time based on exactly 10 iterations.

#### B. Dynamically Bounded Loops (Uses `--max-iter`)
Loops whose exit conditions depend on dynamically changing values or sensor inputs (such as `WHILE` or `REPEAT` loops) cannot be resolved statically.
*   **Example:**
    ```scl
    WHILE sensor_active DO
        process_data();  // Latency: 0.001 ms per iteration
    END_WHILE;
    ```
    *   *Bound Resolution:* The exit condition is `sensor_active`, which depends on external inputs. The analyzer must make an assumption. It uses the value provided to `--max-iter` as the worst-case number of iterations.

#### Mathematical Impact of `--max-iter` on WCET:
Assuming the loop body has a latency of `0.001 ms` per iteration:

| `--max-iter` Value | Execution Time Calculation | WCET Contribution |
| :--- | :--- | :--- |
| `--max-iter 10` | 0.001 ms × 10 | **0.01 ms** |
| `--max-iter 100` *(Default)* | 0.001 ms × 100 | **0.10 ms** |
| `--max-iter 500` | 0.001 ms × 500 | **0.50 ms** |

#### Practical Rule of Thumb:
*   **Default (100):** Suitable for most general-purpose blocks with typical logic.
*   **Adjust Lower:** If you have an algorithm (e.g., binary search or a small filter) where you mathematically know the loop cannot run more than 10 or 20 times.
*   **Adjust Higher:** If you process large data arrays or do communication buffering where a loop might run up to 500 or 1000 times. Always choose the **worst-case scenario** that is physically possible in your system.

---

## Understanding the Output

### Result Table

| Field | Description |
|---|---|
| **WCET (Worst Case)** | Maximum possible execution time of the FB |
| **BCET (Best Case)** | Minimum possible execution time of the FB |
| **Zykluszeit** | Your configured PLC cycle time |
| **Sicherheitspuffer** | Remaining time budget as % of cycle time |
| **Bewertung** | `PASS` if WCET ≤ cycle time, otherwise `FAIL` |

### Hotspot Table

| Column | Description |
|---|---|
| **#** | Priority rank (1 = worst hotspot) |
| **Zeilen** | Source code line range of the hotspot block |
| **Latenz** | Absolute execution time of this block |
| **Anteil** | Share of this block in the total WCET (%) |
| **Hinweis** | Specific optimization recommendation |

### Optimization Hints

| Hint | Meaning |
|---|---|
| *Intensiver DB-Zugriff* | High data block read/write — cache values in `VAR_TEMP` |
| *SQRT/SIN/COS sind langsam* | Use lookup tables or precompute values |
| *Division ist teuer* | Replace `/` with multiplication by reciprocal where possible |
| *Viele Multiplikationen* | Use `DINT` instead of `REAL` for up to 3x speedup on S7-300 |

---

## Documentation

Full technical documentation is available in the `docs/` directory:

| File | Content |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System architecture, module overview, and data flow |
| [`profiles/s7_300/`](profiles/s7_300/) | CPU profile JSON files with timing data |
| [`grammar/SCL.g4`](grammar/SCL.g4) | ANTLR grammar definition for Siemens SCL |

### Project Structure

```
step7-scl-runtime-analyzer/
├── src/
│   ├── parser/        # ANTLR Lexer + Parser → AST
│   ├── semantic/      # Symbol table & type analysis
│   ├── ir/            # Intermediate Representation (IR)
│   ├── cfg/           # Control Flow Graph (CFG)
│   ├── wcet/          # WCET engine, loop bounds, hotspot detection
│   ├── profiles/      # CPU profile loader (JSON → Python)
│   ├── reporter/      # Export engine (JSON, HTML, CSV, text)
│   └── cli/           # Command-line interface (Click)
├── profiles/
│   └── s7_300/        # Siemens S7-300 CPU timing profiles
├── tests/
│   ├── unit/          # Unit tests per module
│   └── integration/   # Full pipeline integration tests
├── grammar/           # SCL.g4 ANTLR grammar
├── docs/              # Architecture & technical documentation
├── scripts/           # Batch analysis & profile calibration scripts
├── requirements.txt
└── pyproject.toml
```

---

## Testing

Run the full test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=src --cov-report=term-missing
```

Run only unit tests:

```bash
pytest tests/unit/
```

Run only integration tests:

```bash
pytest tests/integration/
```

**Current test status:** ✅ 31 tests passing

---

## Troubleshooting

### ❌ `UnicodeEncodeError` on Windows

**Problem:** The terminal cannot display special characters (✓, │, etc.).

**Fix:** Set the UTF-8 environment variable before running:
```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms
```

---

### ❌ `FileNotFoundError: CPU profile not found`

**Problem:** The specified `--cpu` name does not match any profile file.

**Fix:** Run `scl-analyzer profiles` to see all available profile names, and use the exact name shown.

---

### ❌ `CFG enthält Zyklen` (CFG contains cycles)

**Problem:** The SCL file contains loops but the loop resolution failed.

**Fix:** Ensure your SCL file uses standard SCL loop syntax (`FOR`, `WHILE`, `REPEAT`). If WHILE/REPEAT loops are unbounded, increase `--max-iter`:
```bash
scl-analyzer analyze MY_FB.scl --cpu S7-300-CPU315-2DP --cycle-time 10ms --max-iter 200
```

---

### ❌ Parse errors in SCL file

**Problem:** The parser cannot read the SCL file — typically due to non-standard Siemens extensions.

**Fix:**
- Ensure the file is exported from **STEP 7 / SIMATIC Manager** (not TIA Portal — TIA Portal uses a different SCL dialect)
- Remove any STEP 7-specific preprocessor directives or region markers
- Encoding issues: ensure the file is saved as **UTF-8** or **ANSI**

---

### ❌ WCET is 0.000 ms

**Problem:** All blocks have zero latency — likely caused by missing or mismatched CPU profile opcodes.

**Fix:** Ensure you are using the correct `--cpu` profile. Run `scl-analyzer profiles` to verify.

---

## Contributing

Contributions are welcome! Whether it's a new CPU profile, a bug fix, or a new feature — all pull requests are appreciated.

### How to Contribute

1. **Fork** the repository on GitHub
2. **Create a new branch** for your feature or fix:
   ```bash
   git checkout -b feature/add-cpu-318-profile
   ```
3. **Make your changes** and add tests where applicable
4. **Run the test suite** to make sure nothing is broken:
   ```bash
   pytest
   ```
5. **Commit** your changes with a clear message:
   ```bash
   git commit -m "feat: add CPU 318-3 PN/DP profile"
   ```
6. **Push** to your fork and open a **Pull Request** on GitHub

### Adding a New CPU Profile

The easiest contribution you can make! No Python knowledge required:

1. Copy an existing profile from `profiles/s7_300/`
2. Rename it to match your CPU (e.g. `S7-300-CPU318.json`)
3. Update the `name`, `description`, `clock_mhz`, and all `latency_ns` values from the official [Siemens S7-300 Instruction List](https://support.industry.siemens.com/)
4. Run `scl-analyzer profiles` to confirm it appears
5. Submit a Pull Request

### Code Style

- Follow **PEP 8** conventions
- All public functions must have **docstrings**
- New features must include **unit tests** in `tests/unit/`
- Keep module responsibilities separated (parser ≠ IR ≠ CFG)

---

## Support

If you encounter a problem or have a question:

1. 📖 **Check the [Troubleshooting](#troubleshooting) section** above first
2. 🔍 **Search existing [GitHub Issues](https://github.com/Mohmad-Kazmouz/step7-scl-runtime-analyzer/issues)**
3. 🐛 **Open a new Issue** with:
   - Your operating system and Python version (`python --version`)
   - The exact command you ran
   - The full error message / output
   - If possible, a minimal `.scl` file that reproduces the issue

> ⚠️ **Do not** share confidential production code or proprietary SCL programs in public issues.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License — Copyright (c) 2025 Mohmad Kazmouz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
```

---

<div align="center">

Made with ❤️ for the Siemens S7-300 PLC engineering community

**[⬆ Back to Top](#️-step7-scl-runtime-analyzer)**

</div>
