# Experiment and file index

| ID | Question | Canonical processed file(s) | Main endpoint |
|---|---|---|---|
| WP1 | Does independent emergency stop interrupt propulsion? | `physical/wp1/emergency_stop_trips.csv` | 10/10 first gate; 23/24 cumulative |
| WP2A | How do servo command and measured angle relate? | `physical/wp2/steering_calibration.csv` | OLS slope ≈ 1.238 |
| WP2B | How large are response delays? | `physical/wp2/latency_events.csv` | P95 ≈ 28.16 ms; 3/200 > 33 ms |
| WP3 | How good is docking camera measurement? | `physical/wp3/dock_camera_accuracy.csv` | 2.480 mm position p95 pass; 1.286° heading p95 fail |
| WP4 | How do physical controllers respond across heading test cohorts? | `physical/wp4/clock_compass_pairs.csv` | Linkage mismatch Clock 6.42°, Compass 0.48° |
| WP5 | Are physical docking successes reproducible across sessions? | `physical/wp5_wp6/docking_session_summary.csv` | 41/60 Clock, 53/60 Compass |
| WP6 | Does offline decision audit agree with held-out references? | `physical/wp5_wp6/independent_audit.csv` | 8/10 agreement, 1 unsupported winner |
| WP7 | Does a reversible linkage change alter measured response? | `physical/wp7/linkage_ABA.csv` | A, B, A' response and current shifts |
| WP8 | Does decision framework transfer to sorting recipes? | `physical/wp8/colour_sorter.csv` | 588/673 pooled items correct |
| D1 | How many failure-bearing pairs fail for both controllers? | `physical/d1/shared_failure_60pair.csv`, `extended_shared_failure_pairs.csv` | Extended 160/204; separate from 60-pair study |
| SIM-P | Do A and D rankings depend on simulated gain/stress/time step? | `simulation/primary_grid.csv` | 66 cells; 8/29/29 labels |
| SIM-C | Do independent confirmation witnesses have opposite signs? | `simulation/confirmation.csv` | g=1.200 +1.050 pp; g=1.260 −2.925 pp |
| SIM-M | Do other model-form choices affect rankings? | `simulation/model_forms.csv` | 12 extra forms and 3 repeated base rows |
| SIM-A | Which inputs explain variation within processed grid? | `simulation/attribution.csv` | Descriptive steering-gain share 0.7313 |
| CartPole | Supplemental transfer metadata | `simulation/cartpole_summary.csv` | 5,000 episodes *metadata only* |

All file paths are relative to `REFERENCE_DATA/starlight-iris-2026/`.

Every derived figure is built from the CSVs. No raw observations, old simulator inputs or true empirical outcome records have been imputed.
