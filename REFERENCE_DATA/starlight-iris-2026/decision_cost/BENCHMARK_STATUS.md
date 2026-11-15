# Decision-cost benchmark — intentionally excluded

The published processed-data archive does **not** include the decision-cost
case-level table or aggregated comparisons. During verification, the nominal
`Baseline_AlwaysSelectA` strategy had 442/640 non-A actions;
`Ablation_NoWithhold` had 149/640 `request_more` actions; and
`Ablation_NoAdequacyCheck` had 32/640 `reject_both` actions.

The underlying action-selection policies and fallback rules were not supplied,
so the named-baseline comparison cannot be validated or repaired responsibly
from exported outcomes alone. The historical 14.3–33.0% cost-reduction claim
is **not validated by this public release**.

The numerical benchmark is preserved separately for private reconciliation.
No simulation/physical CSV in this release was altered.
