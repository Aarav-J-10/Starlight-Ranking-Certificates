"""Prespecified failure codes and descriptive event labels, not causal proof."""
FAILURES=('SUCCESS','F01_WALL_COLLISION','F02_OBSTACLE_COLLISION',
 'F03_WRONG_SIDE_PASS','F04_STATE_ERROR','F05_TIMEOUT','F06_PARKING_FAILURE',
 'F07_CONTROL_INSTABILITY','F08_PERCEPTION_LOSS')
# Legacy field name ``causal_chain`` is retained by the mission API for file
# compatibility. These labels state observed events only: a missing target can
# co-occur with collision without demonstrating that perception caused it.
CHAINS=('none','early_handoff_with_course_event_count',
 'pillar_contact;current_target_status_recorded_separately',
 'wall_contact_or_motion_limit','pillar_plane_crossing_on_wrong_side',
 'parking_phase_timeout_or_geometric_failure',
 'wall_evidence_loss_then_persistent_dropout','course_or_handoff_requirement_unmet')
