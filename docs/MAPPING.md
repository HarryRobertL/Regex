# Field mapping

## Concat Address1 (regex fallback)

Runs **before** the 3-step regex: comma tidy (`56, Westcroft Close`) and trailing-flat peel (`138 Belsize Road, flat 2`).

Then:

1. Peel street suffix from the right (`Belsize Road`)
2. Peel flat / abode from the left (`Flat 2`)
3. Score remainder into building number and building name

| Customer column | Verify `currentAddress` | Identitysearch `addresses.current` |
|-----------------|-------------------------|--------------------------------------|
| `Address1` (+ `Address2`) | parsed | parsed |
| — | `subBuilding` | `abodeNo` and `subBuilding` (same string from the regex) |
| — | `buildingNo` | `buildingNo` |
| — | `buildingName` | `buildingName` |
| — | `street` | `street` (`subStreet` left empty) |
| `Town` | `town` | `city` |
| `PostCode` | `postCode` (required for Verify) | `postCode` |
| `County` | `county` | `district` |

Verify is sent as **component fields**. `addressLine` stays empty so the regex split is what the bureau receives.

## Loqate (preferred)

| Loqate | Identitysearch `current` |
|--------|--------------------------|
| `SubBuilding` | `subBuilding` (as-is, e.g. `Flat 8`) |
| `BuildingNumber` | `buildingNo` |
| `BuildingName` | `buildingName` |
| `Street` | `street` |
| `SecondaryStreet` | `subStreet` |
| `City` | `city` |
| `District` | `district` |
| `PostalCode` / `Postcode` | `postCode` |
| `Block` / `Neighbourhood` | not mapped (leave CS empty) |

`abodeNo` is **not** a Loqate field. Use `--abode-mode`:

- `empty` — leave blank until ops AML shows what Connect populated
- `number` — `Flat 8` → `8`
- `mirror` — copy `SubBuilding`

Empty `BuildingNumber` with a `BuildingName` is valid (named building, no house number).

## Endpoints

```http
POST /v1/authenticate
POST /v1/localSolutions/GB/identitysearch
POST /v1/localSolutions/GB/verify/individual/directReport
```

People’s Partnership CS documentation sample is **identitysearch** (`abodeNo`, `city`, `district`). Use `--target identitysearch` in demos unless you are specifically testing Verify.

## Known concat limits

The regex peels only the last two tokens as the street. Town-on-the-end (`28a Queens Drive Enderby`) and extra street words (`18 Red Kite Drive` → `Kite Drive`) are weak. Prefer Loqate for those. Failures should follow the existing manual / non-pass AML path.
