import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

Row = dict[str, Any]
INTS = set("button_pressed motor_cut_confirmed missed_33ms missed_50ms frame_idx aruco_id_left aruco_id_right n_pairs clock_success compass_success agreement unsupported_winner n_pairs_in_unit rep n_items n_correct clock_fail compass_fail failure_bearing_pairs both_fail clock_only compass_only n_episodes n_plus n_minus is_base_repeat missions_executed missions_executed_additional".split())
FLOATS = set("cut_latency_ms latency_ms battery_voltage_V servo_command protractor_angle_deg AS5600_angle_deg position_error_mm heading_error_deg heading_shift_deg battery_V measured_gain_response servo_current_A clock_heading_shift_deg compass_heading_shift_deg as5600_delta_deg accuracy shared_fraction gain_g stress_s timestep_s delta_pp ci_low_pp ci_high_pp variance_share".split())
FLAGS = set("button_pressed motor_cut_confirmed missed_33ms missed_50ms agreement unsupported_winner clock_fail compass_fail is_base_repeat".split())
ACTIONS = {"select_A", "select_D", "accept_either", "reject_both", "request_more"}
CATEGORIES = {
    "controller": {"Clock", "Compass"}, "order": {"AB", "BA"},
    "sweep_direction": {"forward", "reverse"},
    "cohort": {"initial_gate", "extended_log"}, "unit_type": {"dial", "linkage"},
    "decision": ACTIONS, "reference_outcome": ACTIONS,
    "phase": {"A_baseline", "B_modified", "Aprime_restored"},
    "recipe": {"S1_fixed", "S2_calibrated", "S3_recheck"},
    "outcome": {"both_succeed", "both_fail", "clock_only", "compass_only"},
    "certificate_label": {"A", "D", "unresolved"},
    "model_form": {"base", "clearance", "fractional", "nonlinear", "triangular"},
    "category": {"physical", "simulation"},
    "factor": {"gain_g", "stress_s", "timestep_s", "g_x_s", "g_x_dt", "s_x_dt", "g_x_s_x_dt", "residual"},
}
NONNEGATIVE = FLOATS - {"protractor_angle_deg", "AS5600_angle_deg", "as5600_delta_deg", "clock_heading_shift_deg", "compass_heading_shift_deg", "delta_pp", "ci_low_pp", "ci_high_pp"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def label(low: float, high: float) -> str:
    return "A" if low > 0 else "D" if high < 0 else "unresolved"


def outcome(clock_fail: int, compass_fail: int) -> str:
    require(clock_fail in (0, 1) and compass_fail in (0, 1), "Failure flags must be 0/1")
    return {(0, 0): "both_succeed", (1, 1): "both_fail", (1, 0): "clock_only", (0, 1): "compass_only"}[clock_fail, compass_fail]


def units(column: str) -> str:
    for suffix, unit in (("_ms", "ms"), ("_mm", "mm"), ("_deg", "degrees"), ("_V", "V"), ("_A", "A"), ("_pp", "percentage points")):
        if column.endswith(suffix):
            return unit
    if column == "timestep_s":
        return "s"
    if column == "servo_command":
        return "command units; neutral 75"
    if column in {"gain_g", "stress_s", "measured_gain_response", "accuracy", "shared_fraction", "variance_share"}:
        return "dimensionless"
    return "count/flag" if column in INTS else "identifier/text"


class Schema:
    def __init__(self, root: Path, contracts: Path | None = None):
        self.root = root.resolve()
        self.contracts = contracts or self.root.parent.parent / "CONTRACTS"
        self.spec = json.loads((self.contracts / "CSV_SCHEMAS.json").read_text(encoding="utf-8"))

    def read(self, key: str, archived: bool = True) -> list[Row]:
        with (self.root / key).open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            require(reader.fieldnames == self.spec[key]["columns"], f"{key}: exact header/order mismatch")
            return self.validate(key, list(reader), archived)

    def validate(self, key: str, rows: list[Row], archived: bool = False) -> list[Row]:
        columns = self.spec[key]["columns"]
        result, seen = [], set()
        for index, raw in enumerate(rows, 1):
            context = f"{key} row {index}"
            require(set(raw) == set(columns), f"{context}: missing/extra fields")
            row = {}
            for column in columns:
                value = raw[column]
                if column == "cut_latency_ms" and value in (None, ""):
                    row[column] = None
                    continue
                require(value is not None and str(value).strip() != "", f"{context}: empty {column}")
                try:
                    if column in INTS:
                        require(str(value).lstrip("-").isdigit(), f"{context}: {column} must be integer")
                        value = int(value)
                        require(value >= 0, f"{context}: negative {column}")
                    elif column in FLOATS:
                        value = float(value)
                        require(math.isfinite(value), f"{context}: non-finite {column}")
                        if column in NONNEGATIVE:
                            require(value >= 0, f"{context}: negative {column}")
                    else:
                        value = str(value)
                except (TypeError, ValueError) as error:
                    raise ValueError(f"{context}: invalid {column}: {value!r}") from error
                if column in FLAGS:
                    require(value in (0, 1), f"{context}: {column} must be 0/1")
                if column in CATEGORIES:
                    require(value in CATEGORIES[column], f"{context}: unknown {column}: {value}")
                if column == "timestamp":
                    stamp = datetime.fromisoformat(value)
                    require(archived or stamp.utcoffset() is not None, f"{context}: new timestamps need timezone")
                row[column] = value
            if "sweep_direction" in row:
                identity = tuple(row[c] for c in ("session_id", "sweep_direction", "servo_command"))
            elif "frame_idx" in row:
                identity = (row["point_id"], row["frame_idx"])
            elif "phase" in row:
                identity = (row["phase"], row["rep"])
            elif "controller" in row:
                identity = (row["pair_id"], row["controller"])
            elif "clock_success" in row:
                identity = (row["study_id"], row["session"])
            else:
                identity = row[columns[0]]
            require(identity not in seen, f"{context}: duplicate identity {identity}")
            seen.add(identity)
            self.check_row(key, row)
            result.append(row)
        if archived:
            require(len(result) == self.spec[key]["rows"], f"{key}: archived row count mismatch")
            require(str(result[0][columns[0]]) == self.spec[key]["first_id"], f"{key}: archived first ID mismatch")
        if "clock_compass" in key:
            pairs = {r["pair_id"] for r in result}
            for pair in pairs:
                group = [r for r in result if r["pair_id"] == pair]
                require({r["controller"] for r in group} == {"Clock", "Compass"}, f"{pair}: incomplete pair")
                for column in ("study_id", "session", "condition", "order"):
                    require(len({r[column] for r in group}) == 1, f"{pair}: inconsistent {column}")
        if "primary_grid" in key:
            require(len({(r["gain_g"], r["stress_s"], r["timestep_s"]) for r in result}) == len(result), "Duplicate grid factors")
        return result

    @staticmethod
    def check_row(key: str, r: Row) -> None:
        if "condition" in r:
            choices = {"normal", "warm_dim", "fast_feed"} if "colour_sorter" in key else {"matched", "mismatch"} if "clock_compass" in key else {"matched", "mismatched"}
            require(r["condition"] in choices, f"{key}: unknown condition")
        if "motor_cut_confirmed" in r:
            require((r["cut_latency_ms"] is not None) == bool(r["motor_cut_confirmed"]), "Latency only on confirmed cuts")
        if "latency_ms" in r:
            for deadline in (33, 50):
                require(r[f"missed_{deadline}ms"] == int(r["latency_ms"] > deadline), "Deadline flag mismatch")
        if "servo_command" in r:
            require(35 <= r["servo_command"] <= 105, "Servo command outside [35,105]")
        if "aruco_id_left" in r:
            require((r["aruco_id_left"], r["aruco_id_right"]) == (10, 11), "Expected ArUco IDs 10/11")
        if "clock_fail" in r:
            require(r["outcome"] == outcome(r["clock_fail"], r["compass_fail"]), "Failure truth-table mismatch")
            require("extended" not in key or r["outcome"] != "both_succeed", "Extended ledger is failure-bearing only")
        if "clock_success" in r:
            require(r["n_pairs"] > 0 and max(r["clock_success"], r["compass_success"]) <= r["n_pairs"], "Invalid docking denominator")
        if "agreement" in r:
            require(r["agreement"] == int(r["decision"] == r["reference_outcome"]), "Audit agreement mismatch")
        if "n_items" in r:
            require(0 <= r["n_correct"] <= r["n_items"] and r["n_items"] > 0, "Invalid item denominator")
            require(abs(r["accuracy"] - r["n_correct"] / r["n_items"]) <= 0.000051, "Accuracy exceeds four-decimal rounding")
        if "variance_share" in r:
            require(r["variance_share"] <= 1, "Invalid variance share")
        if "failure_bearing_pairs" in r:
            require(r["failure_bearing_pairs"] > 0 and sum(r[c] for c in ("both_fail", "clock_only", "compass_only")) == r["failure_bearing_pairs"], "Invalid failure denominator")
            require(abs(r["shared_fraction"] - r["both_fail"] / r["failure_bearing_pairs"]) < 0.000051, "Invalid shared fraction")
        if "n_plus" in r:
            n = r["n_pairs"]
            require(n > 0 and r["n_plus"] + r["n_minus"] <= n, "Invalid discordance denominator")
            require(abs(r["delta_pp"] - 100 * (r["n_plus"] - r["n_minus"]) / n) <= 1e-6, "Risk difference mismatch")
            require(-100 <= r["ci_low_pp"] <= r["delta_pp"] <= r["ci_high_pp"] <= 100, "Invalid risk interval")
            require(label(r["ci_low_pp"], r["ci_high_pp"]) == r["certificate_label"], "Interval sign mismatch")
            if "is_base_repeat" in r:
                require(r["is_base_repeat"] == int(r["model_form"] == "base"), "Base-repeat flag mismatch")
                require(r["missions_executed_additional"] == 2 * n * (1 - r["is_base_repeat"]), "Additional missions mismatch")
            else:
                require(r["missions_executed"] == 2 * n, "Two missions per matched pair")

    def export(self, key: str, rows: list[Row], target: Path) -> None:
        protected = self.root.parent if self.root.parent.name == "REFERENCE_DATA" else self.root
        require(not target.resolve().is_relative_to(protected), "Cannot export into reference data")
        rows = self.validate(key, rows)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, self.spec[key]["columns"], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
