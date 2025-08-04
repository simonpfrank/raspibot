"""Tests for hardware configuration constants and mappings.

This module tests the hardware-specific configuration constants
that define pin mappings, device addresses, and hardware limits.
"""

import pytest

# Import the hardware config module (will be created after tests)
# from raspibot.settings import hardware_config


class TestHardwareConfig:
    """Test hardware configuration constants and mappings."""

    def test_i2c_bus_default(self):
        """Test that I2C_BUS defaults to 1 (standard for Raspberry Pi)."""
        # This test will fail until we implement the hardware_config module
        from raspibot.settings import hardware_config
        assert hardware_config.I2C_BUS == 1

    def test_pca9685_address(self):
        """Test that PCA9685_ADDRESS is set to the correct I2C address."""
        from raspibot.settings import hardware_config
        assert hardware_config.PCA9685_ADDRESS == 0x40

    def test_servo_angle_limits(self):
        """Test that servo angle limits are reasonable values."""
        from raspibot.settings import hardware_config
        assert hardware_config.SERVO_MIN_ANGLE == 0
        assert hardware_config.SERVO_MAX_ANGLE == 359  # Updated for full 360-degree servos
        assert hardware_config.SERVO_DEFAULT_ANGLE == 90

    def test_servo_channels(self):
        """Test that servo channel mappings are defined."""
        from raspibot.settings import hardware_config
        assert hardware_config.SERVO_PAN_CHANNEL == 0
        assert hardware_config.SERVO_TILT_CHANNEL == 1

    def test_camera_settings(self):
        """Test that camera configuration constants are defined."""
        from raspibot.settings import hardware_config
        assert hardware_config.CAMERA_WIDTH == 640
        assert hardware_config.CAMERA_HEIGHT == 480
        assert hardware_config.CAMERA_FPS == 30

    def test_gpio_pins(self):
        """Test that GPIO pin mappings are defined."""
        from raspibot.settings import hardware_config
        assert hardware_config.LED_PIN == 18
        assert hardware_config.BUTTON_PIN == 17 