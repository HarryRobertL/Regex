#!/usr/bin/env python3
"""Build and optionally POST an AML identitysearch request from legacy address fields."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pp_poc.aml_request_builder import build_aml_identity_search_request, strip_mapping_meta
from pp_poc.connect_client import ConnectClient, ConnectClientError, credentials_from_env
from pp_poc.legacy_mapper import map_legacy_address


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AML identitysearch sample")
    parser.add_argument("--forename", required=True)
    parser.add_argument("--surname", required=True)
    parser.add_argument("--date-of-birth", required=True, help="yyyy-mm-dd")
    parser.add_argument("--address1", required=True)
    parser.add_argument("--address2", default="")
    parser.add_argument("--town", default="")
    parser.add_argument("--county", default="")
    parser.add_argument("--postcode", default="")
    parser.add_argument(
        "--live",
        action="store_true",
        help="POST to Connect (requires USERNAME/PASSWORD env vars)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print request JSON only (default when --live not set)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a single JSON object (mapping + Connect address + request)",
    )
    args = parser.parse_args()

    mapping = map_legacy_address(
        address1=args.address1,
        address2=args.address2,
        town=args.town,
        county=args.county,
        postcode=args.postcode,
    )
    body = build_aml_identity_search_request(
        forename=args.forename,
        surname=args.surname,
        date_of_birth=args.date_of_birth,
        legacy_address={
            "address1": args.address1,
            "address2": args.address2,
            "town": args.town,
            "county": args.county,
            "postcode": args.postcode,
        },
        mapping=mapping,
    )

    payload = strip_mapping_meta(body)
    current = body["common"]["person"]["addresses"]["current"]

    if args.json:
        out = {
            "input": {
                "forename": args.forename,
                "surname": args.surname,
                "dateOfBirth": args.date_of_birth,
                "address1": args.address1,
                "address2": args.address2 or None,
                "town": args.town or None,
                "county": args.county or None,
                "postcode": args.postcode or None,
            },
            "confidence": body["_mappingMeta"]["confidence"],
            "parseable": body["_mappingMeta"]["parseable"],
            "warnings": body["_mappingMeta"]["warnings"],
            "connectCurrent": current,
            "request": payload,
        }
        if args.live:
            try:
                username, password = credentials_from_env()
                client = ConnectClient()
                token = client.authenticate(username, password)
                response = client.run_aml_identity_search(token, payload)
                out["amlBandText"] = client.extract_aml_band_text(response)
                out["amlResponse"] = response
            except ConnectClientError as exc:
                print(f"Connect error: {exc}", file=sys.stderr)
                return 1
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    print("=== Mapping ===")
    print(json.dumps(body["_mappingMeta"], indent=2))
    print("=== Connect current address ===")
    print(json.dumps(current, indent=2))

    if args.live:
        try:
            username, password = credentials_from_env()
            client = ConnectClient()
            token = client.authenticate(username, password)
            response = client.run_aml_identity_search(token, payload)
            band = client.extract_aml_band_text(response)
            print("=== AML response (bandText) ===")
            print(band or "(no bandText)")
            print("=== Full response ===")
            print(json.dumps(response, indent=2))
        except ConnectClientError as exc:
            print(f"Connect error: {exc}", file=sys.stderr)
            return 1
    else:
        print("=== Request body (dry-run) ===")
        print(json.dumps(payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
