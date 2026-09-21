#!/usr/bin/env python3
"""Map a Loqate capture JSON object onto Connect identitysearch ``current``.

  python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json
  python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode number
  python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode mirror --full-request
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pp_poc.aml_request_builder import build_aml_identity_search_request, strip_mapping_meta
from pp_poc.loqate_mapper import loqate_report, map_loqate_address


def _load(path: Path) -> List[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("Items"), list):
        return list(data["Items"])
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"Expected a Loqate object or array in {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Map Loqate JSON to Connect identitysearch current address"
    )
    parser.add_argument("--from-json", type=Path, required=True)
    parser.add_argument(
        "--abode-mode",
        choices=("empty", "mirror", "number"),
        default="empty",
        help="How to fill abodeNo (default: empty until ops AML confirms)",
    )
    parser.add_argument(
        "--full-request",
        action="store_true",
        help="Wrap in an identitysearch request (name/DOB left empty unless passed)",
    )
    parser.add_argument("--forename", default="")
    parser.add_argument("--surname", default="")
    parser.add_argument("--date-of-birth", default="")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    if not args.from_json.is_file():
        print(f"File not found: {args.from_json}", file=sys.stderr)
        return 1

    try:
        items = _load(args.from_json)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid Loqate JSON: {exc}", file=sys.stderr)
        return 1

    results = []
    for i, item in enumerate(items, start=1):
        report = loqate_report(
            item,
            abode_mode=args.abode_mode,
            case_id=item.get("id") or f"loqate_{i}",
        )
        if args.full_request:
            mapping = map_loqate_address(item, abode_mode=args.abode_mode)
            body = build_aml_identity_search_request(
                forename=args.forename,
                surname=args.surname,
                date_of_birth=args.date_of_birth,
                legacy_address={
                    "address1": "",
                    "town": mapping.mapped.city or "",
                    "postcode": mapping.mapped.post_code or "",
                },
                mapping=mapping,
            )
            current = strip_mapping_meta(body)["common"]["person"]["addresses"]["current"]
            current["abodeNo"] = mapping.mapped.abode_no or ""
            current["subBuilding"] = mapping.mapped.sub_building or ""
            payload = strip_mapping_meta(body)
            payload["common"]["person"]["addresses"]["current"] = current
            report["endpoint"] = "/v1/localSolutions/GB/identitysearch"
            report["request"] = payload
        results.append(report)

    out: Any = results[0] if len(results) == 1 else {"results": results}
    if args.compact:
        print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
