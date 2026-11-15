from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PolicyConfig:
    minimum_reliability: float
    equivalence_pp: float
    testing_cost: float
    error_cost: float
    budget: float

    def __post_init__(self):
        values = (self.minimum_reliability, self.equivalence_pp, self.testing_cost, self.error_cost, self.budget)
        if not all(math.isfinite(x) for x in values) or not 0 <= self.minimum_reliability <= 1 or not 0 <= self.equivalence_pp <= 100 or min(values[2:]) < 0:
            raise ValueError("insufficient_configuration: invalid policy thresholds/costs")


def decide(difference_pp: tuple[float, float], reliability_a: tuple[float, float], reliability_d: tuple[float, float], config: PolicyConfig) -> dict:
    if config is None:
        raise ValueError("insufficient_configuration: supply PolicyConfig")
    for interval, lower, upper in ((difference_pp, -100, 100), (reliability_a, 0, 1), (reliability_d, 0, 1)):
        if len(interval) != 2 or not all(math.isfinite(x) for x in interval) or not lower <= interval[0] <= interval[1] <= upper:
            raise ValueError("Invalid interval or units")
    low, high = difference_pp
    a_ok, d_ok = reliability_a[0] >= config.minimum_reliability, reliability_d[0] >= config.minimum_reliability
    if reliability_a[1] < config.minimum_reliability and reliability_d[1] < config.minimum_reliability:
        action, reason = "reject_both", "Both upper reliability bounds miss the minimum"
    elif a_ok and d_ok and -config.equivalence_pp <= low <= high <= config.equivalence_pp:
        action, reason = "accept_either", "Both adequate and the entire difference interval is inside equivalence limits"
    elif low > 0 and a_ok:
        action, reason = "select_A", "Positive D-minus-A failure interval and adequate A reliability"
    elif high < 0 and d_ok:
        action, reason = "select_D", "Negative D-minus-A failure interval and adequate D reliability"
    else:
        action, reason = "request_more", "Adequacy or preference/equivalence remains unresolved"
    can_test = config.testing_cost <= min(config.budget, config.error_cost)
    return {"action": action, "trace": reason, "testing_permitted": can_test if action == "request_more" else False,
            "cost_rule": "One further test permitted only if its cost fits budget and does not exceed error cost; no value-of-information claim"}
