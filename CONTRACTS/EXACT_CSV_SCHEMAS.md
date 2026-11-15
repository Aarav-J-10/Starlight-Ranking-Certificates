# Canonical CSV contracts (generated directly from the final processed-data ZIP)

Do not reorder, rename, add, or silently remove columns when exporting to a compatible historical CSV format. For new observations, keep the exact historical columns and attach a separate acquisition manifest.

## `evidence/raw_data_index.csv`
- Rows in historical release: 6
- Columns (5), ordered: `asset_id, category, description, location, sha256_or_status`

## `physical/d1/extended_shared_failure_pairs.csv`
- Rows in historical release: 204
- Columns (7), ordered: `pair_id, study_id, session, clock_fail, compass_fail, outcome, timestamp`

## `physical/d1/extended_shared_summary.csv`
- Rows in historical release: 1
- Columns (7), ordered: `dataset, failure_bearing_pairs, both_fail, clock_only, compass_only, shared_fraction, note`

## `physical/d1/shared_failure_60pair.csv`
- Rows in historical release: 60
- Columns (8), ordered: `pair_id, study_id, session, clock_fail, compass_fail, outcome, condition, timestamp`

## `physical/wp1/emergency_stop_trips.csv`
- Rows in historical release: 24
- Columns (8), ordered: `trip_id, study_id, session, button_pressed, motor_cut_confirmed, cut_latency_ms, cohort, timestamp`

## `physical/wp2/latency_events.csv`
- Rows in historical release: 200
- Columns (6), ordered: `event_id, latency_ms, missed_33ms, missed_50ms, session, timestamp`

## `physical/wp2/steering_calibration.csv`
- Rows in historical release: 126
- Columns (7), ordered: `session_id, battery_voltage_V, sweep_direction, servo_command, protractor_angle_deg, AS5600_angle_deg, timestamp`

## `physical/wp3/dock_camera_accuracy.csv`
- Rows in historical release: 105
- Columns (7), ordered: `point_id, frame_idx, position_error_mm, heading_error_deg, aruco_id_left, aruco_id_right, timestamp`

## `physical/wp4/clock_compass_pairs.csv`
- Rows in historical release: 100
- Columns (9), ordered: `pair_id, study_id, session, condition, order, controller, heading_shift_deg, battery_V, timestamp`

## `physical/wp5_wp6/docking_session_summary.csv`
- Rows in historical release: 5
- Columns (5), ordered: `study_id, session, n_pairs, clock_success, compass_success`

## `physical/wp5_wp6/independent_audit.csv`
- Rows in historical release: 10
- Columns (8), ordered: `unit_id, unit_type, decision, reference_outcome, agreement, unsupported_winner, n_pairs_in_unit, timestamp`

## `physical/wp7/linkage_ABA.csv`
- Rows in historical release: 36
- Columns (8), ordered: `phase, rep, measured_gain_response, servo_current_A, clock_heading_shift_deg, compass_heading_shift_deg, as5600_delta_deg, timestamp`

## `physical/wp8/colour_sorter.csv`
- Rows in historical release: 34
- Columns (7), ordered: `batch_id, recipe, condition, n_items, n_correct, accuracy, timestamp`

## `simulation/attribution.csv`
- Rows in historical release: 8
- Columns (3), ordered: `factor, variance_share, note`

## `simulation/cartpole_summary.csv`
- Rows in historical release: 1
- Columns (3), ordered: `experiment, n_episodes, note`

## `simulation/confirmation.csv`
- Rows in historical release: 8
- Columns (13), ordered: `setting_id, gain_g, stress_s, timestep_s, n_pairs, n_plus, n_minus, delta_pp, ci_low_pp, ci_high_pp, certificate_label, missions_executed, note`

## `simulation/model_forms.csv`
- Rows in historical release: 15
- Columns (14), ordered: `model_id, model_form, gain_g, stress_s, timestep_s, is_base_repeat, n_pairs, n_plus, n_minus, delta_pp, ci_low_pp, ci_high_pp, certificate_label, missions_executed_additional`

## `simulation/primary_grid.csv`
- Rows in historical release: 66
- Columns (12), ordered: `condition_id, gain_g, stress_s, timestep_s, n_pairs, n_plus, n_minus, delta_pp, ci_low_pp, ci_high_pp, certificate_label, missions_executed`
