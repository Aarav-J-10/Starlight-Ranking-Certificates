from collections import Counter, defaultdict
from statistics import mean, stdev
import json
import math
import random

from .schema import Row, Schema, label, require
from .statistics import clopper_pearson, ols, paired_interval, quantile

NOTES = {
    "wp1": "Cut confirmation is archived feedback, not independently authenticated. Latency excludes the failed cutoff.",
    "wp2-steering": "OLS uses command minus 75. This physical slope is not simulated gain g. The historical hysteresis estimator is unavailable.",
    "wp2-latency": "Linear sample quantiles; strict >33 and >50 ms deadlines. Raw response timestamps are absent.",
    "wp3": "Sample P95 is not a confidence interval. Original images and surveyed poses are absent; heading gate remains failed.",
    "wp4": "Recorded magnitudes and descriptive paired cohorts; no causal mismatch estimate. WP7 is a different sample.",
    "wp5": "Five session aggregates only; McNemar discordances are NOT IDENTIFIABLE. No historical trial rows are generated.",
    "wp6": "Processed labels only. Literal equality checks agreement; unsupported-winner flags cannot be independently re-adjudicated.",
    "wp7": "Configuration restoration is not exact numerical return. Response change does not identify geometry change. Some archived heading shifts are signed despite dictionary magnitude wording; values are preserved.",
    "wp8": "Pooled item ratios, not unweighted batch means. Items and batches may be dependent; no independence CI is asserted.",
    "d1": "Studies remain separate; overlap is unknown. Binomial CIs assume independent pairs; session bootstrap is sensitivity only with five clusters.",
    "primary-grid": "Simulated seven-switch A/D bundles, not physical Clock/Compass. Joint outcomes and generator are unavailable.",
    "confirmation": "Stored endpoints are preserved. Six common s=.030, dt=.040 settings are separate from two companion settings.",
    "model-forms": "Base rows repeat existing missions. Clearance changes the failure criterion; other forms change the model specification.",
    "attribution": "Reported finite-grid variance shares; original decomposition/weighting is unavailable. No individual-feature or physical causality.",
    "cartpole": "Metadata only: no episode-level outcomes or performance estimates. Excluded from robot mission totals.",
    "evidence": "Processed-tree hashes do not authenticate absent instrument logs, videos or simulator provenance.",
}


def grouped(rows: list[Row], *columns: str) -> dict[tuple, list[Row]]:
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[c] for c in columns)].append(row)
    return dict(groups)


def describe(values: list[float]) -> dict:
    return {"n": len(values), "mean": mean(values), "sd": stdev(values) if len(values) > 1 else None}


def group_means(rows: list[Row], groups: tuple[str, ...], value: str) -> list[dict]:
    return [dict(zip(groups, key), **describe([r[value] for r in sub])) for key, sub in grouped(rows, *groups).items()]


def binomial(k: int, n: int) -> dict:
    result = {"numerator": k, "denominator": n, "fraction": k / n, "method": "Clopper-Pearson 95%; independent-pair assumption"}
    try:
        result["ci95"] = clopper_pearson(k, n)
    except ImportError as error:
        result["ci95"] = None
        result["skipped"] = str(error)
    return result


def interval_audit(rows: list[Row], alpha: float) -> list[dict]:
    result = []
    corrected = {1.230: (-0.055, 1.153), 1.255: (-1.099, 0.450), 1.280: (-4.439, -2.427)}
    for r in rows:
        entry = {"id": next(iter(r.values())), "n_plus": r["n_plus"], "n_minus": r["n_minus"], "n_pairs": r["n_pairs"],
                 "gain_g": r["gain_g"], "stress_s": r["stress_s"], "timestep_s": r["timestep_s"],
                 "stored_pp": [r["ci_low_pp"], r["ci_high_pp"]], "stored_label": r["certificate_label"],
                 "family_alpha": alpha, "family_size": len(rows), "tail_probability": alpha / (4 * len(rows))}
        try:
            bounds = paired_interval(r["n_plus"], r["n_minus"], r["n_pairs"], alpha, len(rows))
            entry.update(recomputed_pp=bounds, recomputed_label=label(*bounds),
                         discrepancy=any(abs(a - b) > 0.00051 for a, b in zip(entry["stored_pp"], bounds)))
        except ImportError as error:
            entry.update(recomputed_pp=None, discrepancy=None, skipped=str(error))
        if str(entry["id"]).startswith("CONF_"):
            entry["common_stress_timestep"] = r["stress_s"] == 0.03 and r["timestep_s"] == 0.04
            entry["poster_v4_2_pp"] = corrected.get(r["gain_g"]) if entry["common_stress_timestep"] else None
        result.append(entry)
    return result


