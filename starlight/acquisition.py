import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import random
import time
from uuid import uuid4
import warnings

from .controllers import Hardware, MockHardware
from .schema import require

PAIR_COLUMNS = ["study_id", "session_id", "pair_id", "clock_trial_id", "compass_trial_id", "order", "configuration_id"]
CHECKS = ("independent_latching_estop", "wiring_verified", "power_limits_verified", "calibration_verified", "physical_clearance", "operator_supervised")


@dataclass(frozen=True)
class ArmConfig:
    operator: str
    apparatus_revision: str
    confirmed_revision: str
    timeout_s: float
    max_duty: float
    checks: dict


class SafetyGuard:
    def __init__(self, hardware: Hardware, config: ArmConfig, enable: bool, armed: bool, clock=time.monotonic):
        self.hardware, self.config, self.clock = hardware, config, clock
        self.enabled, self.armed, self.deadline = enable, armed, 0.0

    def __enter__(self):
        self.hardware.stop()
        c = self.config
        require(self.enabled and self.armed, "Hardware needs --enable-hardware and --arm")
        require(bool(c.operator) and c.apparatus_revision == c.confirmed_revision, "Missing operator or stale apparatus revision")
        require(all(c.checks.get(key) is True for key in CHECKS), "Operator checklist incomplete")
        require(0 < c.timeout_s <= 60 and 0 < c.max_duty <= 1, "Invalid timeout/duty limits")
        require(not self.hardware.estop_active(), "E-stop is active")
        self.deadline = self.clock() + c.timeout_s
        return self

    def command(self, steering: float, duty: float) -> None:
        try:
            require(self.deadline > self.clock(), "Deadman timeout")
            require(not self.hardware.estop_active(), "E-stop is active")
            require(35 <= steering <= 105 and 0 <= duty <= self.config.max_duty, "Command exceeds approved limits")
            self.hardware.command(steering, duty)
        except BaseException:
            self.deadline = 0.0
            self.hardware.stop()
            raise

    def __exit__(self, *_):
        self.deadline = 0.0
        self.hardware.stop()


class Recorder:
    def __init__(self, directory: Path, study_id: str, session_id: str, configuration_id: str, metadata: dict | None = None):
        require(not study_id.startswith("sim"), "Physical recorder cannot mix simulation")
        require("reference_data" not in [part.lower() for part in directory.resolve().parts], "Cannot log into REFERENCE_DATA")
        self.directory, self.study, self.session, self.configuration = directory, study_id, session_id, configuration_id
        self.pairs, self.trials, self.last_ns, self.calibrated, self.completed = {}, set(), 0, False, set()
        self.event_index = 0
        directory.mkdir(parents=True, exist_ok=True)
        self.events_path = directory / "events.jsonl"
        self.pairs_path = directory / "acquisition_pairs.csv"
        require(not self.events_path.exists() and not self.pairs_path.exists(), "Use a new run directory; recorder is append-only")
        self.events_path.touch(exist_ok=False)
        with self.pairs_path.open("x", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, PAIR_COLUMNS).writeheader()
        from .reports import dump, manifest
        details = dict(metadata or {}, apparatus_revision=configuration_id, paired_session_ids=[session_id])
        dump(directory / "run_manifest.json", manifest("TEST_ONLY" if study_id.startswith("TEST_ONLY") else "new_acquisition", {}, details))

    def pair(self, order: str) -> dict:
        require(order in ("AB", "BA"), "Order must be AB or BA")
        pair = dict(zip(PAIR_COLUMNS, (self.study, self.session, uuid4().hex, uuid4().hex, uuid4().hex, order, self.configuration)))
        require(pair["clock_trial_id"] != pair["compass_trial_id"], "Ambiguous trial IDs")
        self.pairs[pair["pair_id"]] = pair
        self.trials.update((pair["clock_trial_id"], pair["compass_trial_id"]))
        with self.pairs_path.open("a", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, PAIR_COLUMNS).writerow(pair)
        return pair

    def event(self, event_type: str, **fields) -> dict:
        require(event_type in {"calibration", "start", "measurement", "result", "stop"}, "Unknown event type")
        reserved = {"study_id", "session_id", "configuration_id", "event_type", "monotonic_ns", "wall_time_iso8601", "event_index"}
        require(not reserved.intersection(fields), "Caller cannot replace lineage/clocks")
        require(fields.get("operator_confirmed") is True, "Operator confirmation required")
        require(fields.get("reference_source") in {"hardware", "camera", "manual", "TEST_ONLY"}, "Reference source required")
        run_manifest = json.loads((self.directory / "run_manifest.json").read_text(encoding="utf-8"))
        if fields["reference_source"] != "TEST_ONLY":
            require(bool(run_manifest["operator"]), "Real observations need operator metadata")
        if event_type == "calibration":
            require(not self.calibrated and fields.get("calibration_file"), "One calibration snapshot per run; supply file")
            if fields["reference_source"] != "TEST_ONLY":
                source = Path(fields["calibration_file"])
                blob = source.read_bytes()
                fields["calibration_sha256"] = hashlib.sha256(blob).hexdigest()
                target = self.directory / ("calibration_snapshot" + source.suffix)
                with target.open("xb") as file:
                    file.write(blob)
                fields["calibration_snapshot"] = str(target)
                from .reports import dump
                run_manifest["calibration_file"] = str(target)
                run_manifest["calibration_sha256"] = fields["calibration_sha256"]
                dump(self.directory / "run_manifest.json", run_manifest)
        else:
            require(self.calibrated, "Record calibration before trials")
            pair = self.pairs.get(fields.get("pair_id"))
            require(pair is not None, "Unknown pair_id")
            require(fields.get("controller") in {"Clock", "Compass"}, "Physical controller required")
            trial = pair[f'{fields["controller"].lower()}_trial_id']
            require(fields.get("trial_id") == trial, "Trial/controller pairing mismatch")
            require(trial not in self.completed, "Trial already completed")
            if event_type == "result":
                require(type(fields.get("success")) is bool, "Result needs boolean success")
                require(fields["success"] or bool(fields.get("fail_reason")), "Failed result needs reason")
        video = fields.get("video_path")
        if not video or not Path(video).is_file():
            warnings.warn("Video unavailable; no media fabricated", stacklevel=2)
        now = time.monotonic_ns()
        require(now >= self.last_ns, "Non-monotonic event")
        event = dict(study_id=self.study, session_id=self.session, configuration_id=self.configuration, event_type=event_type,
                     monotonic_ns=now, event_index=self.event_index, wall_time_iso8601=datetime.now(timezone.utc).isoformat(), **fields)
        encoded = json.dumps(event, allow_nan=False)
        with self.events_path.open("a", encoding="utf-8") as file:
            file.write(encoded + "\n")
            file.flush()
        self.last_ns = now
        self.event_index += 1
        if event_type == "calibration":
            self.calibrated = True
        if event_type == "result":
            self.completed.add(fields["trial_id"])
        return event


