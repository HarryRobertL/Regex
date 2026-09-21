#!/usr/bin/env python3
"""Score a CSV of legacy addresses — mapped JSON + summary stats."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pp_poc.legacy_mapper import map_legacy_address


def _normalise_header(name: str) -> str:
    return name.strip().lower().replace(" ", "")


def _row_get(row: dict, *keys: str) -> str:
    norm = {_normalise_header(k): v for k, v in row.items()}
    for key in keys:
        val = norm.get(_normalise_header(key))
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def score_csv(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    mapped_path = output_dir / "mapped.jsonl"
    summary_path = output_dir / "summary.json"

    confidence_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()
    total = 0
    parseable = 0

    with input_path.open(newline="", encoding="utf-8-sig") as f_in, mapped_path.open(
        "w", encoding="utf-8"
    ) as f_out:
        reader = csv.DictReader(f_in)
        for i, row in enumerate(reader, start=1):
            total += 1
            mapping = map_legacy_address(
                address1=_row_get(row, "address1", "Address1"),
                address2=_row_get(row, "address2", "Address2"),
                town=_row_get(row, "town", "Town"),
                county=_row_get(row, "county", "County"),
                postcode=_row_get(row, "postcode", "PostCode", "postCode"),
            )
            if mapping.parseable:
                parseable += 1
            confidence_counts[mapping.confidence] += 1
            for w in mapping.warnings:
                warning_counts[w] += 1

            record = {
                "row": i,
                "input": dict(row),
                "confidence": mapping.confidence,
                "parseable": mapping.parseable,
                "warnings": mapping.warnings,
                "connectCurrent": mapping.mapped.to_connect_dict(),
                "verifyCurrent": mapping.mapped.to_verify_dict(),
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "total": total,
        "parseable": parseable,
        "parseable_pct": round(100.0 * parseable / total, 1) if total else 0.0,
        "confidence": dict(confidence_counts),
        "warnings": dict(warning_counts),
        "high_medium_pct": round(
            100.0
            * (confidence_counts.get("high", 0) + confidence_counts.get("medium", 0))
            / total,
            1,
        )
        if total
        else 0.0,
        "mapped_jsonl": str(mapped_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Score legacy address CSV mapping")
    parser.add_argument("input_csv", type=Path, help="CSV with Address1, Address2, Town, etc.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "out",
        help="Output directory (default: ./out)",
    )
    args = parser.parse_args()
    if not args.input_csv.is_file():
        print(f"Input not found: {args.input_csv}", file=sys.stderr)
        return 1
    summary = score_csv(args.input_csv, args.output_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
