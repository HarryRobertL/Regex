#!/usr/bin/env python3
"""Dry-run (or live) a Connect Verify individual/directReport body from a concat address."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pp_poc.aml_request_builder import strip_mapping_meta
from pp_poc.connect_client import ConnectClient, ConnectClientError, credentials_from_env
from pp_poc.legacy_mapper import map_legacy_address
from pp_poc.verify_request_builder import VERIFY_PATH, build_verify_direct_report_request


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Verify directReport JSON")
    parser.add_argument("--forename", default="")
    parser.add_argument("--surname", default="")
    parser.add_argument("--date-of-birth", default="")
    parser.add_argument("--address1", required=True)
    parser.add_argument("--address2", default="")
    parser.add_argument("--town", default="")
    parser.add_argument("--county", default="")
    parser.add_argument("--postcode", default="")
    parser.add_argument("--reason-for-search", default="")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    mapping = map_legacy_address(
        address1=args.address1,
        address2=args.address2,
        town=args.town,
        county=args.county,
        postcode=args.postcode,
    )
    body = build_verify_direct_report_request(
        first_name=args.forename,
        last_name=args.surname,
        date_of_birth=args.date_of_birth,
        legacy_address={
            "address1": args.address1,
            "address2": args.address2,
            "town": args.town,
            "county": args.county,
            "postcode": args.postcode,
        },
        mapping=mapping,
        reason_for_search=args.reason_for_search,
    )
    payload = strip_mapping_meta(body)
    print(json.dumps({"endpoint": VERIFY_PATH, "request": payload}, indent=2, ensure_ascii=False))

    if args.live:
        try:
            username, password = credentials_from_env()
            client = ConnectClient()
            token = client.authenticate(username, password)
            url = f"{client.base_url}{VERIFY_PATH}"
            import requests

            response = requests.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                timeout=client.timeout,
            )
            print(json.dumps({"status": response.status_code, "body": response.json() if response.content else {}}, indent=2))
            if response.status_code != 200:
                return 1
        except ConnectClientError as exc:
            print(f"Connect error: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
