# Scope and file map

The attached prompts supply project requirements; they are not recovered source.
This implementation favors shared modules over repeated experiment folders.

| Location | Purpose |
|---|---|
| `CONTRACTS/CSV_SCHEMAS.json` | Exact ordered columns, archived row counts and first IDs |
| `CONTRACTS/EXPECTED_RESULTS.json` | Archived numerical checks |
| `REFERENCE_DATA/starlight-iris-2026/physical/` | WP1, WP2 calibration/latency, WP3, WP4, WP5/WP6, WP7, WP8 and separate D1 ledgers |
| `REFERENCE_DATA/starlight-iris-2026/simulation/` | Grid, confirmation, model forms, attribution and CartPole metadata |
| `REFERENCE_DATA/starlight-iris-2026/evidence/` | Missing-asset index and release hashes |
| `starlight/schema.py` | All 18 CSV contracts, types, categories, units and consistency checks |
| `starlight/analysis.py`, `statistics.py` | Experiment summaries, exact intervals and golden comparisons |
| `starlight/reports.py` | JSON, Markdown, SVG figures, manifests and reference protection |
| `starlight/acquisition.py`, `controllers.py`, `vision.py` | New-run lineage, mocks, controller plans and optional calibrated image analysis |
| `starlight/decision.py` | Explicit five-action policy; no cost benchmark |
| `starlight/cli.py` | Shared replay/validate/acquire commands |
| `tests/` | Offline regression and safety tests |
| `REPORTS/`, `outputs/` | New reports only |

Replay all 18 CSVs without changing bytes. Export exact headers without an index.
Archive checks enforce historical counts; fresh rows use the same schema without
requiring historical sizes or values. Timestamps in the archive are naive IST;
new events use aware current timestamps and monotonic ordering.

Report units, denominators, missing values, uncertainty and methods separately
from CSV columns. Validate every expected-result leaf. Audit intervals separately
from archived endpoints. Distinguish 376,000 matched scenarios from 752,000 missions.
Keep D1 studies separate and old cross-study overlap unknown.

Acquisition defaults to mocks. Live drivers remain unimplemented until physical
commissioning; even armed requests fail closed. New event logging supports real
operator-entered observations without generating historical observations. No
code energizes motors on import, installation, replay or test discovery.

The simulator, sealed media, original policies and excluded cost benchmark are
unavailable. No surrogate data or benchmark claims are included.
