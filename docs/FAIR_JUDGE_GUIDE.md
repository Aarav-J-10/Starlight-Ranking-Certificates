# IRIS National Fair | Judge quick guide

**Starlight: Predicting Design Ranking Reversals in an Autonomous Car from Measured Steering Gain**  
Robotics and Intelligent Machines · Project ROBO0065 · Research manuscript dated 12 November 2026  
Manuscript authors: Aarav Jalan and Darsh Zaveri; mentor: Sunil Solanki.

## 30-second explanation

A self-driving scale robot can seem better in one test and worse after a small change in steering assumptions. We measured steering and physical docking behavior, then compared two *simulated* seven-feature designs under a fixed family of conditions. Their performance ranking reversed in independent confirmation runs. Our analysis uses paired failure differences and simultaneous intervals to identify when evidence supports A, supports D or remains undecided. The robot demonstrates the engineering context, but these simulations do not certify real-world safety.

## Follow the evidence

| Research component | Source | Show this result | Caveat |
|---|---|---|---|
| Physical autonomous car | `legacy/competition_2026/` | Historical controller files, circuit and robot photographs | Competition program ≠ research simulator |
| WP1 safety | `REFERENCE_DATA/.../physical/wp1/` | 10/10 initial; 23/24 overall; 14.196 ms success-only | One failed cutoff |
| WP2 steering and latency | `physical/wp2/` | slope 1.238; p95 latency 28.16 ms | Physical slope is not simulator g |
| WP3 metrology | `physical/wp3/` | position pass, heading fail | Heading error 1.286° exceeds 1° goal |
| WP4 heading | `physical/wp4/` | mismatch Clock 6.42°, Compass 0.48° | Descriptive cohort means, not causal difference |
| WP5 & WP6 | `physical/wp5_wp6/` | 41/60 vs 53/60 docking successes; audit 8/10 | Missing individual WP5 pair outcomes |
| WP7 linkage | `physical/wp7/` | A–B–A reversible intervention | Do not collapse three phases |
| WP8 sorter | `physical/wp8/` | S2 202/216 correct; S3 198/219; S1 188/238 | Batch-level observation units |
| D1 shared failures | `physical/d1/` | extended 160/204 shared among failure-bearing pairs | Different study from the 60-pair ledger |
| Simulation | `simulation/` | 752,000 missions; 8 A / 29 D / 29 unresolved | Source model and seeds not released |
| Decision policy | `starlight/decision.py` | newly reconstructed *example* five-action rule | Does not validate historical cost benchmark |

The paths above beginning with `physical/` or `simulation/` are relative to `REFERENCE_DATA/starlight-iris-2026/`.

## Answers to predictable questions

**Does 752,000 mean 752,000 physical robot runs?** No. These are recorded simulated mission counts: two designs per paired simulated scenario. Physical tests have much smaller denominators.

**Did the physical Clock controller prove A was better?** No. Physical Clock/Compass and simulated A/D are different comparisons.

**What does 29 unresolved mean?** The reported simultaneous interval includes zero, so neither direction is certified in those specific simulated settings. It is not proof of equality.

**Can you regenerate your 752,000 simulated missions?** Not from this public release: simulator generation source and seeds were not provided. One can verify exported sufficient counts, calculations, figures and code tests.

**Why are cost-reduction files not here?** The strategy-action labels were inconsistent with the nominal baseline names and underlying policies were unavailable. The historical claim remains in the paper, but cannot be independently substantiated from this public release.

**Where is the original robot code?** In `legacy/competition_2026/`. It is a competition-era source snapshot, not the original experiment scripts.

**What failed?** WP1 had one later failed cutoff, WP3 heading precision missed its target, and the ten-unit audit had one unsupported winner. These failures are part of the engineering findings.

**Can a statistic certify a real self-driving car as safe?** Not here. These intervals apply to a finite, defined source-informed simulator family. Physical deployment requires separate safety assurance.

## Demonstration commands

```bash
python -m pip install -e '.[science,dev]'
python TOOLS/check_reference.py
python REFERENCE_DATA/starlight-iris-2026/scripts/verify_all_results.py
python -m pytest -q
python -m starlight replay confirmation --out outputs
```

`outputs/` holds fresh derived reports, not overwritten historical records. There is no active hardware driving in these commands.
