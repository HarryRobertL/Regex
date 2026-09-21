#!/usr/bin/env python3
"""Print legacy → Connect address mapping as JSON (stdout).

Examples:

  python scripts/show_mapping.py --address1 "138 Belsize Road, flat 2" --town LONDON --postcode "NW3 4BA"
  python scripts/show_mapping.py --matt
  python scripts/show_mapping.py --matt --full-request
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pp_poc.mapping_report import mapping_report, mapping_report_batch


def _load_cases(path: Path) -> List[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"]
    if isinstance(data, dict) and isinstance(data.get("cases"), list):
        return data["cases"]
    raise ValueError(f"Expected a JSON array of address cases in {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show legacy address → Connect mapping as JSON"
    )
    parser.add_argument("--address1", default="")
    parser.add_argument("--address2", default="")
    parser.add_argument("--town", default="")
    parser.add_argument("--county", default="")
    parser.add_argument("--postcode", default="")
    parser.add_argument(
        "--matt",
        action="store_true",
        help="Run Matt's two People's Partnership examples and print JSON",
    )
    parser.add_argument(
        "--from-json",
        type=Path,
        help="JSON file of address cases (array). Prints summary + results.",
    )
    parser.add_argument(
        "--full-request",
        action="store_true",
        help="Include the Connect request body (Verify by default)",
    )
    parser.add_argument(
        "--target",
        choices=("verify", "identitysearch"),
        default="verify",
        help="Which Connect payload to build with --full-request (default: verify)",
    )
    parser.add_argument(
        "--reason-for-search",
        default="",
        help="Verify reasonForSearch code. Leave empty unless you have the agreed code.",
    )
    parser.add_argument("--forename", default="")
    parser.add_argument("--surname", default="")
    parser.add_argument("--date-of-birth", default="")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Single-line JSON (default is pretty-printed)",
    )
    args = parser.parse_args()

    cases_path = args.from_json
    if args.matt:
        cases_path = ROOT / "fixtures" / "matt_examples.json"

    if cases_path:
        if not cases_path.is_file():
            print(f"File not found: {cases_path}", file=sys.stderr)
            return 1
        try:
            cases = _load_cases(cases_path)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"Invalid JSON cases file: {exc}", file=sys.stderr)
            return 1
        payload = mapping_report_batch(
            cases,
            full_request=args.full_request,
            forename=args.forename,
            surname=args.surname,
            date_of_birth=args.date_of_birth,
            target=args.target,
            reason_for_search=args.reason_for_search,
        )
    else:
        if not (args.address1 or "").strip():
            parser.error("Provide --matt, --from-json, or --address1")
        payload = mapping_report(
            address1=args.address1,
            address2=args.address2,
            town=args.town,
            county=args.county,
            postcode=args.postcode,
            full_request=args.full_request,
            forename=args.forename,
            surname=args.surname,
            date_of_birth=args.date_of_birth,
            target=args.target,
            reason_for_search=args.reason_for_search,
        )

    if args.compact:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
