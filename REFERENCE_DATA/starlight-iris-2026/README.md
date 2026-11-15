# Starlight / IRIS research data package (2026)

**Processed research support tables** for the Starlight engineering manuscript
(Team Sentio). Physical session window: 1-9 November 2026.

This archive is **not** an independent regeneration of the full simulator and
**not** a release of sealed instrument binaries or videos. Internal arithmetic
of the included CSVs has been checked; treat all files as processed exports.

## Mission-count reconciliation (robot study)

| Component | Executions |
|-----------|----------:|
| Primary 66-cell A-D grid (4,000 pairs/cell) | 528,000 |
| Eight independent confirmation settings | 128,000 |
| Twelve additional model-form conditions | 96,000 |
| **Total** | **752,000** |

CartPole metadata (`simulation/cartpole_summary.csv`) is excluded from this total.

## Simulation semantics

- **A and D** = simulated design bundles.
- **Clock and Compass** = physical docking controllers (WP4 / D1 only).
- Primary grid factors: gain g in {1.20,...,1.30}, stress s in {0.015,0.030,0.050},
  timestep dt in {0.010,0.040} s.
- Confirmation witnesses (s=0.030, dt=0.040): g=1.200 (+1.050 pp); g=1.260 (-2.925 pp).

## WP1 safety (report carefully)

- Initial gate: **10/10** passed.
- Overall logged trips: **23/24** confirmed motor cutoffs (`ES_12` failed).
- Mean cutoff latency **~14.2 ms** among the **23 successful timed cutoffs** only.

## WP4 heading (CSV-authoritative pilot means)

| Cohort | n / controller | Clock mean | Compass mean |
|--------|----------------|------------|--------------|
| Dial-pilot mismatch | 22 | 6.80° | 1.10° |
| Linkage mismatch | 18 | 6.42° | 0.48° |
| Linkage matched | 10 | 6.64° | 0.65° |

Linkage mismatch matches the abstract (6.42° / 0.48°). Dial-pilot means above
are the CSV values; align poster labels to the CSV if this file is canonical.

## Verify

Install Python dependencies:

```bash
pip install numpy pandas
```

```bash
python scripts/verify_all_results.py
```

Exit text reports **supported internal checks** only — not provenance of raw data.

## Decision-cost benchmark — not included

The benchmark's nominal comparator names do not agree with some recorded
selection actions, and its actual policy rules were not provided. Therefore,
**this public release excludes the decision-cost case-level and aggregate tables**.
The 14.3–33.0% manuscript claim is not independently established by this release.
See `decision_cost/BENCHMARK_STATUS.md` for details. No simulation or physical
measurements have been modified.
