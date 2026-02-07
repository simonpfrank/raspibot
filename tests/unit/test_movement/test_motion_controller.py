"""Unit tests for MotionController.

Tests the class that wires movement stack (sequences, offsets) to servo hardware.
Uses mock servo controllers to verify correct angles are sent.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from raspibot.hardware.servos.servo_types import ServoName
from raspibot.movement.gestures import NOD
from raspibot.movement.motion_controller import MotionController
from raspibot.movement.motion_offset import MotionOffset


def _make_mock_servo() -> MagicMock:
    """Create a mock servo controller satisfying ServoControllerProtocol."""
    mock = MagicMock()
    mock.set_servo_angle = MagicMock()
    mock.get_servo_angle = MagicMock(return_value=90.0)
    mock.smooth_move_to_angle = AsyncMock()
    return mock


class TestMotionControllerInit:
    """Tests for MotionController construction."""

    def test_is_not_playing_initially(self) -> None:
        """MotionController is not playing after construction."""
        mc = MotionController(_make_mock_servo())
        assert mc.is_playing is False

    def test_default_limits(self) -> None:
        """Default limits are pan (0,180) and tilt (0,150)."""
        mc = MotionController(_make_mock_servo())
        mc.set_base(200.0, 200.0)
        mc.apply()
        servo = mc._servo  # noqa: SLF001
        servo.set_servo_angle.assert_any_call(ServoName.PAN, 180.0)
        servo.set_servo_angle.assert_any_call(ServoName.TILT, 150.0)


class TestSetBaseAndApply:
    """Tests for set_base, set_offset, clear_offset, and apply."""

    def test_set_base_and_apply(self) -> None:
        """set_base + apply sends base angles to servo controller."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)
        mc.apply()
        servo.set_servo_angle.assert_any_call(ServoName.PAN, 90.0)
        servo.set_servo_angle.assert_any_call(ServoName.TILT, 75.0)

    def test_set_offset_and_apply(self) -> None:
        """Offset adds to base before sending."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)
        mc.set_offset("tracking", MotionOffset(pan=5.0, tilt=-3.0))
        mc.apply()
        servo.set_servo_angle.assert_any_call(ServoName.PAN, 95.0)
        servo.set_servo_angle.assert_any_call(ServoName.TILT, 72.0)

    def test_clear_offset_and_apply(self) -> None:
        """Clearing offset removes it from resolution."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)
        mc.set_offset("tracking", MotionOffset(pan=5.0))
        mc.clear_offset("tracking")
        mc.apply()
        servo.set_servo_angle.assert_any_call(ServoName.PAN, 90.0)

    def test_apply_clamps_to_limits(self) -> None:
        """Angles are clamped to constructor limits."""
        servo = _make_mock_servo()
        mc = MotionController(servo, pan_limits=(10, 170), tilt_limits=(20, 130))
        mc.set_base(5.0, 5.0)
        mc.apply()
        servo.set_servo_angle.assert_any_call(ServoName.PAN, 10.0)
        servo.set_servo_angle.assert_any_call(ServoName.TILT, 20.0)

    def test_multiple_offsets_sum(self) -> None:
        """Multiple offset layers sum correctly."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)
        mc.set_offset("tracking", MotionOffset(pan=5.0))
        mc.set_offset("gesture", MotionOffset(pan=-3.0, tilt=2.0))
        mc.apply()
        servo.set_servo_angle.assert_any_call(ServoName.PAN, 92.0)
        servo.set_servo_angle.assert_any_call(ServoName.TILT, 77.0)


class TestPlayGesture:
    """Tests for async play_gesture method."""

    @pytest.mark.asyncio
    async def test_play_gesture_calls_set_servo_angle(self) -> None:
        """Mock servo receives set_servo_angle calls during gesture playback."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)

        with patch("time.monotonic", side_effect=[0.0, 0.3, 0.6, 0.9, 1.1]):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await mc.play_gesture(NOD)

        assert servo.set_servo_angle.call_count >= 2

    @pytest.mark.asyncio
    async def test_play_gesture_clears_layer_when_done(self) -> None:
        """Gesture layer is cleared after playback completes."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)

        with patch("time.monotonic", side_effect=[0.0, 0.5, 1.1]):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await mc.play_gesture(NOD)

        # After gesture, the "gesture" layer should be gone
        mc.apply()
        servo.set_servo_angle.assert_called_with(ServoName.TILT, 75.0)

    @pytest.mark.asyncio
    async def test_is_playing_during_gesture(self) -> None:
        """is_playing is True during gesture, False after."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)

        playing_during: bool = False

        async def capture_playing(_: float) -> None:
            nonlocal playing_during
            playing_during = mc.is_playing

        with patch("time.monotonic", side_effect=[0.0, 0.5, 1.1]):
            with patch("asyncio.sleep", side_effect=capture_playing):
                await mc.play_gesture(NOD)

        assert playing_during is True
        assert mc.is_playing is False

    @pytest.mark.asyncio
    async def test_gesture_preserves_other_layers(self) -> None:
        """Non-gesture layers persist through gesture playback."""
        servo = _make_mock_servo()
        mc = MotionController(servo)
        mc.set_base(90.0, 75.0)
        mc.set_offset("tracking", MotionOffset(pan=5.0))

        with patch("time.monotonic", side_effect=[0.0, 0.5, 1.1]):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await mc.play_gesture(NOD)

        # After gesture, tracking layer should still be active
        mc.apply()
        servo.set_servo_angle.assert_any_call(ServoName.PAN, 95.0)