def analyze(name: str, rows: list[Row], seed: int = 0) -> dict:
    result = {"rows": len(rows), "notes": NOTES[name]}
    if name == "wp1":
        initial = [r for r in rows if r["cohort"] == "initial_gate"]
        latencies = [r["cut_latency_ms"] for r in rows if r["motor_cut_confirmed"]]
        result.update(trips=len(rows), initial_n=len(initial), initial_pass=sum(r["motor_cut_confirmed"] for r in initial),
                      overall_confirmed=len(latencies), mean_successful_cut_ms=mean(latencies),
                      failed_trip_ids=[r["trip_id"] for r in rows if not r["motor_cut_confirmed"]], timed_denominator=len(latencies))
    elif name == "wp2-steering":
        fit = ols([r["servo_command"] - 75 for r in rows], [r["protractor_angle_deg"] for r in rows])
        errors = [r["AS5600_angle_deg"] - r["protractor_angle_deg"] for r in rows]
        matched = []
        for (session, command), sub in grouped(rows, "session_id", "servo_command").items():
            sweeps = {r["sweep_direction"]: r["protractor_angle_deg"] for r in sub}
            if len(sweeps) == 2:
                matched.append({"session": session, "command": command, "forward_minus_reverse_deg": sweeps["forward"] - sweeps["reverse"]})
        result.update(protractor_ols_slope=fit["slope"], fit=fit, sensor_bias_deg=mean(errors),
                      sensor_rmse_deg=math.sqrt(mean(x * x for x in errors)),
                      battery_sweep=group_means(rows, ("session_id", "sweep_direction"), "battery_voltage_V"),
                      matched_hysteresis=matched, hysteresis_method="Within-session equal-command forward minus reverse; newly chosen estimator")
    elif name == "wp2-latency":
        values = [r["latency_ms"] for r in rows]
        result.update(events=len(rows), **{f"p{p}_ms": quantile(values, p / 100) for p in (50, 95, 99)},
                      above_33ms=sum(v > 33 for v in values), above_50ms=sum(v > 50 for v in values))
    elif name == "wp3":
        p = quantile([r["position_error_mm"] for r in rows], .95)
        h = quantile([r["heading_error_deg"] for r in rows], .95)
        result.update(frames=len(rows), position_p95_mm=p, heading_p95_deg=h,
                      position_limit_mm=2.5, heading_limit_deg=1.0, position_pass=p <= 2.5, heading_pass=h <= 1.0)
    elif name == "wp4":
        groups = grouped(rows, "session", "condition", "controller")
        means, counts = defaultdict(dict), {}
        for (session, condition, controller), sub in groups.items():
            cohort = f"{session}_{condition}"
            means[cohort][controller] = mean(r["heading_shift_deg"] for r in sub)
            counts[cohort] = len(sub)
        result.update(pairs=len({r["pair_id"] for r in rows}), n_by_controller=counts, means=dict(means),
                      by_order_study=group_means(rows, ("study_id", "session", "condition", "order", "controller"), "heading_shift_deg"),
                      battery_by_cohort=group_means(rows, ("session", "condition", "controller"), "battery_V"))
    elif name == "wp5":
        result.update(sessions=len(rows), pairs=sum(r["n_pairs"] for r in rows),
                      clock_success=sum(r["clock_success"] for r in rows), compass_success=sum(r["compass_success"] for r in rows),
                      session_counts=rows, mcnemar="NOT IDENTIFIABLE")
        result["missions"] = 2 * result["pairs"]
    elif name == "wp6":
        result.update(audit_units=len(rows), agreements=sum(r["agreement"] for r in rows),
                      unsupported_winners=sum(r["unsupported_winner"] for r in rows),
                      other_disagreements=sum(not r["agreement"] and not r["unsupported_winner"] for r in rows), cases=rows)
    elif name == "wp7":
        phases = grouped(rows, "phase")
        require(len(phases) == 3 and all(len(sub) == 12 for sub in phases.values()), "Archived WP7 needs 12 runs per phase")
        gain = {p[0]: mean(r["measured_gain_response"] for r in sub) for p, sub in phases.items()}
        current = {p[0]: mean(r["servo_current_A"] for r in sub) for p, sub in phases.items()}
        result.update(runs_per_phase=len(next(iter(phases.values()))), mean_gain=gain, mean_current=current,
                      gain_b_vs_a_pct=100 * (gain["B_modified"] / gain["A_baseline"] - 1),
                      current_b_vs_a_pct=100 * (current["B_modified"] / current["A_baseline"] - 1),
                      gain_by_phase=group_means(rows, ("phase",), "measured_gain_response"),
                      current_by_phase=group_means(rows, ("phase",), "servo_current_A"))
    elif name == "wp8":
        for (recipe,), sub in grouped(rows, "recipe").items():
            result[recipe] = {"correct": sum(r["n_correct"] for r in sub), "total": sum(r["n_items"] for r in sub)}
            result[recipe]["accuracy"] = result[recipe]["correct"] / result[recipe]["total"]
        result.update(batches=len(rows), pooled_correct=sum(r["n_correct"] for r in rows), pooled_items=sum(r["n_items"] for r in rows))
        result["pooled_accuracy"] = result["pooled_correct"] / result["pooled_items"]
        result["recipe_condition"] = [dict(recipe=k[0], condition=k[1], batches=len(sub), correct=sum(r["n_correct"] for r in sub), total=sum(r["n_items"] for r in sub)) for k, sub in grouped(rows, "recipe", "condition").items()]
        for group in result["recipe_condition"]:
            group["accuracy"] = group["correct"] / group["total"]
    elif name == "d1":
        counts = Counter(r["outcome"] for r in rows)
        failures = len(rows) - counts["both_succeed"]
        result.update(pairs=len(rows), failure_bearing_pairs=failures, **{k: counts[k] for k in ("both_succeed", "both_fail", "clock_only", "compass_only")},
                      shared_failure=binomial(counts["both_fail"], failures), study_id=rows[0]["study_id"], overlap_unknown=True)
        sessions = list(grouped(rows, "session").values())
        rng = random.Random(seed)
        samples = []
        for _ in range(2000):
            sample = [r for sub in rng.choices(sessions, k=len(sessions)) for r in sub if r["outcome"] != "both_succeed"]
            if sample:
                samples.append(sum(r["outcome"] == "both_fail" for r in sample) / len(sample))
        result["session_bootstrap"] = {"ci95": [quantile(samples, .025), quantile(samples, .975)], "clusters": len(sessions), "resamples": len(samples), "seed": seed, "method": "Percentile cluster bootstrap of shared/failure-bearing ratio"}
    elif name in {"primary-grid", "confirmation", "model-forms"}:
        result.update(certificates=dict(Counter(r["certificate_label"] for r in rows)),
                      matched_pairs=sum(r["n_pairs"] for r in rows if not r.get("is_base_repeat", 0)),
                      missions=sum(r.get("missions_executed", r.get("missions_executed_additional", 0)) for r in rows),
                      interval_audit=interval_audit(rows, .02 if name == "primary-grid" else .01),
                      interval_method="Bonferroni marginal Clopper-Pearson; tail=alpha/(4*m); difference=[Lplus-Uminus,Uplus-Lminus]*100; new explicit allocation, historical procedure not version-locked")
        if name == "model-forms":
            result["non_base_model_forms"] = sum(not r["is_base_repeat"] for r in rows)
        if name == "confirmation":
            result["witnesses"] = {f'gain_{r["gain_g"]:.3f}'.replace(".", "_"): {"n_plus": r["n_plus"], "n_minus": r["n_minus"], "N": r["n_pairs"], "delta_pp": r["delta_pp"]} for r in rows if r["stress_s"] == .03 and r["timestep_s"] == .04 and r["gain_g"] in (1.2, 1.26)}
    elif name == "attribution":
        require(abs(sum(r["variance_share"] for r in rows) - 1) < .001, "Attribution shares do not normalize to one")
        result.update(shares={r["factor"]: r["variance_share"] for r in rows}, sum_shares=sum(r["variance_share"] for r in rows), normalization="Archived shares sum to one; decomposition not independently reconstructed")
    elif name == "cartpole":
        result.update(episodes=rows[0]["n_episodes"], metadata_only=True, performance=None)
    elif name == "evidence":
        result.update(assets=rows, raw_authenticity="NOT VERIFIED")
    return result


