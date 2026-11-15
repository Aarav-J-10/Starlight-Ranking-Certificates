# Statistical rules and known exceptions

1. Paired simulation failure difference in percentage points: `delta_pp = 100*(n_plus - n_minus)/n_pairs`; `n_plus` means D-only failure and `n_minus` means A-only failure. Joint success/fail splits cannot be inferred from discordant counts alone.
2. Classify a **certified strict ranking preference** only using the reported simultaneous interval sign: lower >0 → A preferred; upper <0 → D preferred; else unresolved. Intervals spanning 0 do not prove equivalence or inadequacy.
3. The primary-grid family uses alpha 0.02 over 66 settings, confirmation uses alpha 0.01 over 8 settings, model-form sensitivity uses a distinct family alpha 0.01. Source counts and multiplicity must be explicit.
4. The final centre-panel V4.2 corrected three plotted confirmation interval endpoints relative to older CSV data: g=1.230 [−0.055,+1.153] pp, g=1.255 [−1.099,+0.450] pp, g=1.280 [−4.439,−2.427] pp, while some archived rows still carry earlier endpoints. Also inspect the two non-plotted companion settings. Do not silently overwrite public CSVs. Report original and independently recalculated numbers, inputs, formula, version and discrepancy.
5. WP3 95th percentile: linear interpolation between sorted sample ranks; reported heading P95 1.286° is **not** a confidence interval; position 2.480 mm passes 2.5 mm while heading fails 1.0°.
6. WP4 `heading_shift_deg` = *recorded magnitude*, descriptive cohorts; comparison alone is not a causal mismatch effect. WP7 heading-shift metrics are from another sample, do not combine.
7. WP7 A → B → A′: restoration is of hardware configuration, not exact numerical return. Compare phase mean response and current to A; do not call the measured response increase the hardware linkage modification percentage.
8. WP8 batch summaries report pooled item accuracies. Batches and items are not automatically independent units.
9. D1: extended 204 rows are all failure-bearing, so 160/204 = 78.43%. Small 60-pair set has 27 failure-bearing pairs, with 18 shared failures. Do not pool without established mapping.
10. WP5 summary has five sessions and 12 pairs per session, but no underlying 60 individual docking records in the public CSV. Never fabricate per-trial records.
11. Decision-cost benchmark tables are **excluded** from the public reference due to policy/label conflicts. Implement a five-action logic API with explicit thresholds only; do not claim a reproduced cost reduction.
12. Never optimize parameters or edit generated data to force a match to a published numerical target. Reconciliation reports should identify discrepancies rather than hiding them.
