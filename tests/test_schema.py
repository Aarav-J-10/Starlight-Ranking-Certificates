from datetime import datetime, timezone

import pytest

from starlight.analysis import DATASETS


def fresh(schema, name):
    key = DATASETS[name][0]
    row = dict(schema.read(key)[0])
    if "timestamp" in row:
        row["timestamp"] = datetime.now(timezone.utc).isoformat()
    return key, row


@pytest.mark.parametrize("name,column,value", [
    ("wp1", "motor_cut_confirmed", 2), ("wp1", "cut_latency_ms", None),
    ("wp2-steering", "servo_command", 106), ("wp2-steering", "battery_voltage_V", "nan"),
    ("wp2-latency", "missed_33ms", 1), ("wp2-latency", "latency_ms", float("inf")),
    ("wp3", "aruco_id_left", 9), ("wp3", "position_error_mm", -1),
    ("wp5", "clock_success", 100), ("wp6", "agreement", 0),
    ("wp7", "phase", "A_prime_restore"), ("wp8", "n_correct", 999),
    ("wp8", "accuracy", .12345), ("d1", "outcome", "wrong"),
    ("primary-grid", "n_pairs", 0), ("primary-grid", "delta_pp", 99),
    ("primary-grid", "certificate_label", "Clock"), ("primary-grid", "ci_low_pp", 101),
    ("model-forms", "missions_executed_additional", 8000), ("attribution", "variance_share", 1.1),
])
def test_bad_measurements_rejected(schema, name, column, value):
    key, row = fresh(schema, name)
    row[column] = value
    with pytest.raises(ValueError):
        schema.validate(key, [row])


@pytest.mark.parametrize("name", list(DATASETS))
def test_duplicate_ids_rejected(schema, name):
    key, row = fresh(schema, name)
    with pytest.raises(ValueError):
        schema.validate(key, [row, row])


def test_headers_case_and_order(schema, tmp_path):
    key, row = fresh(schema, "wp1")
    target = tmp_path / "fresh.csv"
    schema.export(key, [row], target)
    assert target.read_text().splitlines()[0] == ",".join(schema.spec[key]["columns"])
    with pytest.raises(FileExistsError):
        schema.export(key, [row], target)
    with pytest.raises(ValueError):
        schema.validate(key, [dict(row, Timestamp=row["timestamp"])])


def test_fresh_vs_archived_and_timestamp(schema):
    key, row = fresh(schema, "wp1")
    assert len(schema.validate(key, [row])) == 1
    with pytest.raises(ValueError, match="row count"):
        schema.validate(key, [row], archived=True)
    row["timestamp"] = "2026-11-01 12:00:00"
    with pytest.raises(ValueError, match="timezone"):
        schema.validate(key, [row])


def test_incomplete_or_mismatched_pair(schema):
    key = DATASETS["wp4"][0]
    rows = schema.read(key)[:2]
    for row in rows:
        row["timestamp"] = datetime.now(timezone.utc).isoformat()
    with pytest.raises(ValueError, match="incomplete"):
        schema.validate(key, rows[:1])
    rows[1]["order"] = "BA"
    with pytest.raises(ValueError, match="inconsistent"):
        schema.validate(key, rows)
