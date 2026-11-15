# Data dictionary

Processed exports only. Physical window: 1-9 November 2026 (IST).

## simulation/primary_grid.csv

66 rows from manuscript Table 10.

| Column | Meaning |
|--------|---------|
| condition_id | Cell id |
| gain_g, stress_s, timestep_s | Factor levels |
| n_pairs | 4,000 matched A-D scenarios |
| n_plus | Only-D-fails count (favors A) |
| n_minus | Only-A-fails count (favors D) |
| delta_pp | (n_plus - n_minus) / n_pairs * 100 |
| ci_low_pp, ci_high_pp | Simultaneous interval (pp), primary-grid family alpha=0.02 |
| certificate_label | A / D / unresolved |
| missions_executed | 8,000 (= 2 bundles x 4,000 pairs) |

Joint shared-success/failure counts are **not** published: they are not
identified by discordances alone.

## simulation/confirmation.csv

Eight settings, 8,000 pairs each. Intervals use the confirmation family
(manuscript family-error allocation 0.01). Missions = 2 x n_pairs.

## simulation/model_forms.csv

Manuscript Table 11. Forms base, clearance, fractional, nonlinear, triangular
at g in {1.200, 1.250, 1.300}. Base rows repeat primary-grid discordance counts
(`is_base_repeat=1`, additional missions 0). Non-base: n_pairs=4000,
missions_executed_additional=8000.

**CI note:** Base-repeat interval endpoints can differ from the matching
primary-grid row because the model-form family uses a different simultaneous
multiplicity (family alpha=0.01) than the primary grid (alpha=0.02). Discordance
counts match; interval endpoints need not.

## simulation/attribution.csv

Approximate variance-share decomposition of primary-grid risk-difference
response across factors/interactions (gain main effect ~0.7313). Descriptive
summary of the processed grid; not a substitute for the original analysis code.

## simulation/cartpole_summary.csv

**Metadata only** (episode count / note). Not a CartPole trial dataset.

## physical/wp1/emergency_stop_trips.csv

| Field | Notes |
|-------|-------|
| cohort | `initial_gate` (first 10) or `extended_log` |
| motor_cut_confirmed | 0/1; ES_12 = 0 |
| cut_latency_ms | Present only on successful cutoffs; mean ~14.2 ms over those rows |

Report: 10/10 initial; 23/24 confirmed overall; mean latency on successful trips.

## physical/wp2/steering_calibration.csv

Gain = pooled OLS slope of protractor_angle_deg on (servo_command - 75).
Manuscript gain 1.238.

## physical/wp2/latency_events.csv

200 events; missed_33ms / missed_50ms flags.

## physical/wp3/dock_camera_accuracy.csv

Frame errors vs survey. Position p95 = 2.480 mm (pass 2.5 mm).
Heading p95 = **1.286°** (three-decimal sample quantile; fails 1.0° gate).
Do not report as 1.28° unless a different quantile definition is frozen.

## physical/wp4/clock_compass_pairs.csv

Physical controllers. `heading_shift_deg` = recorded heading-shift magnitude
(degrees) for that run. Descriptive by cohort; not a causal mismatch ATE.

Canonical cohort means in this CSV:
- Dial-pilot mismatch (22): Clock 6.80°, Compass 1.10°
- Linkage mismatch (18): Clock 6.42°, Compass 0.48° (abstract)
- Linkage matched (10): Clock 6.64°, Compass 0.65°

## physical/wp5_wp6/

`study_id=WP5_docking` summaries; `independent_audit.csv` (10 units, 8 agreements,
1 unsupported winner).

## physical/wp7/linkage_ABA.csv

A-B-A' reversible linkage intervention.

| Column | Meaning |
|--------|---------|
| phase | A_baseline, B_modified, or A_prime_restore |
| rep | Replicate index within phase |
| measured_gain_response | Steering response metric in that phase |
| servo_current_A | Mean servo current (A) |
| clock_heading_shift_deg / compass_heading_shift_deg | Heading-shift magnitudes collected during WP7 runs; **not** the same sample as WP4 `heading_shift_deg` |
| as5600_delta_deg | Encoder delta during the measurement |

B vs A: about +2.5% gain response and +28% current. A' is not an exact numerical
return to A.

## physical/wp8/colour_sorter.csv

Batch-level counts by recipe (S1/S2/S3) and condition.

## physical/d1/

| File | study_id | Content |
|------|----------|---------|
| shared_failure_60pair.csv | D1_detailed_60pair | 60 pairs |
| extended_shared_failure_pairs.csv | D1_extended_shared_failure | **204 processed pair rows** (160 both-fail) |
| extended_shared_summary.csv | summary | 160/204 |

Processed extended pairs are included. Original sealed media are not.
Do not pool with the 60-pair study without an overlap map.

## decision_cost/

Decision-cost performance tables intentionally **not included**. See `decision_cost/BENCHMARK_STATUS.md`.
