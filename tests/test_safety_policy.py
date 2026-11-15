import json
import time

import pytest

from starlight.acquisition import ArmConfig, CHECKS, Recorder, SafetyGuard, balanced_orders, live_hardware
from starlight.controllers import Clock, Compass, MockHardware
from starlight.decision import PolicyConfig, decide


@pytest.fixture
def arming():
    return ArmConfig("operator", "rev1", "rev1", 1, .2, dict.fromkeys(CHECKS, True))


def test_stop_on_timeout_estop_and_exception(arming):
    hw, now = MockHardware(), [0.0]
    with SafetyGuard(hw, arming, True, True, lambda: now[0]) as guard:
        guard.command(75, .1)
        now[0] = 2
        with pytest.raises(ValueError, match="timeout"):
            guard.command(75, .1)
        assert hw.stopped
    with pytest.raises(RuntimeError):
        with SafetyGuard(hw, arming, True, True) as guard:
            guard.command(75, .1)
            raise RuntimeError("TEST_ONLY failure")
    assert hw.stopped
    hw.estop = True
    with pytest.raises(ValueError, match="E-stop"):
        with SafetyGuard(hw, arming, True, True):
            pass
    assert hw.stopped


@pytest.mark.parametrize("enable,armed", [(False, False), (True, False), (False, True)])
def test_explicit_arm_required(arming, enable, armed):
    hw = MockHardware()
    with pytest.raises(ValueError):
        with SafetyGuard(hw, arming, enable, armed):
            pass
    assert hw.stopped and not hw.commands


def test_stale_config_and_limits(arming):
    hw = MockHardware()
    stale = ArmConfig("operator", "rev1", "rev0", 1, .2, arming.checks)
    with pytest.raises(ValueError, match="stale"):
        with SafetyGuard(hw, stale, True, True):
            pass
    with SafetyGuard(hw, arming, True, True) as guard:
        with pytest.raises(ValueError, match="limits"):
            guard.command(106, .3)
    assert hw.stopped and not hw.commands


def test_live_stub_fails_even_when_armed(arming):
    from dataclasses import asdict
    with pytest.raises(RuntimeError, match="unavailable"):
        live_hardware({"arming": asdict(arming)}, True, True)


def test_recorder_lineage_and_append_only(tmp_path):
    recorder = Recorder(tmp_path, "TEST_ONLY", "session", "rev1")
    with pytest.warns(UserWarning, match="Video"):
        first = recorder.event("calibration", calibration_file="TEST_ONLY", operator_confirmed=True, reference_source="TEST_ONLY")
    pair = recorder.pair("AB")
    fields = dict(pair_id=pair["pair_id"], trial_id=pair["clock_trial_id"], controller="Clock", operator_confirmed=True, reference_source="TEST_ONLY", success=True)
    with pytest.warns(UserWarning):
        last = recorder.event("result", **fields)
    assert last["monotonic_ns"] >= first["monotonic_ns"]
    assert last["event_index"] > first["event_index"]
    assert last["wall_time_iso8601"].endswith("+00:00")
    with pytest.raises(ValueError, match="completed"):
        recorder.event("result", **fields)
    with pytest.raises(ValueError, match="append-only"):
        Recorder(tmp_path, "TEST_ONLY", "session", "rev1")
    assert len((tmp_path / "events.jsonl").read_text().splitlines()) == 2


def test_invalid_pair_and_clock_override(tmp_path):
    recorder = Recorder(tmp_path, "TEST_ONLY", "session", "rev1")
    with pytest.raises(ValueError, match="calibration"):
        recorder.event("measurement", operator_confirmed=True, reference_source="TEST_ONLY")
    with pytest.warns(UserWarning):
        recorder.event("calibration", calibration_file="TEST_ONLY", operator_confirmed=True, reference_source="TEST_ONLY")
    with pytest.raises(ValueError, match="Unknown pair"):
        recorder.event("result", pair_id="missing", operator_confirmed=True, reference_source="TEST_ONLY")
    with pytest.raises(ValueError, match="replace"):
        recorder.event("measurement", monotonic_ns=1, operator_confirmed=True, reference_source="TEST_ONLY")
    assert balanced_orders(12, 2).count("AB") == 6
    assert balanced_orders(12, 2) == balanced_orders(12, 2)


@pytest.mark.parametrize("difference,a,d,action", [
    ((1, 3), (.96, .99), (.9, .94), "select_A"),
    ((-3, -1), (.9, .94), (.96, .99), "select_D"),
    ((-.4, .4), (.96, .99), (.96, .99), "accept_either"),
    ((-3, 3), (.7, .8), (.7, .8), "reject_both"),
    ((-3, 3), (.96, .99), (.96, .99), "request_more"),
    ((1, 3), (.8, .99), (.8, .99), "request_more"),
])
def test_five_actions(difference, a, d, action):
    result = decide(difference, a, d, PolicyConfig(.95, .5, 1, 10, 5))
    assert result["action"] == action
    assert result["trace"]


def test_missing_config_invalid_units_and_budget():
    with pytest.raises(ValueError, match="insufficient_configuration"):
        decide((-1, 1), (.9, 1), (.9, 1), None)
    with pytest.raises(ValueError):
        PolicyConfig(float("nan"), .5, 1, 2, 3)
    config = PolicyConfig(.95, .5, 10, 3, 1)
    assert not decide((-1, 1), (.9, 1), (.9, 1), config)["testing_permitted"]
    with pytest.raises(ValueError, match="interval"):
        decide((1, -1), (.9, 1), (.9, 1), config)


def test_controller_plans_do_not_actuate():
    assert Clock(2, 90).command(1) == 90
    assert Clock(2, 90).command(2) == 75
    assert Compass(0, 1, 1, .5).command(359) == 76
    assert Compass(0, 1, 1, .5).command(0) == 75
