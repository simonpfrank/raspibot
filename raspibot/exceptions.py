"""Custom exception classes for the Raspibot project.

This module defines a simple exception hierarchy for domain-specific
error handling without complex abstractions.
"""


class RaspibotException(Exception):
    """Base exception for all raspibot errors."""
    pass


class HardwareException(RaspibotException):
    """Hardware-related errors (servo, camera, sensors)."""
    pass


class ConfigurationException(RaspibotException):
    """Configuration and settings errors."""
    pass


class CalibrationException(RaspibotException):
    """Servo/camera calibration errors."""
    pass


class CameraException(HardwareException):
    """Camera-specific hardware errors."""
    pass


class ServoException(HardwareException):
    """Servo-specific hardware errors."""
    pass 