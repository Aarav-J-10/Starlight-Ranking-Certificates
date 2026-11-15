# Verified results

All 18 CSVs and 75 expected numerical metrics pass. All 27 reference files are unchanged.
Test coverage: 96.9%. Test count and full commands/results are in tests.log and tests.xml.

| Measurement | Replayed result |
|---|---|
| WP1 confirmed cuts | 23/24; initial 10/10; mean 14.19565217 ms over 23 |
| WP2 steering OLS slope | 1.2379998828 |
| WP2 latency | P95 28.160 ms; 3 above 33 ms, 0 above 50 ms |
| WP3 | Position 2.480 mm PASS; heading 1.286 degrees FAIL |
| WP5 / WP6 | 41/60 Clock and 53/60 Compass successes; 8/10 audit agreements |
| WP8 pooled items | 588/673 = 87.3700% |
| D1 | Detailed 18/27 shared failures; extended 160/204; kept separate |
| Simulation | 8 A / 29 D / 29 unresolved primary cells; 376,000 pairs; 752,000 robot missions |

5 of 89 stored simulated intervals differ from the explicit recalculation beyond .00051 pp.
Detailed reports: [replay/all/20261115T062351576842Z-ce7127](replay/all/20261115T062351576842Z-ce7127/INTERVAL_DISCREPANCIES.md).

Live acquisition is uncommissioned. Original software, raw media, simulator generation and the excluded decision-cost benchmark remain unavailable.
