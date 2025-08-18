# Comprehensive Unit Test Plan for Raspibot Refactor

## Overview

This document defines all unit tests needed to provide comprehensive coverage of the current Raspibot functionality after a refactor. The goal is to create tests that can be re-run to ensure no functionality is broken as changes are made. Once built the plan will be to create tests with development (possibly TDD)

## Test Coverage Goals

- **Target Coverage**: 90%+ line coverage for all modules
- **Strategy**: Mock all hardware dependencies (GPIO, I2C, camera hardware)
- **Focus**: Test business logic, error handling, edge cases, and API contracts
- **Re-runnable**: All tests must be deterministic and independent

## Test Structure

All tests will be located in `tests/unit/` with structure mirroring the source code:

```
tests/unit/
├── test_hardware/
│   ├── test_servos/
│   │   ├── test_servo.py
│   │   └── test_controller_selector.py
│   └── test_cameras/
│       ├── test_camera.py
│       ├── test_pi_ai_camera.py
│       ├── test_pi_camera.py
│       └── test_usb_camera.py
├── test_vision/
│   ├── test_deduplication.py
│   └── test_search_pattern.py
├── test_movement/
│   └── test_scanner.py
├── test_core/
│   └── test_room_scan.py
├── test_settings/
│   └── test_config.py
├── test_utils/
│   ├── test_helpers.py
│   └── test_logging_config.py
├── test_exceptions.py
└── test_main.py
```

## Detailed Test Specifications

### test_hardware/test_servos/test_servo.py

#### TestUtilityFunctions
- `test_validate_angle_valid_angles` - Test valid angles pass validation
- `test_validate_angle_invalid_angles` - Test invalid angles raise HardwareException
- `test_handle_jitter_zone_in_zone` - Test angles 87-104 are adjusted
- `test_handle_jitter_zone_outside_zone` - Test angles outside zone unchanged
- `test_apply_calibration_normal` - Test calibration offset application
- `test_apply_calibration_clamping` - Test offset clamping to valid range

#### TestSmoothMoveImplementation
- `test_smooth_move_small_diff` - Test no movement for <0.5 degree difference
- `test_smooth_move_normal` - Test step calculation and movement sequence
- `test_smooth_move_speed_limits` - Test speed clamping to 0.1-1.0 range
- `test_smooth_move_angle_validation` - Test invalid target angle handling

#### TestPCA9685ServoController
- `test_init_without_hardware` - Test initialization when Adafruit libs unavailable
- `test_init_with_hardware_mock` - Test successful initialization with mocked hardware
- `test_set_servo_angle_valid` - Test setting valid angles
- `test_set_servo_angle_invalid` - Test invalid angle handling
- `test_set_servo_angle_jitter_zone` - Test jitter zone handling
- `test_get_servo_angle` - Test angle retrieval
- `test_set_calibration_offset` - Test calibration offset setting
- `test_pulse_width_calculation` - Test pulse width interpolation
- `test_initialize_creates_servo_objects` - Test servo object creation
- `test_shutdown_cleanup` - Test proper shutdown and cleanup
- `test_smooth_move_to_angle_async` - Test async smooth movement

#### TestGPIOServoController  
- `test_init_without_gpio` - Test initialization when RPi.GPIO unavailable
- `test_init_with_gpio_mock` - Test successful initialization with mocked GPIO
- `test_set_servo_angle_valid` - Test PWM duty cycle calculation and setting
- `test_set_servo_angle_invalid` - Test invalid angle handling
- `test_get_servo_angle` - Test angle tracking
- `test_pulse_width_to_duty_cycle` - Test pulse width conversion
- `test_initialize_gpio_setup` - Test GPIO pin setup
- `test_shutdown_gpio_cleanup` - Test GPIO cleanup
- `test_smooth_move_to_angle_async` - Test async smooth movement

### test_hardware/test_servos/test_controller_selector.py

#### TestGetServoController
- `test_get_controller_auto_pca9685_available` - Test auto selection when PCA9685 works
- `test_get_controller_auto_fallback_gpio` - Test fallback to GPIO when PCA9685 fails
- `test_get_controller_explicit_pca9685` - Test explicit PCA9685 selection
- `test_get_controller_explicit_gpio` - Test explicit GPIO selection
- `test_get_controller_invalid_type` - Test invalid controller type raises exception
- `test_kwargs_passed_to_controller` - Test additional arguments passed through

#### TestControllerAvailability
- `test_is_pca9685_available_true` - Test PCA9685 availability detection (mocked true)
- `test_is_pca9685_available_false` - Test PCA9685 availability detection (mocked false)
- `test_get_recommended_controller_type_pca9685` - Test recommendation when PCA9685 available
- `test_get_recommended_controller_type_gpio` - Test recommendation when only GPIO available

