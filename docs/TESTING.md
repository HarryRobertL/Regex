# Testing this PoC

No Connect credentials are required for mapping tests. Live AML/Verify calls are optional.

## 1. Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requires Python 3.11+.

## 2. One-shot demo

```powershell
python scripts/run_demos.py
```

`--skip-tests` if you only want the JSON mapping runs.

Exit code `0` and `"ok": true` in the summary means the mapped demos ran cleanly.

## 3. Unit tests

```powershell
pytest tests/ -q
```

Coverage includes:

- Payment Assist 3-step regex (`tests/test_uk_address_normalization.py`)
- Legacy comma / trailing-flat preprocess (`tests/test_legacy_mapper.py`)
- Matt concat examples
- AML identitysearch body shape
- Verify body shape
- Loqate → CS mapping and the three `abodeNo` modes

## 4. Concat Address1 (fallback)

Print identitysearch JSON for Matt’s two examples:

```powershell
python scripts/show_mapping.py --matt --full-request --target identitysearch
```

Single address:

```powershell
python scripts/show_mapping.py `
  --address1 "138 Belsize Road, flat 2" `
  --town LONDON --postcode "NW3 4BA" `
  --full-request --target identitysearch
```

Verify instead of AML:

```powershell
python scripts/show_mapping.py --matt --full-request --target verify
python scripts/run_verify_sample.py --address1 "56, Westcroft Close" --town LONDON --postcode "SW1A 1AA"
```

Person fields (`firstName`, `lastName`, `dateOfBirth`, `reasonForSearch`) stay empty unless you pass `--forename`, `--surname`, `--date-of-birth`, `--reason-for-search`.

## 5. Loqate (preferred when you have a capture)

Matt’s Shanklin Towers example is in `fixtures/loqate_shanklin.json`.

```powershell
python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode empty
python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode number
python scripts/map_loqate.py --from-json fixtures/loqate_shanklin.json --abode-mode mirror --full-request
```

| `--abode-mode` | `abodeNo` | `subBuilding` |
|----------------|-----------|-----------------|
| `empty` (default) | `""` | `Flat 8` |
| `number` | `8` | `Flat 8` |
| `mirror` | `Flat 8` | `Flat 8` |

`subBuilding` is always Loqate `SubBuilding` as-is. Which `abodeNo` Creditsafe/AML actually wants should be confirmed by ops submitting a live search.

Drop in your own Loqate object (or `{ "Items": [ ... ] }`) and point `--from-json` at it. Include `PostalCode` if you have it — CS `postCode` is required for a real search.

## 6. Batch CSV (concat fallback)

`fixtures/sample_addresses.csv` is a starter file.

```powershell
python scripts/score_addresses.py fixtures/sample_addresses.csv --output-dir out
```

Writes:

- `out/summary.json` — counts and `high_medium_pct`
- `out/mapped.jsonl` — one JSON object per row

Your extract should use columns `Address1`, `Address2`, `Town`, `County`, `PostCode`.

Confidence on concat rows is a **parser** score, not a bureau match score. Town-on-the-end and multi-word streets can look `high` and still be wrong — spot-check `mapped.jsonl`.

## 7. Live sandbox (optional)

```powershell
$env:CONNECT_BASE_URL = "https://connect.sandbox.creditsafe.com"
$env:USERNAME = "..."
$env:PASSWORD = "..."

python scripts/run_aml_sample.py --json --live `
  --forename Jane --surname Example --date-of-birth 1985-04-12 `
  --address1 "138 Belsize Road, flat 2" --town LONDON --postcode "NW3 4BA"
```

Use sandbox only, and only consented/synthetic people.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/run_demos.py` | Tests + Matt + Loqate + sample CSV |
| `scripts/show_mapping.py` | Concat Address1 → Verify or identitysearch JSON |
| `scripts/map_loqate.py` | Loqate JSON → identitysearch `current` |
| `scripts/score_addresses.py` | Batch concat CSV |
| `scripts/run_aml_sample.py` | AML identitysearch dry-run / live |
| `scripts/run_verify_sample.py` | Verify directReport dry-run / live |

## Fixtures

| File | Contents |
|------|----------|
| `fixtures/matt_examples.json` | Two concat examples from Matt |
| `fixtures/loqate_shanklin.json` | Loqate Shanklin Towers / Flat 8 |
| `fixtures/sample_addresses.csv` | Small concat CSV to score |
| `fixtures/customer_demo_addresses.json` | Broader concat shapes (includes known weak cases) |
| `fixtures/pa_regression_cases.json` | Regex regression cases |
