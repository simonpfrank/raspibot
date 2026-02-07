"""Servo name enumeration for type-safe servo references.

This module defines ServoName, replacing magic strings like "pan" and "tilt"
with a type-safe enum. Use ServoName.PAN and ServoName.TILT throughout the
codebase instead of raw strings.
"""

from enum import Enum


class ServoName(Enum):
    """Valid servo names for the robot's pan/tilt system."""

    PAN = "pan"
    TILT = "tilt"
