"""Unit tests for ServoName enum."""

import pytest

from raspibot.hardware.servos.servo_types import ServoName
from raspibot.settings.config import SERVO_CONFIGS


class TestServoNameEnum:
    """Tests for ServoName enum values and usage."""

    def test_pan_value(self) -> None:
        """PAN enum has value 'pan'."""
        assert ServoName.PAN.value == "pan"

    def test_tilt_value(self) -> None:
        """TILT enum has value 'tilt'."""
        assert ServoName.TILT.value == "tilt"

    def test_only_two_members(self) -> None:
        """ServoName has exactly two members."""
        assert len(ServoName) == 2

    def test_config_lookup_by_enum(self) -> None:
        """SERVO_CONFIGS can be looked up with ServoName enum values."""
        for name in ServoName:
            assert name.value in SERVO_CONFIGS

    def test_enum_from_string(self) -> None:
        """ServoName can be created from string value."""
        assert ServoName("pan") == ServoName.PAN
        assert ServoName("tilt") == ServoName.TILT

    def test_invalid_name_raises(self) -> None:
        """Invalid string raises ValueError."""
        with pytest.raises(ValueError):
            ServoName("invalid")
