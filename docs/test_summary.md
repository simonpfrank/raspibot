# Test Summary

## Smart Room Scanner Tests

### Unit Tests (`tests/unit/test_core/test_smart_room_scanner.py`)

#### Initialization
- `test_init_creates_components` - Scanner initializes all components correctly
- `test_init_with_custom_scan_interval` - Scanner accepts custom scan interval

#### Scan Cycle (No People)
- `test_no_people_returns_to_center` - Returns to center when no people found
- `test_no_people_returns_empty_list` - Returns empty detection list when no people

#### Scan Cycle (With People)
- `test_early_stop_when_people_detected` - Stops scanning early once people detected
- `test_heat_map_updated_on_detection` - Heat map updated when people detected
- `test_enters_watch_mode_after_detection` - Enters watch mode after finding people
- `test_optimal_position_calculated` - Calculates optimal position for detected people

#### Position Ordering
- `test_center_positions_scanned_first_without_heat` - Center positions prioritized without heat
- `test_heat_prioritizes_positions` - Heat history influences position priority

#### Watch Phase
- `test_watch_update_adjusts_position` - Watch update adjusts camera position

#### Filtering
- `test_filters_non_person_detections` - Non-person detections filtered out
- `test_filters_low_confidence_detections` - Low confidence detections filtered

#### Heat Map Persistence
- `test_saves_heat_map_after_scan` - Heat map saved after scan cycle

#### Face Tilt Adjustment (Phase B)
- `test_person_at_top_no_face_returns_negative_adjustment` - Returns negative tilt for face cutoff
- `test_person_at_top_with_partial_face_returns_smaller_adjustment` - Partial face gets smaller adjustment
- `test_person_not_at_top_returns_none` - No adjustment when person not at top
- `test_person_at_top_with_face_not_at_edge_returns_none` - No adjustment when face visible
- `test_adjustment_uses_fov_for_calculation` - FOV used correctly in calculation

#### Face Detection Integration (Phase B)
- `test_includes_empty_faces_list_when_no_faces` - Empty faces list when no faces
- `test_includes_faces_associated_with_person` - Faces associated with person box
- `test_does_not_associate_face_outside_person_box` - Faces outside box not associated

#### Tilt Nudge in Scan Cycle (Phase B)
- `test_applies_tilt_nudge_when_face_at_top` - Tilt nudge applied for face cutoff
- `test_no_tilt_nudge_when_face_visible` - No nudge when face visible
- `test_detection_result_includes_faces` - Detections include face data

**Total Unit Tests: 25 passing**

### Integration Tests (`tests/integration/test_smart_scanner_integration.py`)

#### Heat Map Integration
- `test_heat_map_persistence_roundtrip` - Heat map survives save/load cycle
- `test_heat_map_ordering_with_real_data` - Position ordering works with accumulated heat

#### Position Calculator Integration
- `test_calculates_optimal_for_clustered_people` - Finds optimal position for clusters
- `test_clusters_spread_people_correctly` - Clusters people spread beyond FOV

#### Watch Controller Integration
- `test_watch_controller_adjusts_servo` - Sends correct commands to servo
- `test_watch_controller_respects_deadband` - Respects deadband for small offsets

#### Smart Room Scanner Integration
- `test_scan_cycle_with_single_person` - Full cycle with single person
- `test_scan_cycle_with_no_people` - Full cycle with no people returns to center
- `test_scan_cycle_filters_non_person_detections` - Filters non-person detections
- `test_heat_map_updated_after_detection` - Heat map updated and saved
- `test_multiple_scan_cycles_accumulate_heat` - Heat accumulates over cycles
- `test_watch_update_after_scan` - Watch update works after scan cycle

#### End-to-End Scenarios
- `test_scenario_person_tracking_session` - Complete tracking session simulation

#### Face Detection Integration (Phase B)
- `test_scan_returns_detections_with_faces` - Detections include face data
- `test_scan_applies_tilt_nudge_when_face_cut_off` - Tilt nudge applied for cutoff
- `test_scan_no_tilt_nudge_when_face_visible` - No nudge when face visible
- `test_face_outside_person_not_associated` - Faces outside box not associated
- `test_multiple_people_with_faces` - Multiple people get correct faces

**Total Integration Tests: 18 passing**

---

## Other Test Files

### HeatMap Unit Tests (`tests/unit/test_core/test_heat_map.py`)
- 21 tests covering heat recording, decay, persistence, ordering

### Position Calculator Unit Tests (`tests/unit/test_core/test_position_calculator.py`)
- 19 tests covering single/multiple people, clustering, edge cases

### Watch Controller Unit Tests (`tests/unit/test_core/test_watch_controller.py`)
- 16 tests covering watching state, adjustments, deadband, boundaries
- 7 tests for pan_to_keep_in_frame (Phase C)

