from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from starlight.acquisition import Recorder, export_pairs
from starlight.vision import classify_colour, frame_errors


def test_real_observation_lineage_exports_share_ids(schema, tmp_path):
    calibration = tmp_path / "calibration.json"
    calibration.write_text('{"label":"TEST_ONLY_CALIBRATION_FIXTURE"}')
    video = tmp_path / "video.txt"
    video.write_text("TEST_ONLY_FILE_PRESENCE_FIXTURE")
    recorder = Recorder(tmp_path / "run", "NEW_TEST_STUDY", "NEW_TEST_SESSION", "rev1", {"operator": "TEST_ONLY_OPERATOR"})
    recorder.event("calibration", calibration_file=str(calibration), operator_confirmed=True, reference_source="manual", video_path=str(video))
    recorded_manifest = json.loads((recorder.directory / "run_manifest.json").read_text())
    assert Path(recorded_manifest["calibration_file"]).read_bytes() == calibration.read_bytes()
    pair = recorder.pair("BA")
    for controller in ("Compass", "Clock"):
        recorder.event("result", pair_id=pair["pair_id"], trial_id=pair[f"{controller.lower()}_trial_id"], controller=controller,
                       success=controller == "Compass", fail_reason="TEST_ONLY_FAILURE", heading_shift_deg=1.2, battery_V=12,
                       operator_confirmed=True, reference_source="manual", video_path=str(video))
    exported = export_pairs(recorder, schema, "mismatch")
    assert exported["pair_ids"] == [pair["pair_id"]]
    files = list((recorder.directory / "csv").rglob("*.csv"))
    assert len(files) == 3
    d1 = next(p for p in files if p.name == "shared_failure_60pair.csv").read_text()
    assert pair["pair_id"] in d1 and "clock_only" in d1
    assert "2026-11-01" not in d1


def test_test_only_observations_cannot_be_exported(schema, tmp_path):
    recorder = Recorder(tmp_path, "TEST_ONLY", "session", "revision")
    with pytest.warns(UserWarning):
        recorder.event("calibration", calibration_file="TEST_ONLY", reference_source="TEST_ONLY", operator_confirmed=True)
    with pytest.raises(ValueError, match="TEST_ONLY"):
        export_pairs(recorder, schema, "matched")


def test_real_observations_require_operator_metadata(tmp_path):
    recorder = Recorder(tmp_path, "NEW_TEST_STUDY", "session", "revision")
    with pytest.raises(ValueError, match="operator metadata"):
        recorder.event("calibration", calibration_file="TEST_ONLY", reference_source="manual", operator_confirmed=True)
    assert recorder.events_path.read_text() == ""


def test_colour_thresholds_require_unique_match():
    thresholds = {"red": ([0, 100, 100], [10, 255, 255]), "blue": ([100, 100, 100], [130, 255, 255])}
    assert classify_colour((5, 200, 200), thresholds) == "red"
    assert classify_colour((50, 200, 200), thresholds) == "recheck"
    with pytest.raises(ValueError):
        classify_colour((float("nan"), 0, 0), thresholds)


def test_calibrated_aruco_pipeline_and_rejections(tmp_path):
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    image = np.full((400, 600, 3), 200, dtype=np.uint8)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    for marker, x in ((10, 100), (11, 400)):
        tile = cv2.aruco.generateImageMarker(dictionary, marker, 100)
        image[150:250, x:x + 100] = cv2.cvtColor(tile, cv2.COLOR_GRAY2BGR)
    path = tmp_path / "TEST_ONLY_markers.png"
    cv2.imwrite(str(path), image)
    config = {"revision": "TEST_ONLY", "camera_matrix": [[600, 0, 300], [0, 600, 200], [0, 0, 1]], "distortion": [0, 0, 0, 0, 0],
              "image_size": [600, 400], "image_to_plane_mm": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "marker_size_mm": 100,
              "dictionary": "DICT_4X4_50", "coordinate_system": "TEST_ONLY_plane_xy_mm", "survey_confirmed": True}
    calibration = tmp_path / "calibration.json"
    calibration.write_text(json.dumps(config))
    quality = {"max_age_s": 60, "exposure_verified": True, "rolling_shutter_verified": True, "max_saturated_fraction": .5, "min_laplacian_variance": 1}
    reference = {"position_mm": [299.5, 199.5], "heading_deg": 0}
    stamp = datetime.now(timezone.utc).isoformat()
    row = frame_errors(path, calibration, reference, stamp, 1, "TEST_ONLY", quality)
    assert row["position_error_mm"] < .1
    assert row["heading_error_deg"] < .1
    stale = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    with pytest.raises(ValueError, match="Stale"):
        frame_errors(path, calibration, reference, stale, 1, "TEST_ONLY", quality)
    with pytest.raises(ValueError, match="Glare"):
        frame_errors(path, calibration, reference, stamp, 1, "TEST_ONLY", dict(quality, max_saturated_fraction=0))
    image[150:250, 400:500] = 200
    cv2.imwrite(str(path), image)
    with pytest.raises(ValueError, match="marker"):
        frame_errors(path, calibration, reference, stamp, 1, "TEST_ONLY", quality)
