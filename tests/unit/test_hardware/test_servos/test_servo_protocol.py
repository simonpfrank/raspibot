"""Unit tests for ServoControllerProtocol."""

import pytest
from typing import runtime_checkable
from unittest.mock import Mock, AsyncMock

from raspibot.hardware.servos.servo_protocol import ServoControllerProtocol
from raspibot.hardware.servos.servo_types import ServoName


class TestServoControllerProtocol:
    """Tests for the consolidated servo controller protocol."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """Protocol is decorated with runtime_checkable."""
        assert runtime_checkable(ServoControllerProtocol)

    def test_mock_satisfies_protocol(self) -> None:
        """A mock with correct methods satisfies the protocol."""
        mock = Mock()
        mock.set_servo_angle = Mock()
        mock.get_servo_angle = Mock(return_value=90.0)
        mock.smooth_move_to_angle = AsyncMock()

        assert isinstance(mock, ServoControllerProtocol)

    def test_protocol_requires_set_servo_angle(self) -> None:
        """Protocol requires set_servo_angle method."""

        class Incomplete:
            def get_servo_angle(self, name: ServoName) -> float:
                return 0.0

            async def smooth_move_to_angle(
                self, name: ServoName, angle: float, speed: float = 1.0
            ) -> None:
                pass

        assert not isinstance(Incomplete(), ServoControllerProtocol)

    def test_protocol_requires_get_servo_angle(self) -> None:
        """Protocol requires get_servo_angle method."""

        class Incomplete:
            def set_servo_angle(self, name: ServoName, angle: float) -> None:
                pass

            async def smooth_move_to_angle(
                self, name: ServoName, angle: float, speed: float = 1.0
            ) -> None:
                pass

        assert not isinstance(Incomplete(), ServoControllerProtocol)

    def test_protocol_requires_smooth_move_to_angle(self) -> None:
        """Protocol requires smooth_move_to_angle method."""

        class Incomplete:
            def set_servo_angle(self, name: ServoName, angle: float) -> None:
                pass

            def get_servo_angle(self, name: ServoName) -> float:
                return 0.0

        assert not isinstance(Incomplete(), ServoControllerProtocol)

    def test_complete_implementation_satisfies_protocol(self) -> None:
        """A complete implementation satisfies the protocol."""

        class Complete:
            def set_servo_angle(self, name: ServoName, angle: float) -> None:
                pass

            def get_servo_angle(self, name: ServoName) -> float:
                return 0.0

            async def smooth_move_to_angle(
                self, name: ServoName, angle: float, speed: float = 1.0
            ) -> None:
                pass

        assert isinstance(Complete(), ServoControllerProtocol)