---

## Phase C: Event-Driven Tracking Tests

### TrackingEvents Unit Tests (`tests/unit/test_core/test_tracking_events.py`)

#### EdgePosition
- `test_edge_position_values` - EdgePosition enum has all required values
- `test_edge_position_is_critical` - is_critical returns True only for critical positions
- `test_edge_position_is_warning` - is_warning returns True for warning and critical
- `test_edge_position_direction` - direction returns left/right/None

#### TrackingEvent
- `test_create_tracking_event` - TrackingEvent can be created with timestamp and track_id
- `test_tracking_event_immutable` - TrackingEvent is frozen (immutable)

#### EdgeEvent
- `test_create_edge_event` - EdgeEvent can be created with all required fields
- `test_edge_event_inherits_tracking_event` - EdgeEvent is a TrackingEvent
- `test_edge_event_critical_values` - EdgeEvent with critical edge position

#### ExitEvent
- `test_create_exit_event` - ExitEvent can be created with all required fields
- `test_exit_event_inherits_tracking_event` - ExitEvent is a TrackingEvent
- `test_exit_event_directions` - ExitEvent exit_direction can be left or right

#### NewPersonEvent
- `test_create_new_person_event` - NewPersonEvent with all fields
- `test_new_person_event_inherits_tracking_event` - NewPersonEvent is a TrackingEvent
- `test_new_person_event_no_entry_edge` - entry_edge can be None
- `test_new_person_event_with_entry_edges` - entry_edge can be left/right

**Total: 16 tests**

### TrackingState Unit Tests (`tests/unit/test_core/test_tracking_state.py`)

#### TrackingStatus
- `test_status_values` - TrackingStatus enum has all required values
- `test_is_trackable` - is_trackable returns True for active/missing/reacquiring

#### TrackedPerson
- `test_create_tracked_person` - TrackedPerson with all fields
- `test_tracked_person_with_exit_direction` - TrackedPerson can have exit_direction
- `test_tracked_person_is_near_edge` - is_near_edge returns True for edge positions
- `test_tracked_person_should_trigger_exit` - should_trigger_exit logic

#### TrackingState
- `test_create_empty_tracking_state` - TrackingState can be created empty
- `test_create_tracking_state_with_people` - TrackingState with tracked people
- `test_add_person` - add_person adds to tracking
- `test_remove_person` - remove_person removes from tracking
- `test_update_person` - update_person replaces tracked person
- `test_get_active_people` - get_active_people returns trackable people
- `test_get_primary_target` - get_primary_target returns primary person
- `test_get_primary_target_none` - returns None when no primary
- `test_should_trigger_full_sweep_no_people` - True when no active people
- `test_should_trigger_full_sweep_all_lost` - True when all people lost
- `test_should_trigger_full_sweep_has_active` - False when active people exist
- `test_set_primary_target` - sets primary target ID
- `test_set_primary_target_invalid` - raises error for non-existent ID

**Total: 19 tests**

### EventTracker Unit Tests (`tests/unit/test_core/test_event_tracker.py`)

#### Initialization
- `test_create_event_tracker` - EventTracker with defaults
- `test_create_event_tracker_custom_size` - EventTracker with custom frame size
- `test_create_event_tracker_custom_thresholds` - EventTracker with custom thresholds

#### Edge Position Calculation
- `test_center_position` - Box in center returns CENTER
- `test_left_warning_position` - Box near left edge returns LEFT_WARNING
- `test_left_critical_position` - Box very near left returns LEFT_CRITICAL
- `test_right_warning_position` - Box near right returns RIGHT_WARNING
- `test_right_critical_position` - Box very near right returns RIGHT_CRITICAL

#### Velocity Estimation
- `test_estimate_velocity_no_history` - Zero velocity with no history
- `test_estimate_velocity_single_position` - Zero velocity with one position
- `test_estimate_velocity_moving_right` - Positive velocity when moving right
- `test_estimate_velocity_moving_left` - Negative velocity when moving left
- `test_estimate_velocity_diagonal` - Captures diagonal movement

#### Edge Event Detection
- `test_detect_edge_event_center` - No event for person in center
- `test_detect_edge_event_warning` - Event generated for person near edge
- `test_detect_edge_event_critical` - Critical event for person very near edge
- `test_detect_multiple_edge_events` - Multiple events for multiple people

#### Exit Event Detection
- `test_no_exit_event_first_frame` - No exit on first frame
- `test_exit_event_after_missing_frames` - Exit after missing 3+ frames
- `test_no_exit_event_center_missing` - No exit when person disappears from center

#### New Person Event Detection
- `test_new_person_first_detection` - New person event on first detection
- `test_new_person_at_edge` - Entry edge set when near edge
- `test_no_new_person_existing_track` - No new person for existing track