### test_hardware/test_cameras/test_camera.py

#### TestCameraInitialization
- `test_init_default_parameters` - Test default parameter initialization
- `test_init_custom_parameters` - Test custom parameter initialization
- `test_init_without_picamera2` - Test initialization when Picamera2 unavailable
- `test_camera_type_detection` - Test auto-detection of camera types
- `test_display_mode_selection` - Test display mode configuration

#### TestCameraControl
- `test_start_camera_success` - Test successful camera startup
- `test_start_camera_failure` - Test camera startup failure handling
- `test_stop_camera` - Test camera shutdown
- `test_process_detection_thread` - Test detection processing in separate thread
- `test_clear_tracked_objects` - Test object tracking reset

#### TestObjectDetection
- `test_detection_with_pi_ai_camera` - Test object detection with hardware acceleration
- `test_detection_fallback_mode` - Test fallback when hardware detection unavailable
- `test_confidence_filtering` - Test detection confidence thresholding
- `test_tracked_objects_management` - Test object tracking over time

### test_vision/test_deduplication.py

#### TestObjectDeduplicator
- `test_init_default_parameters` - Test default threshold initialization
- `test_init_custom_parameters` - Test custom threshold initialization

#### TestDeduplicationMethods
- `test_deduplicate_empty_list` - Test empty detection list handling
- `test_deduplicate_no_duplicates` - Test unique detections pass through
- `test_deduplicate_identical_objects` - Test identical object removal
- `test_deduplicate_confidence_sorting` - Test highest confidence objects kept
- `test_deduplicate_async` - Test async deduplication

#### TestDuplicateDetection
- `test_is_duplicate_object_same_label` - Test duplicate detection for same label
- `test_is_duplicate_object_different_label` - Test different labels not duplicates
- `test_is_duplicate_object_overlap_threshold` - Test bounding box overlap detection
- `test_is_duplicate_object_spatial_threshold` - Test spatial similarity detection

#### TestBoundingBoxOverlap
- `test_calculate_box_overlap_no_overlap` - Test non-overlapping boxes return 0
- `test_calculate_box_overlap_partial` - Test partial overlap calculation
- `test_calculate_box_overlap_complete` - Test complete overlap calculation
- `test_calculate_box_overlap_identical` - Test identical boxes return 1.0

#### TestSpatialSimilarity
- `test_calculate_spatial_similarity_identical` - Test identical boxes return 1.0
- `test_calculate_spatial_similarity_different_positions` - Test different positions
- `test_calculate_spatial_similarity_different_sizes` - Test different sizes
- `test_calculate_spatial_similarity_threshold_cases` - Test edge cases around threshold

#### TestTemporalSmoothing
- `test_apply_temporal_smoothing_sufficient_frames` - Test objects with enough frames kept
- `test_apply_temporal_smoothing_insufficient_frames` - Test objects filtered out
- `test_apply_temporal_smoothing_empty_list` - Test empty list handling

#### TestWorldAngleCalculation
- `test_calculate_world_angle_center_object` - Test center object angle calculation
- `test_calculate_world_angle_left_edge` - Test left edge object angle
- `test_calculate_world_angle_right_edge` - Test right edge object angle
- `test_calculate_world_angle_with_fov` - Test different FOV values

### test_movement/test_scanner.py

#### TestScanPattern
- `test_init_default_parameters` - Test default FOV and overlap initialization
- `test_init_custom_parameters` - Test custom parameter initialization

#### TestPositionCalculation
- `test_calculate_positions_default_settings` - Test position calculation with defaults
- `test_calculate_positions_custom_fov` - Test with different FOV values
- `test_calculate_positions_custom_overlap` - Test with different overlap values
- `test_calculate_positions_edge_coverage` - Test full range coverage
- `test_calculate_positions_boundary_conditions` - Test edge cases

#### TestMovement
- `test_move_to_position_direct` - Test direct servo movement
- `test_move_to_position_async_with_smooth` - Test async movement with smooth capability
- `test_move_to_position_async_fallback` - Test async fallback to direct movement

### test_core/test_room_scan.py

#### TestRoomScannerInitialization
- `test_init_default_parameters` - Test default parameter initialization
- `test_init_custom_parameters` - Test custom parameter setup
- `test_init_with_mocked_hardware` - Test initialization with mocked camera/servo

#### TestScanProcess
- `test_scan_room_empty_environment` - Test scan with no objects detected
- `test_scan_room_with_objects` - Test scan with detected objects
- `test_scan_room_camera_startup` - Test camera initialization during scan
- `test_scan_room_position_movement` - Test servo movement through positions
- `test_scan_room_detection_capture` - Test detection capture at each position
- `test_scan_room_return_to_center` - Test return to center after scan

