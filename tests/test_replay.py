import csv
import json
from pathlib import Path
import subprocess
import sys

import pytest

from starlight.analysis import DATASETS, expected_comparison
from starlight.cli import main
from starlight.reports import snapshot, verify_manifests

KEYS = [key for keys in DATASETS.values() for key in keys]


@pytest.mark.parametrize("key", KEYS)
def test_every_csv(schema, key):
    before = (schema.root / key).read_bytes()
    rows = schema.read(key)
    assert len(rows) == schema.spec[key]["rows"]
    assert list(rows[0]) == schema.spec[key]["columns"]
    assert (schema.root / key).read_bytes() == before


def test_all_expected_leaves(schema, data):
    tables, summaries = data
    checks = expected_comparison(schema, summaries, tables)
    assert len(checks) == 75
    assert all(c["pass"] for c in checks)
    assert summaries["wp1"]["failed_trip_ids"] == ["ES_12"]
    assert summaries["wp3"]["position_pass"] and not summaries["wp3"]["heading_pass"]
    assert summaries["wp5"]["mcnemar"] == "NOT IDENTIFIABLE"
    assert summaries["d1"]["extended"]["shared_failure"]["fraction"] == 160 / 204
    assert summaries["d1"]["detailed"]["shared_failure"]["fraction"] == 18 / 27
    assert summaries["cartpole"]["metadata_only"]
    assert summaries["wp8"]["pooled_correct"] == 588
    assert summaries["wp8"]["pooled_items"] == 673


def test_interval_discrepancies_are_reported(data):
    audits = data[1]["confirmation"]["interval_audit"]
    assert len(audits) == 8
    assert sum(r["common_stress_timestep"] for r in audits) == 6
    by_gain = {r["gain_g"]: r for r in audits if r["common_stress_timestep"]}
    for gain in (1.23, 1.255, 1.28):
        row = by_gain[gain]
        assert row["discrepancy"]
        assert row["recomputed_pp"] == pytest.approx(row["poster_v4_2_pp"], abs=.00051)
    assert not by_gain[1.2]["discrepancy"]
    assert not by_gain[1.26]["discrepancy"]


def test_reference_manifests(schema):
    checks = verify_manifests(schema.contracts.parent, schema.root)
    assert checks["SHA256_manifest.csv"] > 18


def test_cli_replay_and_export(schema, tmp_path):
    before = snapshot(schema.root)
    assert main(["replay", "wp1", "--out", str(tmp_path)]) == 0
    run = next((tmp_path / "wp1").iterdir())
    summary = json.loads((run / "wp1/summary.json").read_text())
    assert summary["timed_denominator"] == 23
    assert (run / "wp1/figures/summary.svg").is_file()
    key = DATASETS["wp1"][0]
    assert (run / "wp1/csv" / key).read_bytes() == (schema.root / key).read_bytes()
    assert snapshot(schema.root) == before


def test_no_dependency_validation(tmp_path):
    result = subprocess.run([sys.executable, "-S", "-m", "starlight", "validate", "all", "--out", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "75 expected metrics" in result.stdout


@pytest.mark.parametrize("args", [["replay", "invalid"], ["replay", "wp1", "--enable-hardware"], ["acquire", "wp1"], ["acquire", "primary-grid", "--dry-run"], ["decision"], ["replay", "--fresh"]])
def test_cli_rejects_unsafe_or_invalid_requests(args):
    assert main(args) == 2


def test_output_protection(schema):
    before = snapshot(schema.root)
    assert main(["replay", "wp1", "--out", str(schema.root)]) == 2
    assert snapshot(schema.root) == before


def test_all_report_paths(schema, data, tmp_path):
    from starlight.reports import write_replay
    tables, summaries = data
    write_replay(schema, tables, summaries, list(DATASETS), tmp_path, expected_comparison(schema, summaries, tables), snapshot(schema.root))
    assert (tmp_path / "INTERVAL_DISCREPANCIES.md").is_file()
    for name in DATASETS:
        assert (tmp_path / name / "summary.json").is_file()
        assert (tmp_path / name / "run_manifest.json").is_file()


def test_policy_cli(capsys):
    assert main(["decision", "--config", "configs/policy.example.json"]) == 0
    assert '"action": "accept_either"' in capsys.readouterr().out


@pytest.mark.parametrize("name", [n for n in DATASETS if n.startswith("wp") or n == "d1"])
def test_physical_dry_run(name, tmp_path):
    with pytest.warns(UserWarning, match="Video"):
        assert main(["acquire", name, "--dry-run", "--out", str(tmp_path)]) == 0
    run = next((tmp_path / name).iterdir())
    summary = json.loads((run / "summary.json").read_text())
    assert summary["label"] == "TEST_ONLY"
    assert summary["motor_commands"] == 0
    assert not list(run.glob("physical/**/*.csv"))