#### Update Method
- `test_update_returns_events` - Update returns list of events
- `test_update_tracks_positions` - Update tracks position history
- `test_update_increments_missing_frames` - Increments missing when not detected

#### Re-acquisition
- `test_attempt_reacquisition` - Returns pan direction
- `test_reacquisition_limited_attempts` - Fails after max attempts

#### Tracking State Access
- `test_get_tracking_state` - Can access tracking state
- `test_tracking_state_updates` - Tracking state updates with detections

**Total: 30 tests**

### SmartRoomScanner Event-Driven Mode Unit Tests

#### Event-Driven Mode Init
- `test_event_tracker_created` - Scanner creates EventTracker component
- `test_inactivity_timeout_configurable` - Inactivity timeout can be configured

#### Event-Driven Watch
- `test_run_event_driven_watch_processes_detections` - Processes camera detections
- `test_edge_event_triggers_pan` - Edge event triggers preemptive pan
- `test_returns_to_scan_when_all_lost` - Indicates sweep needed when all lost

#### Handle Tracking Event
- `test_handle_edge_event_calls_pan` - Edge event calls pan_to_keep_in_frame
- `test_handle_exit_event_attempts_reacquisition` - Exit event attempts re-acquisition
- `test_handle_new_person_event_records_to_heatmap` - New person recorded to heat map

**Total: 8 tests**

### HeatMap record_event Unit Tests
- `test_record_event_detection` - Detection event increases heat
- `test_record_event_exit_lower_weight` - Exit events have lower weight
- `test_record_event_entry_medium_weight` - Entry events have medium weight
- `test_record_event_unknown_type_uses_default` - Unknown types use default
- `test_record_event_updates_count` - Recording events increments count
- `test_record_event_confidence_scales_weight` - Confidence scales weight

**Total: 6 tests**

### Event-Driven Tracking Integration Tests (`tests/integration/test_event_driven_tracking.py`)

#### Full Integration
- `test_full_tracking_cycle_person_enters_watches_exits` - Complete tracking cycle
- `test_preemptive_pan_keeps_person_in_frame` - Pan keeps person in frame
- `test_multiple_people_one_exits` - Continue tracking when one exits
- `test_heat_map_learns_from_events` - Heat map records events

#### EventTracker Integration
- `test_velocity_estimation_accuracy` - Velocity estimation accurate
- `test_edge_detection_thresholds` - Edge detection respects thresholds
- `test_exit_confirmation_requires_multiple_frames` - Exit requires multiple frames
- `test_new_person_event_only_fires_once` - New person event only once

#### WatchController Integration
- `test_pan_scales_with_edge_severity` - Pan scales with severity
- `test_pan_respects_servo_limits` - Pan respects limits

#### Full System
- `test_scan_to_watch_to_rescan_cycle` - Complete scan-watch-rescan cycle

**Total: 11 tests**

---

**Grand Total Phase C: 97 tests (86 unit + 11 integration)**

---

## Foundation Motion Patterns Tests (Phases 1-4)

### ServoName Enum (`tests/unit/test_hardware/test_servos/test_servo_types.py`)

- `test_pan_value` - PAN enum has value "pan"
- `test_tilt_value` - TILT enum has value "tilt"
- `test_only_two_members` - ServoName has exactly two members
- `test_config_lookup_by_enum` - SERVO_CONFIGS can be looked up with enum values
- `test_enum_from_string` - ServoName can be created from string
- `test_invalid_name_raises` - Invalid string raises ValueError

**Total: 6 tests**

### ServoControllerProtocol (`tests/unit/test_hardware/test_servos/test_servo_protocol.py`)

- `test_protocol_is_runtime_checkable` - Protocol is runtime_checkable
- `test_mock_satisfies_protocol` - Mock with correct methods satisfies protocol
- `test_protocol_requires_set_servo_angle` - Missing set_servo_angle fails isinstance
- `test_protocol_requires_get_servo_angle` - Missing get_servo_angle fails isinstance
- `test_protocol_requires_smooth_move_to_angle` - Missing smooth_move fails isinstance
- `test_complete_implementation_satisfies_protocol` - Complete class satisfies protocol

**Total: 6 tests**

### Interpolation Functions (`tests/unit/test_movement/test_interpolation.py`)

#### Linear
- `test_start` - Linear at t=0 returns 0
- `test_end` - Linear at t=1 returns 1
- `test_midpoint` - Linear at t=0.5 returns 0.5
- `test_quarter` - Linear at t=0.25 returns 0.25
- `test_monotonic` - Linear is monotonically increasing

#### Minjerk
- `test_start` - Minjerk at t=0 returns 0
- `test_end` - Minjerk at t=1 returns 1
- `test_midpoint` - Minjerk at t=0.5 returns 0.5
- `test_monotonic` - Minjerk is monotonically increasing
- `test_slow_start` - Minjerk starts slow (value near 0 at t=0.1)
- `test_slow_end` - Minjerk ends slow (value near 1 at t=0.9)
- `test_symmetric` - Minjerk is symmetric: f(t) + f(1-t) = 1