#### TestAsyncScanning
- `test_scan_room_async_empty` - Test async scan with no objects
- `test_scan_room_async_with_objects` - Test async scan with objects
- `test_scan_room_async_error_handling` - Test async error handling

#### TestConfigurationMethods
- `test_enable_face_detection` - Test face detection toggle
- `test_get_scan_summary_no_data` - Test summary with no scan data
- `test_get_scan_summary_with_data` - Test summary generation with data

#### TestDetectionCapture
- `test_capture_detections_at_position` - Test detection capture mechanics
- `test_capture_detections_confidence_filtering` - Test confidence threshold filtering
- `test_capture_detections_empty_tracked_objects` - Test with no tracked objects
- `test_capture_detections_async` - Test async detection capture

### test_settings/test_config.py

#### TestEnvironmentVariables
- `test_debug_setting_true` - Test DEBUG environment variable parsing
- `test_debug_setting_false` - Test DEBUG default/false values
- `test_log_level_setting` - Test LOG_LEVEL environment variable
- `test_log_to_file_setting` - Test LOG_TO_FILE environment variable
- `test_log_stacktrace_setting` - Test LOG_STACKTRACE environment variable
- `test_log_file_path_setting` - Test LOG_FILE_PATH environment variable

#### TestHardwareConfiguration
- `test_servo_angle_constants` - Test servo angle min/max/default values
- `test_servo_channel_constants` - Test servo channel assignments
- `test_servo_pulse_width_constants` - Test calibrated pulse width values
- `test_i2c_configuration` - Test I2C bus and address constants
- `test_camera_configuration` - Test camera-related constants

### test_utils/test_helpers.py

#### TestCorrelationID
- `test_generate_correlation_id_format` - Test 8-character hex format
- `test_generate_correlation_id_uniqueness` - Test IDs are unique across calls

#### TestDirectoryOperations
- `test_ensure_directory_exists_new` - Test creating new directory
- `test_ensure_directory_exists_existing` - Test with existing directory
- `test_ensure_directory_exists_nested` - Test creating nested directories

#### TestFilePermissions
- `test_check_file_permissions_read` - Test read permission checking
- `test_check_file_permissions_write` - Test write permission checking
- `test_check_file_permissions_execute` - Test execute permission checking
- `test_check_file_permissions_invalid` - Test invalid permission parameter

#### TestAngleConversion
- `test_degrees_to_radians_zero` - Test 0 degrees conversion
- `test_degrees_to_radians_90` - Test 90 degrees conversion
- `test_degrees_to_radians_180` - Test 180 degrees conversion
- `test_radians_to_degrees_zero` - Test 0 radians conversion
- `test_radians_to_degrees_pi` - Test π radians conversion

#### TestMathUtilities
- `test_clamp_within_range` - Test value within min/max range
- `test_clamp_below_minimum` - Test value clamped to minimum
- `test_clamp_above_maximum` - Test value clamped to maximum
- `test_clamp_equal_boundaries` - Test edge cases at boundaries

#### TestTimer
- `test_timer_context_manager` - Test Timer context manager usage
- `test_timer_decorator` - Test timer decorator functionality
- `test_timer_elapsed_time` - Test elapsed time measurement accuracy

### test_utils/test_logging_config.py

#### TestRaspibotFormatter
- `test_format_basic_message` - Test basic log message formatting
- `test_format_with_correlation_id` - Test formatting with correlation ID
- `test_format_without_correlation` - Test formatting without correlation info
- `test_format_with_exception_stacktrace_disabled` - Test exception formatting (no stack)
- `test_format_with_exception_stacktrace_enabled` - Test exception formatting (with stack)
- `test_format_class_function_info` - Test class/function/line formatting

#### TestCorrelationContext
- `test_set_correlation_id` - Test correlation ID context setting
- `test_get_correlation_id` - Test correlation ID retrieval
- `test_correlation_context_isolation` - Test context isolation across tasks

#### TestLoggingSetup
- `test_setup_logging_default` - Test default logging setup
- `test_setup_logging_custom_level` - Test custom log level setup
- `test_setup_logging_file_output` - Test file output configuration
- `test_setup_logging_console_only` - Test console-only configuration

### test_exceptions.py

#### TestExceptionHierarchy
- `test_raspibot_exception_base` - Test base exception class
- `test_hardware_exception_inheritance` - Test HardwareException inherits from RaspibotException
- `test_configuration_exception_inheritance` - Test ConfigurationException inheritance
- `test_calibration_exception_inheritance` - Test CalibrationException inheritance
- `test_camera_exception_inheritance` - Test CameraException inheritance
- `test_servo_exception_inheritance` - Test ServoException inheritance

