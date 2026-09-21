# PoC

Maps UK addresses into Creditsafe Connect **AML identitysearch** `addresses.current` (and optionally Verify).

Two mapping paths:

1. **Loqate first** (preferred when a capture exists) — 1:1 field rename.
2. **Concat fallback** — Payment Assist 3-step regex on legacy `Address1` / `Address2` when Loqate is empty.

This is a dry-run PoC. It does **not** prove a bureau match until you POST to sandbox with real credentials.

## Clone and test (5 minutes)

Python **3.11+**.

```powershell
git clone <this-repo-url>
cd <repo-folder>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/run_demos.py
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_demos.py
```

That runs unit tests, Matt’s two concat examples as identitysearch JSON, the Loqate Shanklin Towers example, and a sample CSV score.

## What to run in a demo


| Goal                                  | Command                                                                                                                                          |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Unit tests                            | `pytest tests/ -q`                                                                                                                               |
| Matt’s two concat examples (AML JSON) | `python scripts/show_mapping.py --matt --full-request --target identitysearch`                                                                   |
| One concat address                    | `python scripts/show_mapping.py --address1 "138 Belsize Road, flat 2" --town LONDON --postcode "NW3 4BA" --full-request --target identitysearch` |
| Loqate → CS (`abodeNo` empty)         | `python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode empty`                                                      |
| Loqate, `abodeNo=8`                   | `python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode number`                                                     |
| Loqate, `abodeNo=Flat 8`              | `python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode mirror`                                                     |
| Score your CSV                        | `python scripts/score_addresses.py path\to\addresses.csv --output-dir out`                                                                       |
| Verify payload instead of AML         | `python scripts/show_mapping.py --matt --full-request --target verify`                                                                           |


Full walkthrough: [docs/TESTING.md](docs/TESTING.md). Field map: [docs/MAPPING.md](docs/MAPPING.md).

## Expected concat results


| Address1                   | CS `current`                                                            |
| -------------------------- | ----------------------------------------------------------------------- |
| `138 Belsize Road, flat 2` | `buildingNo=138`, `street=Belsize Road`, `abodeNo`/`subBuilding=flat 2` |
| `56, Westcroft Close`      | `buildingNo=56`, `street=Westcroft Close`                               |




## Expected Loqate result (Shanklin)

`subBuilding=Flat 8`, `buildingName=Shanklin Towers`, `street=Prospect Road`, `city=Shanklin`, `buildingNo` empty. `abodeNo` depends on `--abode-mode` (default empty until ops AML confirms).

## Live sandbox (optional)

Copy `.env.example` values into the shell. Do not commit passwords.

```powershell
$env:CONNECT_BASE_URL = "https://connect.sandbox.creditsafe.com"
$env:USERNAME = "your_sandbox_user"
$env:PASSWORD = "your_sandbox_password"

python scripts/run_aml_sample.py --json --live `
  --forename Jane --surname Example --date-of-birth 1985-04-12 `
  --address1 "138 Belsize Road, flat 2" --town LONDON --postcode "NW3 4BA"
```

CSV columns accepted: `Address1`, `Address2`, `Town`, `County`, `PostCode` (case-insensitive).

## Out of scope

- Previous addresses
- PAF / Royal Mail lookup
- Production retry / rate limiting

