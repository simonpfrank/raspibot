"""Hardware configuration constants and mappings.

This module defines hardware-specific constants including pin mappings,
device addresses, and operational limits for the Raspibot hardware.
"""

from typing import Final, Dict

# I2C Configuration
I2C_BUS: Final[int] = 1  # Standard I2C bus on Raspberry Pi
PCA9685_ADDRESS: Final[int] = 0x40  # Default PCA9685 I2C address

# Servo Configuration
SERVO_MIN_ANGLE: Final[int] = 0
SERVO_MAX_ANGLE: Final[int] = 359
SERVO_DEFAULT_ANGLE: Final[int] = 90
SERVO_PAN_CHANNEL: Final[int] = 0
SERVO_TILT_CHANNEL: Final[int] = 1
SERVO_CHANNELS: Final[list[int]] = [0, 1]  # Channels used for servos

# Pan/Tilt Specific Configuration
SERVO_PAN_MIN_ANGLE: Final[int] = 0
SERVO_PAN_MAX_ANGLE: Final[int] = 180
SERVO_PAN_CENTER: Final[int] = 90

# Tilt range adjusted for +70° calibration offset
# Actual servo positions: 160° (up) to 340° (down)
SERVO_TILT_MIN_ANGLE: Final[int] = 90   # 90° = pointing up (actual: 160°)
SERVO_TILT_MAX_ANGLE: Final[int] = 270  # 270° = pointing down (actual: 340°)
SERVO_TILT_CENTER: Final[int] = 200     # Center between 90° and 270° (actual: 270°)
SERVO_TILT_UP_ANGLE: Final[int] = 90    # Pointing straight up (actual: 160°)
SERVO_TILT_DOWN_ANGLE: Final[int] = 270 # Pointing straight down (actual: 340°)

# PCA9685 Anti-Jitter Settings
PCA9685_DEADBAND: Final[float] = 0.5  # Reduced from 2.0 - minimum angle change to trigger movement (degrees)
PCA9685_STABILIZATION_DELAY: Final[float] = 0.02  # Reduced from 0.1 - delay after movement to stabilize (seconds)
PCA9685_MIN_STEP_SIZE: Final[float] = 0.5  # Reduced from 2.0 - minimum step size for smoother movement (degrees)
PCA9685_MAX_STEP_SIZE: Final[float] = 2.0  # Reduced from 5.0 - maximum step size for faster movement (degrees)
PCA9685_STEP_DELAY: Final[float] = 0.01  # Reduced from 0.02 - delay between steps for smoother movement (seconds)
PCA9685_PWM_PRECISION: Final[int] = 3  # Increased from 2 - PWM precision to minimize jitter

# Camera Configuration
CAMERA_DEFAULT_WIDTH: Final[int] = 1280
CAMERA_DEFAULT_HEIGHT: Final[int] = 480
CAMERA_DEVICE_ID: Final[int] = 0

# Face Tracking Configuration  
FACE_MOVEMENT_THRESHOLD: Final[int] = 50   # pixels - minimum movement to trigger servo
FACE_MOVEMENT_SCALE: Final[float] = 0.3    # how much to move servo per pixel offset
FACE_STABILITY_THRESHOLD: Final[int] = 100 # pixels - max movement to be considered stable
FACE_STABILITY_FRAMES: Final[int] = 3      # frames needed to confirm stability
SLEEP_TIMEOUT: Final[int] = 300            # 5 minutes of no faces

# Search Pattern Configuration
SEARCH_PATTERN_ENABLED: Final[bool] = True  # Enable systematic search patterns
SEARCH_PAN_STEPS: Final[int] = 8           # Number of pan steps per tilt level
SEARCH_TILT_STEPS: Final[int] = 6          # Number of tilt levels to scan
SEARCH_MOVEMENT_SPEED: Final[float] = 0.3  # Slow movement speed for search (0.1-1.0)
SEARCH_STABILIZATION_DELAY: Final[float] = 0.5  # Delay after movement to stabilize (seconds)
SEARCH_FACE_DETECTION_DELAY: Final[float] = 0.2  # Delay for face detection at each position (seconds)
SEARCH_PATTERN_TIMEOUT: Final[int] = 60    # Timeout for complete search pattern (seconds)
SEARCH_RETURN_TO_CENTER: Final[bool] = True  # Return to center after search pattern

# GPIO Servo Configuration
GPIO_SERVO_MIN_ANGLE: Final[int] = 0
GPIO_SERVO_MAX_ANGLE: Final[int] = 270  # 270-degree movement range
GPIO_SERVO_DEFAULT_ANGLE: Final[int] = 135  # Center position for 270-degree range
GPIO_SERVO_FREQUENCY: Final[int] = 50  # PWM frequency in Hz
GPIO_SERVO_MIN_PULSE: Final[float] = 0.5  # Minimum pulse width in ms (0 degrees)
GPIO_SERVO_MAX_PULSE: Final[float] = 2.5  # Maximum pulse width in ms (270 degrees)

# GPIO Servo Anti-Jitter Settings
GPIO_SERVO_DEADBAND: Final[float] = 1.0  # Minimum angle change to trigger movement (degrees)
GPIO_SERVO_STABILIZATION_DELAY: Final[float] = 0.05  # Reduced delay after movement to stabilize (seconds)
GPIO_SERVO_MIN_STEP_SIZE: Final[float] = 1.0  # Increased minimum step size for smoother movement (degrees)
GPIO_SERVO_MAX_STEP_SIZE: Final[float] = 3.0  # Increased maximum step size for faster movement (degrees)
GPIO_SERVO_STEP_DELAY: Final[float] = 0.01  # Reduced delay between steps for smoother movement (seconds)
GPIO_SERVO_DUTY_CYCLE_PRECISION: Final[int] = 1  # Reduced precision to minimize PWM jitter

# GPIO Servo Pin Mappings
# Dictionary mapping servo channels to GPIO pins
# Format: {channel: gpio_pin}
GPIO_SERVO_PINS: Final[Dict[int, int]] = {
    0: 17,  # Pan servo on GPIO 17
    1: 18,  # Tilt servo on GPIO 18
}

# Pi AI Camera Configuration
PI_AI_CAMERA_CONFIG: Final[Dict] = {
    "default_model": "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk",
    "people_detection": {
        "confidence_threshold": 0.55,
        "iou_threshold": 0.65,
        "max_detections": 10,
        "inference_rate": 30
    },
    "face_detection": {
        "confidence_threshold": 0.6,
        "iou_threshold": 0.3,
        "max_detections": 5
    }
}

# Search Pattern Configuration
SEARCH_PATTERN_CONFIG: Final[Dict] = {
    "spiral_search": {
        "default_radius": 0.3,
        "default_steps": 20,
        "step_delay": 0.5
    },
    "grid_search": {
        "pan_range": (-0.4, 0.4),
        "tilt_range": (-0.3, 0.3),
        "pan_steps": 8,
        "tilt_steps": 6,
        "step_delay": 0.3
    },
    "adaptive_search": {
        "search_radius": 0.2,
        "max_search_time": 10.0
    }
}

# GPIO Pin Mappings
LED_PIN: Final[int] = 18
BUTTON_PIN: Final[int] = 17 