# Scientific claims and evidence boundaries

| Topic | What the supplied public files support | What they do not establish |
|---|---|---|
| Simulation scale | 66 primary conditions × 8,000 missions = 528,000; eight confirmations × 16,000 = 128,000; 12 new model-form conditions × 8,000 = 96,000; total **752,000** missions | Simulator source or direct rerun of raw missions; the separate CartPole metadata is excluded |
| Ranking reversal | Independent confirmation `g=1.200` gives **+1.050 percentage points** (A favored) and `g=1.260` gives **−2.925 pp** (D favored) at `s=0.030`, `dt=0.040` | Physical test showing that A and D swapped ranking in hardware |
| Primary certificate | Of 66 grid conditions, **8 A**, **29 D**, **29 unresolved** | Equivalence from unresolved intervals, or uniform superiority of either bundle |
| Decision cost | Manuscript states a historical 14.3–33.0% improvement | Public validation of seven baseline rules, three ablations, or their cost reduction. Disputed benchmark files were withheld, not silently repaired |
| WP1 emergency stop | First 10/10 passed; **23/24** confirmed overall; 14.196 ms mean **only among 23 successful timed cutoffs** | Claim of 24/24 universal success |
| WP2 | Pooled steering command-angle OLS slope ~1.238; latency p95 ~28.16 ms; 3/200 exceeded 33 ms, 0/200 exceeded 50 ms | Full calibration mechanism or original oscilloscope acquisition code |
| WP3 camera measurement | p95 position **2.480 mm** vs 2.5 mm limit (pass); p95 heading **1.286°** vs 1.0° limit (fail) | Claim both camera targets passed |
| WP4 docking heading | Linkage-mismatch cohort means Clock **6.42°**, Compass **0.48°**; dial-pilot mismatch 6.80° / 1.10°; matched linkage 6.64° / 0.65° | A clean mismatch-induced causal increase in Clock's mean; pilots/cohorts differ and matched Clock mean is actually larger |
| WP5–WP6 | Five session aggregates, 60 nominal docking pairs: Clock **41/60**, Compass **53/60** successes; independent audit **8/10** agreement and **one unsupported winner** | Matched individual WP5 outcomes or inferential McNemar p-value from session marginals |
| D1 shared failures | Separate detailed 60-pair ledger, and extended 204 failure-bearing pairs with **160 both-fail** (**78.4%**) | Pooling two studies or assuming their records do not overlap |
| WP7 | Three-phase A–B–A response/current data in processed aggregate | Unqualified long-term hardware causal effect or guaranteed perfect return to baseline |
| WP8 sorter | 34 aggregated batches, pooled **588/673 = 87.37%** correct across S1/S2/S3 | Independent-item confidence limits without batch dependence model |
| Statistical intervals | Most archived intervals reproduce under an explicitly implemented conservative CP/Bonferroni family | Exact match for five archived confirmation intervals or proof of original undocumented tail allocation |

### Important reproducibility caveat

Five of 89 archived simulation interval pairs differ by more than 0.00051 pp from the explicit fresh Clopper–Pearson family calculation (all five are in `simulation/confirmation.csv`). Source numbers remain untouched. The audit is in `reports/INTERVAL_DISCREPANCIES.md`; these intervals should be reconciled against versioned original calculation code before claiming exact interval replication.

This repository makes the data and its limitations inspectable, not a substitute for laboratory notebooks, timestamps, hardware inspection, safety review or the excluded decision-cost benchmark.
