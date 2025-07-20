"""Hardware configuration constants and mappings.

This module defines hardware-specific constants including pin mappings,
device addresses, and operational limits for the Raspibot hardware.
"""

from typing import Final

# I2C Configuration
I2C_BUS: Final[int] = 1  # Standard I2C bus on Raspberry Pi
PCA9685_ADDRESS: Final[int] = 0x40  # Default PCA9685 I2C address

# Servo Configuration
SERVO_MIN_ANGLE: Final[int] = 0
SERVO_MAX_ANGLE: Final[int] = 180
SERVO_DEFAULT_ANGLE: Final[int] = 90
SERVO_PAN_CHANNEL: Final[int] = 0
SERVO_TILT_CHANNEL: Final[int] = 1

# Camera Configuration
CAMERA_WIDTH: Final[int] = 640
CAMERA_HEIGHT: Final[int] = 480
CAMERA_FPS: Final[int] = 30

# GPIO Pin Mappings
LED_PIN: Final[int] = 18
BUTTON_PIN: Final[int] = 17 