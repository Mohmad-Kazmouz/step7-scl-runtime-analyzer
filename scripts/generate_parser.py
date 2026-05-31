#!/usr/bin/env python3
"""Generate ANTLR lexer/parser/visitor from grammar/SCL.g4 into src/parser/generated/."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAMMAR = ROOT / "grammar" / "SCL.g4"
OUT_DIR = ROOT / "src" / "parser" / "generated"


def main() -> int:
    if not GRAMMAR.exists():
        print(f"Grammar not found: {GRAMMAR}", file=sys.stderr)
        return 1

    staging = OUT_DIR / "_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    env = {**os.environ, "ANTLR4_TOOLS_ANTLR_VERSION": "4.13.1"}
    antlr4 = shutil.which("antlr4")
    if not antlr4:
        scripts_bin = Path(sys.executable).parent / "antlr4"
        antlr4 = str(scripts_bin) if scripts_bin.exists() else None
    if not antlr4:
        print("Install: pip install antlr4-tools", file=sys.stderr)
        return 1
    subprocess.run(
        [
            antlr4,
            "-Dlanguage=Python3",
            "-visitor",
            "-no-listener",
            "-o",
            str(staging),
            str(GRAMMAR),
        ],
        check=True,
        cwd=ROOT,
        env=env,
    )

    src_py = staging / "grammar" if (staging / "grammar").is_dir() else staging
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for old in OUT_DIR.glob("SCL*.py"):
        old.unlink()

    for path in src_py.glob("*.py"):
        shutil.copy2(path, OUT_DIR / path.name)

    shutil.rmtree(staging, ignore_errors=True)
    (OUT_DIR / "__init__.py").write_text('"""ANTLR-generated SCL parser (from grammar/SCL.g4)."""\n')
    print(f"Generated parser in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