DATASETS = {
    "wp1": ("physical/wp1/emergency_stop_trips.csv",),
    "wp2-steering": ("physical/wp2/steering_calibration.csv",),
    "wp2-latency": ("physical/wp2/latency_events.csv",),
    "wp3": ("physical/wp3/dock_camera_accuracy.csv",),
    "wp4": ("physical/wp4/clock_compass_pairs.csv",),
    "wp5": ("physical/wp5_wp6/docking_session_summary.csv",),
    "wp6": ("physical/wp5_wp6/independent_audit.csv",),
    "wp7": ("physical/wp7/linkage_ABA.csv",),
    "wp8": ("physical/wp8/colour_sorter.csv",),
    "d1": ("physical/d1/shared_failure_60pair.csv", "physical/d1/extended_shared_failure_pairs.csv", "physical/d1/extended_shared_summary.csv"),
    "primary-grid": ("simulation/primary_grid.csv",),
    "confirmation": ("simulation/confirmation.csv",),
    "model-forms": ("simulation/model_forms.csv",),
    "attribution": ("simulation/attribution.csv",),
    "cartpole": ("simulation/cartpole_summary.csv",),
    "evidence": ("evidence/raw_data_index.csv",),
}


def compute(schema: Schema, seed: int = 0) -> tuple[dict, dict]:
    tables = {key: schema.read(key) for key in schema.spec}
    summaries = {}
    for name, keys in DATASETS.items():
        if name == "d1":
            small, extended, stored = (tables[k] for k in keys)
            summaries[name] = {"detailed": analyze(name, small, seed), "extended": analyze(name, extended, seed), "stored_summary": stored}
            for field in ("both_fail", "clock_only", "compass_only", "failure_bearing_pairs"):
                if summaries[name]["extended"][field] != stored[0][field]:
                    raise ValueError(f"D1 extended summary disagrees: {field}")
        else:
            summaries[name] = analyze(name, tables[keys[0]], seed)
    grid = tables[DATASETS["primary-grid"][0]]
    require(all(r["n_pairs"] == 4000 for r in grid), "Archived grid needs 4000 pairs per cell")
    require(all(r["n_pairs"] == 8000 for r in tables[DATASETS["confirmation"][0]]), "Archived confirmation needs 8000 pairs per setting")
    require(all(r["n_pairs"] == 4000 for r in tables[DATASETS["model-forms"][0]]), "Archived model forms need 4000 pairs per row")
    for row in tables[DATASETS["model-forms"][0]]:
        if row["is_base_repeat"]:
            matches = [g for g in grid if (g["gain_g"], g["stress_s"], g["timestep_s"]) == (row["gain_g"], row["stress_s"], row["timestep_s"])]
            if len(matches) != 1 or any(matches[0][c] != row[c] for c in ("n_pairs", "n_plus", "n_minus")):
                raise ValueError("Model base repeat does not match primary counts")
    return tables, summaries


