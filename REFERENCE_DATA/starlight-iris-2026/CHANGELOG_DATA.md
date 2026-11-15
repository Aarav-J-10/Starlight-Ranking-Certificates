# Data changelog

## 2026-11-14d — public-safe release

- Excluded case-level, aggregated and assumptions files for the unresolved
  decision-cost named-strategy comparison. No source values were rewritten.
- Added explicit benchmark status and updated verification scope.
- All simulation and physical research CSVs are byte-for-byte unchanged.


## 2026-11-14c — final public-release corrections

- Removed `both_succeed` / `both_fail` from public `primary_grid.csv` and
  `confirmation.csv`. Only discordance counts (`n_plus`, `n_minus`) and derived
  `delta_pp` / intervals are published; joint-success splits are not identifiable
  from discordances alone.
- WP4 linkage-mismatch means remain abstract values **Clock 6.42° / Compass 0.48°**.
  Dial-pilot mismatch means in the CSV are **Clock 6.80° / Compass 1.10°**
  (22 runs each); the right-panel figure should use these CSV values if the CSV
  is treated as authoritative.
- WP4 wording: reports **descriptive** recorded heading-shift magnitudes by
  controller and cohort. Compass has smaller recorded mean magnitudes in all
  three plotted conditions; a causal mismatch-minus-matched contrast is **not**
  established by these summaries. Pilot, linkage-mismatch, and linkage-matched
  cohorts stay distinct.
- Documented WP1: 10/10 initial pass; **23/24** confirmed overall (`ES_12` failed
  cutoff); mean cutoff latency ~14.2 ms among **successful** timed trips only.
- Confirmed presence of processed extended D1 pair file
  (`physical/d1/extended_shared_failure_pairs.csv`, 204 rows). Original
  instrument/video records remain outside the public release.
- Restored model-form Table 11; confirmation companions; attribution gain ~0.73.
- Renamed `cartpole.csv` → `cartpole_summary.csv` (metadata-only).
- Validator conclusion renamed to report supported internal checks only.
- Regenerated SHA-256 manifests after these edits.

## 2026-11-14b — Table 11 / confirmation / abstract WP4

- Model forms from manuscript Table 11; confirmation witnesses and companions;
  attribution gain-dominant decomposition; linkage mismatch locked to 6.42/0.48.

## 2026-11-14 — GitHub research package layout

- Organized `simulation/`, `physical/`, `decision_cost/`, docs, evidence, scripts.
