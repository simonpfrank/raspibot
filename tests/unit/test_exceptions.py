"""Tests for custom exception classes.

This module tests the simple exception hierarchy for the Raspibot project.
"""

import pytest

# Import the exceptions module (will be created after tests)
# from raspibot import exceptions


class TestExceptionHierarchy:
    """Test the custom exception hierarchy."""

    def test_raspibot_exception_base(self):
        """Test that RaspibotException is the base exception."""
        from raspibot.exceptions import RaspibotException
        assert issubclass(RaspibotException, Exception)

    def test_hardware_exception_inheritance(self):
        """Test that HardwareException inherits from RaspibotException."""
        from raspibot.exceptions import RaspibotException, HardwareException
        assert issubclass(HardwareException, RaspibotException)

    def test_configuration_exception_inheritance(self):
        """Test that ConfigurationException inherits from RaspibotException."""
        from raspibot.exceptions import RaspibotException, ConfigurationException
        assert issubclass(ConfigurationException, RaspibotException)

    def test_calibration_exception_inheritance(self):
        """Test that CalibrationException inherits from RaspibotException."""
        from raspibot.exceptions import RaspibotException, CalibrationException
        assert issubclass(CalibrationException, RaspibotException)

    def test_camera_exception_inheritance(self):
        """Test that CameraException inherits from HardwareException."""
        from raspibot.exceptions import HardwareException, CameraException
        assert issubclass(CameraException, HardwareException)

    def test_servo_exception_inheritance(self):
        """Test that ServoException inherits from HardwareException."""
        from raspibot.exceptions import HardwareException, ServoException
        assert issubclass(ServoException, HardwareException)

    def test_exception_message(self):
        """Test that exceptions can be created with custom messages."""
        from raspibot.exceptions import RaspibotException
        message = "Test error message"
        exception = RaspibotException(message)
        assert str(exception) == message

    def test_hardware_exception_message(self):
        """Test that HardwareException can be created with custom messages."""
        from raspibot.exceptions import HardwareException
        message = "Hardware error occurred"
        exception = HardwareException(message)
        assert str(exception) == message 