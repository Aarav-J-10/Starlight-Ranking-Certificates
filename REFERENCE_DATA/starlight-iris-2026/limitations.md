# Limitations

1. This package contains **processed** tables. It does not independently
   regenerate the simulator or authenticate sealed instrument logs.

2. Primary-grid and confirmation public files publish discordance counts only.
   Joint shared-success/failure splits are not included because they are not
   identified by n_plus/n_minus alone.

3. Model-form base-repeat rows share discordance counts with the primary grid
   but may use a different simultaneous CI family (see DATA_DICTIONARY).

4. The decision-cost benchmark has been **excluded** because observed actions
   contradict literal strategy names and the true policy algorithms were not
   supplied. The reported cost-reduction range is not validated in this release.

5. WP4 summaries are descriptive. Matched Clock mean (6.64°) is not smaller than
   mismatch Clock mean (6.42°); do not claim a mismatch-driven increase from
   these cohort means alone.

6. WP1 cumulative confirmed cutoffs are 23/24, not 24/24.

7. WP3 heading p95 is 1.286° (fail vs 1.0°).

8. D1 60-pair and extended 204-pair ledgers are separate studies.

9. SHA-256 manifests authenticate this processed tree only.
