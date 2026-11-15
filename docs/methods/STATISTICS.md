# Methods

Linear sample quantiles interpolate at `(n-1)*p`. OLS includes an intercept and
uses command minus 75. Standard deviations are sample SDs. WP8 pools item counts;
it does not average batch accuracies. D1 divides shared failures by
failure-bearing pairs, with separate study denominators.

For each simulated setting, `delta_pp=100*(n_plus-n_minus)/N`, where `n_plus`
means D-only failure. A positive interval certifies A; a negative interval
certifies D. An interval containing zero establishes neither equivalence nor
adequacy. Joint success/failure counts cannot be recovered from discordances.

For family error alpha and m settings, allocate alpha/(2m) to each of two
binomial marginals, or alpha/(4m) per tail. For count k out of N, use exact
Clopper–Pearson bounds from beta quantiles, with exact 0/1 boundary cases.
The difference interval is `100*[Lplus-Uminus, Uplus-Lminus]`. Bonferroni does
not require independence between the two discordant categories.

Primary: alpha=.02, m=66. Confirmation: alpha=.01, m=8. Model forms:
alpha=.01, m=15, including base repeats in this explicit sensitivity family.
This allocation is a new documented implementation choice; a version-locked
original procedure is unavailable. Every row gets a side-by-side audit, including
two confirmation companion settings. Stored classification and recalculated
classification are separate fields. A difference above .00051 pp is flagged;
it never changes the stored CSV. Corrected poster endpoints supplied in the
contract are reported separately, not used to fit the method.

D1 reports a 95% exact binomial interval, with an independent-pair assumption.
An additional 2,000-resample session bootstrap resamples whole sessions and
recomputes the ratio. Only five clusters exist; these percentile bounds are a
sensitivity check, not established cluster-adjusted coverage. No pooled D1 CI.
WP5 marginals do not identify McNemar's discordances. No WP8 independence CI
is inferred from batch counts. P95 camera error is a sample percentile.

The decision policy checks both reliability intervals against an explicit
minimum and checks that the full difference interval lies within explicit
equivalence limits. Preference also requires the selected design to be adequate.
Unresolved cases return `request_more`; a separate flag says whether one test
fits both budget and error-cost caps. Costs do not estimate information value
or reproduce any historical benchmark. Conflicting criteria prefer certified
equivalence when both designs are adequate; this rule is newly specified.

Numerical references: [SciPy beta quantiles](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html)
and [SciPy exact binomial intervals](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html).