def balanced_orders(n: int, seed: int) -> list[str]:
    require(n > 0, "Pair count must be positive")
    orders = ["AB", "BA"] * (n // 2) + (["AB"] if n % 2 else [])
    random.Random(seed).shuffle(orders)
    return orders


def export_pairs(recorder: Recorder, schema, condition: str) -> dict:
    from .analysis import DATASETS
    from .schema import outcome
    require(condition in {"matched", "mismatch"}, "Specify matched/mismatch starting condition")
    events = [json.loads(line) for line in recorder.events_path.read_text(encoding="utf-8").splitlines()]
    require(all(e["reference_source"] != "TEST_ONLY" for e in events), "TEST_ONLY events cannot become research CSVs")
    results = [e for e in events if e["event_type"] == "result"]
    rows, heading = [], []
    clock_success = compass_success = 0
    for pair in recorder.pairs.values():
        members = {e["controller"]: e for e in results if e.get("pair_id") == pair["pair_id"]}
        require(set(members) == {"Clock", "Compass"}, "Both controller results required per pair")
        clock, compass = members["Clock"], members["Compass"]
        clock_success += clock["success"]
        compass_success += compass["success"]
        rows.append(dict(pair_id=pair["pair_id"], study_id=recorder.study, session=recorder.session,
                         clock_fail=int(not clock["success"]), compass_fail=int(not compass["success"]),
                         outcome=outcome(int(not clock["success"]), int(not compass["success"])),
                         condition="mismatched" if condition == "mismatch" else "matched", timestamp=max(clock["wall_time_iso8601"], compass["wall_time_iso8601"])))
        for controller, event in members.items():
            if "heading_shift_deg" in event and "battery_V" in event:
                heading.append(dict(pair_id=pair["pair_id"], study_id=recorder.study, session=recorder.session, condition=condition,
                                    order=pair["order"], controller=controller, heading_shift_deg=event["heading_shift_deg"], battery_V=event["battery_V"], timestamp=event["wall_time_iso8601"]))
    require(bool(rows), "No completed pairs")
    exports = {DATASETS["d1"][0]: rows, DATASETS["wp5"][0]: [dict(study_id=recorder.study, session=recorder.session, n_pairs=len(rows), clock_success=clock_success, compass_success=compass_success)]}
    if heading:
        require(len(heading) == 2 * len(rows), "Heading measurements required for both controllers in every pair")
        exports[DATASETS["wp4"][0]] = heading
    for key, values in exports.items():
        schema.validate(key, values)
    for key, values in exports.items():
        schema.export(key, values, recorder.directory / "csv" / key)
    return {"pair_ids": list(recorder.pairs), "session_id": recorder.session, "exports": list(exports)}


def dry_run(directory: Path, experiment: str, seed: int) -> dict:
    recorder = Recorder(directory, "TEST_ONLY_" + experiment, uuid4().hex, "TEST_ONLY")
    recorder.event("calibration", operator_confirmed=True, reference_source="TEST_ONLY", calibration_file="TEST_ONLY_no_sensor")
    for order in balanced_orders(2, seed):
        pair = recorder.pair(order)
        for controller in (("Clock", "Compass") if order == "AB" else ("Compass", "Clock")):
            recorder.event("result", pair_id=pair["pair_id"], trial_id=pair[f"{controller.lower()}_trial_id"], controller=controller,
                           operator_confirmed=True, reference_source="TEST_ONLY", success=True)
    hardware = MockHardware()
    config = ArmConfig("TEST_ONLY", "TEST_ONLY", "TEST_ONLY", 1, .1, dict.fromkeys(CHECKS, True))
    with SafetyGuard(hardware, config, True, True):
        pass
    return {"label": "TEST_ONLY", "experiment": experiment, "motor_commands": len(hardware.commands), "stopped": hardware.stopped,
            "note": "Synthetic lifecycle only; no research CSV or physical observation generated"}


def live_hardware(config: dict, enable: bool, arm: bool) -> None:
    arm_config = ArmConfig(**config["arming"])
    with SafetyGuard(MockHardware(), arm_config, enable, arm):
        raise RuntimeError("Live driver unavailable: commission wiring, feedback, independent power-cut e-stop and hardware watchdog, then implement a reviewed adapter. No output was enabled.")
