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

SERVO_TILT_MIN_ANGLE: Final[int] = 90   # 90° = pointing up
SERVO_TILT_MAX_ANGLE: Final[int] = 310  # 310° = pointing down
SERVO_TILT_CENTER: Final[int] = 200     # Center between 90° and 310°
SERVO_TILT_UP_ANGLE: Final[int] = 90    # Pointing straight up
SERVO_TILT_DOWN_ANGLE: Final[int] = 310 # Pointing straight down

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

# Camera Configuration
CAMERA_WIDTH: Final[int] = 640
CAMERA_HEIGHT: Final[int] = 480
CAMERA_FPS: Final[int] = 30

# GPIO Pin Mappings
LED_PIN: Final[int] = 18
BUTTON_PIN: Final[int] = 17 