#### Ease-in-out
- `test_start` - Ease-in-out at t=0 returns 0
- `test_end` - Ease-in-out at t=1 returns 1
- `test_midpoint` - Ease-in-out at t=0.5 returns 0.5
- `test_monotonic` - Ease-in-out is monotonically increasing
- `test_slow_start` - Ease-in-out starts slow
- `test_slow_end` - Ease-in-out ends slow

#### Dispatch
- `test_linear_dispatch` - interpolate with LINEAR dispatches to linear()
- `test_minjerk_dispatch` - interpolate with MINJERK dispatches to minjerk()
- `test_ease_in_out_dispatch` - interpolate with EASE_IN_OUT dispatches to ease_in_out()
- `test_default_is_linear` - Default method is LINEAR

#### Enum
- `test_three_methods` - Enum has exactly three methods
- `test_values` - Enum values are meaningful strings

**Total: 24 tests**

### MotionOffset + OffsetComposer (`tests/unit/test_movement/test_motion_offset.py`)

#### MotionOffset
- `test_default_values` - Default offset is zero for both axes
- `test_custom_values` - Stores given pan and tilt
- `test_immutable` - Frozen (immutable) dataclass
- `test_add_zero` - Adding zero offset returns same values
- `test_add_positive_negative` - Adding positive and negative offsets
- `test_add_commutative` - Addition is commutative
- `test_add_returns_new_instance` - Addition returns new instance

#### OffsetComposer
- `test_no_offsets_returns_base` - Resolve returns base with no offsets
- `test_one_offset_adds_to_base` - Single offset adds to base
- `test_multiple_offsets_sum` - Multiple offsets are summed
- `test_clear_offset` - Clearing removes offset from computation
- `test_clear_nonexistent_offset_safe` - Clearing non-existent is safe
- `test_clamp_pan_max` - Pan clamped to upper limit
- `test_clamp_pan_min` - Pan clamped to lower limit
- `test_clamp_tilt_max` - Tilt clamped to upper limit
- `test_clamp_tilt_min` - Tilt clamped to lower limit
- `test_replace_offset` - Same-name offset replaces previous
- `test_default_base_is_zero` - Default base is (0, 0)
- `test_active_layers` - Can query active offset layer names

**Total: 19 tests**

### SequencePlayer + MotionSequence (`tests/unit/test_movement/test_sequence.py`)

#### SequenceStep
- `test_create_step` - Stores target, duration, and method
- `test_immutable` - Frozen dataclass

#### MotionSequence
- `test_create_sequence` - Stores name and steps
- `test_total_duration` - Total duration is sum of step durations

#### SequencePlayer
- `test_not_complete_before_start` - Not complete before starting
- `test_evaluate_at_start` - At t=0 offset is zero
- `test_evaluate_at_mid` - At midpoint offset is half target (linear)
- `test_evaluate_at_end` - At end offset equals target
- `test_is_complete_after_end` - Complete after total duration
- `test_evaluate_after_complete_returns_zero` - Zero offset after completion
- `test_two_step_first_half` - First step interpolates correctly
- `test_two_step_transition` - Step boundary returns first step target
- `test_two_step_second_half` - Second step interpolates from first target
- `test_two_step_end` - End of two-step equals last target
- `test_minjerk_produces_nonlinear_curve` - Minjerk offset is non-linear
- `test_start_with_offset_time` - Can start at non-zero time

**Total: 16 tests**

### Gestures (`tests/unit/test_movement/test_gestures.py`)

#### Definitions
- `test_nod_is_motion_sequence` - NOD is a MotionSequence
- `test_nod_name` - NOD named "nod"
- `test_nod_uses_tilt` - NOD uses tilt axis only
- `test_shake_is_motion_sequence` - SHAKE is a MotionSequence
- `test_shake_name` - SHAKE named "shake"
- `test_shake_uses_pan` - SHAKE uses pan axis only
- `test_shake_returns_to_zero` - SHAKE ends at zero
- `test_attention_is_motion_sequence` - ATTENTION is a MotionSequence
- `test_attention_name` - ATTENTION named "attention"
- `test_attention_returns_to_zero` - ATTENTION ends at zero

#### Playback
- `test_nod_produces_tilt_offset` - Playing NOD produces tilt offset
- `test_shake_produces_pan_offset` - Playing SHAKE produces pan offset
- `test_all_gestures_complete` - All gestures complete after total duration

**Total: 13 tests**

---

**Grand Total Foundation Motion: 84 tests passing**
**Grand Total All Phases: 243+ tests passing**
