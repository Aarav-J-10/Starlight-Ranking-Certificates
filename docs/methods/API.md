# Future observations

`Recorder(directory, study_id, session_id, configuration_id, metadata)` creates
a new append-only run with `events.jsonl`, `acquisition_pairs.csv` and a run
manifest. Metadata holds the operator, calibration, sensor/pin map, consent,
video/log pointers and apparatus revision. Record a calibration event first;
it copies and hashes the actual calibration file once.

`pair("AB")` or `pair("BA")` generates one pair ID and two unique trial IDs.
`balanced_orders(n, seed)` provides a reproducible balanced schedule for an
operator-approved protocol. A trial event must use its correct controller,
pair and trial IDs. A result requires boolean success and a failure reason
when unsuccessful. Each event needs `operator_confirmed=True` and a source
tag (`hardware`, `camera`, `manual`, or `TEST_ONLY`). Supply battery, start pose,
sensor snapshots, commanded/measured angles, video pointers and measurement
units as event fields when relevant. Timestamps/lineage cannot be overridden.

`export_pairs(recorder, schema, condition)` exports complete new observations
as WP5 session and D1 detailed tables. When every result includes measured
`heading_shift_deg` and `battery_V`, it also exports WP4. These tables share
the new pair/session lineage; no old crosswalk is inferred. It rejects test
events and incomplete pairs. Other fresh experiment rows can use
`Schema.export(key, rows, destination)` with the exact contract. No function
turns aggregate historical rows into pretend trial observations.

`vision.frame_errors(image, calibration, reference, captured_at, frame_idx,
point_id, quality)` processes a real image with ArUco 10/11. Calibration JSON
requires `revision`, `camera_matrix`, `distortion`, `image_size` (width/height),
`image_to_plane_mm` (homography after undistortion), `marker_size_mm`,
`dictionary`, `coordinate_system`, and `survey_confirmed=true`. Reference has
`position_mm` (two values) and `heading_deg`. The chosen planar method uses the
marker-centre midpoint and left-to-right heading; this is not a recovered
historical pose convention. Intrinsics and the homography must describe the
same undistorted image geometry and surveyed plane.

Quality JSON requires operator-verified `exposure_verified` and
`rolling_shutter_verified`, plus `max_age_s`, `max_saturated_fraction` and
`min_laplacian_variance`. Missing/duplicate markers, stale timestamps, wrong
image dimensions, glare, blur and invalid calibrations reject the frame with
a reason. There is no smoothing or silent acceptance-gate repair.

`classify_colour(hsv, thresholds)` uses explicitly supplied HSV ranges. A
missing or ambiguous match returns `recheck`. Fixed versus calibrated ranges
must be supplied and versioned by the operator; historical thresholds are
unknown. Repeated checks and servo routing remain protocol/adapter work.
