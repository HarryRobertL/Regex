#!/usr/bin/env python3
"""One command for a customer test session: unit tests + mapping demos.

  python scripts/run_demos.py
  python scripts/run_demos.py --skip-tests
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(title: str, argv: list[str]) -> dict:
    print(f"\n=== {title} ===", flush=True)
    completed = subprocess.run(argv, cwd=ROOT)
    return {"title": title, "cmd": argv, "exitCode": completed.returncode}


def main() -> int:
    skip_tests = "--skip-tests" in sys.argv
    py = sys.executable
    steps = []
    if not skip_tests:
        steps.append(
            _run("pytest", [py, "-m", "pytest", "tests/", "-q"])
        )
    steps.append(
        _run(
            "Matt examples identitysearch JSON",
            [
                py,
                str(ROOT / "scripts" / "show_mapping.py"),
                "--matt",
                "--full-request",
                "--target",
                "identitysearch",
            ],
        )
    )
    steps.append(
        _run(
            "Loqate Shanklin Towers (abodeNo empty)",
            [
                py,
                str(ROOT / "scripts" / "map_loqate.py"),
                "--from-json",
                str(ROOT / "fixtures" / "loqate_shanklin.json"),
                "--abode-mode",
                "empty",
            ],
        )
    )
    steps.append(
        _run(
            "Score sample CSV",
            [
                py,
                str(ROOT / "scripts" / "score_addresses.py"),
                str(ROOT / "fixtures" / "sample_addresses.csv"),
                "--output-dir",
                str(ROOT / "out"),
            ],
        )
    )
    failed = [s for s in steps if s["exitCode"] != 0]
    summary = {
        "ok": not failed,
        "failed": [s["title"] for s in failed],
        "steps": [{"title": s["title"], "exitCode": s["exitCode"]} for s in steps],
    }
    print("\n=== Demo summary ===")
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