def expected_comparison(schema: Schema, s: dict, tables: dict) -> list[dict]:
    g, c, m = (s[k] for k in ("primary-grid", "confirmation", "model-forms"))
    sim = {"primary_grid_rows": g["rows"], "grid_certificates": g["certificates"], "grid_pairs_per_cell": tables[DATASETS["primary-grid"][0]][0]["n_pairs"],
           "grid_missions": g["missions"], "confirmation_rows": c["rows"], "confirmation_pairs_per_setting": tables[DATASETS["confirmation"][0]][0]["n_pairs"],
           "confirmation_missions": c["missions"], "model_forms_rows": m["rows"], "non_base_model_forms": m["non_base_model_forms"],
           "additional_model_missions": m["missions"], "total_robot_missions": sum(x["missions"] for x in (g, c, m)),
           "total_matched_pairs": sum(x["matched_pairs"] for x in (g, c, m)), **c["witnesses"]}
    physical = {target: s[source] for target, source in {"wp1": "wp1", "wp2_calibration": "wp2-steering", "wp2_latency": "wp2-latency", "wp3_camera": "wp3", "wp4": "wp4", "wp5": "wp5", "wp6": "wp6", "wp7": "wp7", "wp8": "wp8"}.items()}
    physical.update(d1_60=s["d1"]["detailed"], d1_extended=s["d1"]["extended"])
    actual = {"simulation": sim, "physical": physical}
    expected = json.loads((schema.contracts / "EXPECTED_RESULTS.json").read_text(encoding="utf-8"))
    checks = []

    def visit(want: dict, got: dict, prefix: str = "") -> None:
        for key, value in want.items():
            path = f"{prefix}.{key}".strip(".")
            if isinstance(value, dict):
                visit(value, got[key], path)
            elif isinstance(value, (int, float)):
                found = got[key]
                passed = found == value if isinstance(value, int) else math.isclose(found, value, rel_tol=1e-8, abs_tol=1e-8)
                checks.append({"metric": path, "expected": value, "actual": found, "pass": passed})
    visit({k: expected[k] for k in ("simulation", "physical")}, actual)
    return checks
