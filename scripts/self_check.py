#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> int:
    run([sys.executable, "scripts/daily_digest.py", "--no-fetch", "--preview", "--skip-telegram", "--skip-email", "--date", "2026-01-01"])
    expected = PROJECT_ROOT / "data" / "digests" / "2026-01-01" / "digest.md"
    if not expected.exists():
        raise SystemExit(f"自检失败：未生成 {expected}")
    print(f"自检通过：已生成 {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
