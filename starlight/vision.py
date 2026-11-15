from datetime import datetime, timezone
import json
import math
from pathlib import Path

from .schema import require


def frame_errors(image: Path, calibration: Path, reference: dict, captured_at: str, frame_idx: int, point_id: str, quality: dict) -> dict:
    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise ImportError('Camera analysis needs: python -m pip install -e ".[vision]"') from error
    config = json.loads(calibration.read_text(encoding="utf-8"))
    for key in ("revision", "camera_matrix", "distortion", "image_size", "image_to_plane_mm", "marker_size_mm", "dictionary", "coordinate_system", "survey_confirmed"):
        require(key in config, f"Missing camera calibration {key}")
    require(config["survey_confirmed"] is True and config["marker_size_mm"] > 0, "Survey/marker size unconfirmed")
    stamp = datetime.fromisoformat(captured_at)
    require(stamp.utcoffset() is not None, "Capture time needs timezone")
    age = (datetime.now(timezone.utc) - stamp).total_seconds()
    require(0 <= age <= quality["max_age_s"], "Stale/future capture timestamp")
    require(quality["exposure_verified"] is True and quality["rolling_shutter_verified"] is True, "Exposure/rolling-shutter check required")
    pixels = cv2.imread(str(image))
    require(pixels is not None, "Unreadable image")
    require(list(pixels.shape[1::-1]) == config["image_size"], "Calibration image-size mismatch")
    gray = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
    require(float(np.mean(gray >= 250)) <= quality["max_saturated_fraction"], "Glare/saturation rejection")
    require(float(cv2.Laplacian(gray, cv2.CV_64F).var()) >= quality["min_laplacian_variance"], "Blur rejection")
    matrix, distortion = np.asarray(config["camera_matrix"], float), np.asarray(config["distortion"], float)
    require(matrix.shape == (3, 3) and np.isfinite(matrix).all() and np.isfinite(distortion).all(), "Invalid camera intrinsics")
    corrected = cv2.undistort(pixels, matrix, distortion)
    require(hasattr(cv2.aruco, config["dictionary"]), "Unknown ArUco dictionary")
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, config["dictionary"]))
    corners, ids, _ = cv2.aruco.ArucoDetector(dictionary).detectMarkers(corrected)
    found = [] if ids is None else ids.flatten().tolist()
    require(found.count(10) == found.count(11) == 1, "Missing, occluded or duplicate marker 10/11")
    homography = np.asarray(config["image_to_plane_mm"], float)
    require(homography.shape == (3, 3) and np.isfinite(homography).all() and abs(np.linalg.det(homography)) > 1e-12, "Invalid plane homography")
    centers = []
    for marker in (10, 11):
        center = corners[found.index(marker)][0].mean(axis=0)
        projected = homography @ np.array([*center, 1.0])
        require(abs(projected[2]) > 1e-12, "Marker outside calibrated plane")
        centers.append(projected[:2] / projected[2])
    left, right = centers
    require(np.linalg.norm(right - left) > 0, "Coincident markers")
    position = (left + right) / 2
    heading = math.degrees(math.atan2(*(right - left)[::-1]))
    require(len(reference["position_mm"]) == 2 and all(math.isfinite(x) for x in [*reference["position_mm"], reference["heading_deg"]]), "Invalid surveyed reference")
    return {"point_id": point_id, "frame_idx": frame_idx, "position_error_mm": float(np.linalg.norm(position - reference["position_mm"])),
            "heading_error_deg": abs((heading - reference["heading_deg"] + 180) % 360 - 180),
            "aruco_id_left": 10, "aruco_id_right": 11, "timestamp": stamp.isoformat()}


def classify_colour(hsv: tuple[float, float, float], thresholds: dict[str, tuple[list, list]]) -> str:
    require(len(hsv) == 3 and all(math.isfinite(x) for x in hsv), "Invalid HSV features")
    matches = []
    for name, (low, high) in thresholds.items():
        require(len(low) == len(high) == 3 and all(math.isfinite(a) and math.isfinite(b) and a <= b for a, b in zip(low, high)), "Invalid colour thresholds")
        if all(a <= x <= b for x, a, b in zip(hsv, low, high)):
            matches.append(name)
    return matches[0] if len(matches) == 1 else "recheck"