#### TestExceptionMessages
- `test_exception_message_preservation` - Test custom messages preserved
- `test_exception_str_representation` - Test string representation
- `test_exception_chaining` - Test exception chaining works correctly

### test_main.py

#### TestMainEntryPoint
- `test_main_execution` - Test main function executes without error
- `test_main_logging_setup` - Test logging setup in main
- `test_main_correlation_id_setting` - Test correlation ID initialization
- `test_main_return_code` - Test successful return code

## Mock Strategy

### Hardware Mocking
- **Servo Controllers**: Mock `adafruit_pca9685`, `RPi.GPIO` modules
- **Camera Hardware**: Mock `picamera2` module and camera detection
- **I2C/GPIO**: Mock all hardware communication interfaces

### External Dependencies
- **File System**: Use `tempfile` for directory/file operations
- **Time**: Mock `time.sleep` and `time.time` where needed for deterministic tests
- **Environment Variables**: Use `unittest.mock.patch.dict` for environment testing

## Test Execution Strategy

### Test Markers
- `@pytest.mark.unit` - All unit tests
- `@pytest.mark.servo` - Servo-related tests  
- `@pytest.mark.camera` - Camera-related tests
- `@pytest.mark.async` - Async functionality tests

### Fixtures
- `mock_servo_controller` - Mocked servo controller
- `mock_camera` - Mocked camera hardware
- `temp_directory` - Temporary directory for file operations
- `mock_environment` - Clean environment variables

### Coverage Requirements
- Line coverage: 90%+
- Branch coverage: 85%+
- Function coverage: 95%+

Each test file should achieve >95% coverage of its target module to ensure comprehensive protection against regressions.

## Code Issues Found During Test Implementation

### raspibot.settings.config Issues
- **Fixed**: SERVO_TILT_90_PULSE value in config.py is 1.4, not 1.45 as initially expected in tests
- **Note**: All other pulse width values match expected calibration

### raspibot.hardware.servos.servo Issues
- **Architecture Change**: PCA9685ServoController initializes hardware in constructor, not via separate initialize() method
- **Architecture Change**: GPIOServoController handles ImportError gracefully, doesn't raise exception when RPi.GPIO unavailable
- **Default Pin Mapping**: GPIO controller uses pins {0: 18, 1: 19} by default, not {0: 17, 1: 18}
- **Missing Methods**: No _pulse_width_to_duty_cycle() or initialize() methods in actual implementation
- **Servo Creation**: PCA9685 creates servo objects immediately in _create_servos() during initialization
- **GPIO PWM**: GPIO controller uses temporary PWM objects per movement, not persistent PWM instances

### Testing Approach Adaptations
- **Mocking Strategy**: PCA9685 tests require mocking 'board' module alongside Adafruit libraries
- **GPIO Testing**: GPIO controller gracefully handles missing hardware, making some error tests irrelevant
- **Async Testing**: All async functionality works as expected with proper AsyncMock usage

### raspibot.hardware.cameras.camera Issues
- **Hardware Dependency**: Camera module requires Picamera2 library and raises ImportError when unavailable
- **Complex Initialization**: Camera initialization involves hardware detection, threading, and OpenCV integration
- **Limited Unit Test Scope**: Only basic configuration constants and error handling can be practically unit tested

### Camera Testing Limitations
The camera module presents unique challenges for unit testing:

**NOT Unit Tested (Hardware Complexity)**:
- Hardware detection (Picamera2.global_camera_info())
- Camera streaming and frame capture
- Real-time object detection processing
- Background thread management
- OpenCV neural network inference
- Memory management for video streams
- Camera-specific initialization (Pi AI, Pi Camera, USB)
- Display preview functionality
- Parameter validation beyond basic type checking
- Configuration loading and management
- Tracked objects state management

**Unit Tested (Business Logic)**:
- Import error handling when Picamera2 unavailable
- Display mode constants are properly defined
- Basic module structure and availability detection

**Recommendation**: Camera functionality should be tested through integration tests with real hardware or end-to-end system tests rather than attempting complex mocking.

### Recommendations for Code Changes
**None required** - The current code structure is working correctly. The test plan was based on anticipated architecture that differs from the actual elegant implementation. The actual code:
1. Handles hardware unavailability gracefully
2. Initializes properly in constructors
3. Uses appropriate default pin mappings
4. Implements calibrated pulse width values correctly

The tests have been updated to match the actual working implementation rather than suggesting code changes.