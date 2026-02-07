"""Hardware integration tests for MotionController with PCA9685.

These tests require a PCA9685 board at 0x40 on I2C bus 1 with pan and tilt
servos connected. Tests are skipped automatically if hardware is unavailable.

Run with: python -m pytest tests/integration/test_motion_controller_hardware.py -v
"""

import asyncio
import logging
import time

import pytest

from raspibot.hardware.servos.servo_types import ServoName
from raspibot.movement.gestures import ATTENTION, NOD, SHAKE
from raspibot.movement.motion_controller import MotionController
from raspibot.movement.motion_offset import MotionOffset

logging.basicConfig(level=logging.INFO)

# Base angles outside jitter zone (87-104°)
BASE_PAN = 86.0
BASE_TILT = 75.0


def _create_real_servo():
    """Create a real PCA9685ServoController, or None if unavailable."""
    try:
        from raspibot.hardware.servos.servo import PCA9685ServoController

        return PCA9685ServoController()
    except Exception:
        return None


@pytest.fixture(scope="module")
def servo_controller():
    """Real PCA9685 servo controller fixture. Skips if hardware unavailable."""
    controller = _create_real_servo()
    if controller is None:
        pytest.skip("PCA9685 hardware not available")
    yield controller
    controller.shutdown()


@pytest.fixture()
def motion_controller(servo_controller):
    """MotionController wrapping real hardware."""
    mc = MotionController(servo_controller)
    mc.set_base(BASE_PAN, BASE_TILT)
    mc.apply()
    time.sleep(0.5)  # let servos settle
    return mc


class TestServoDirectControl:
    """Verify direct servo control works before testing MotionController."""

    def test_set_servo_angle_pan(self, servo_controller) -> None:
        """Pan servo moves to commanded angle."""
        servo_controller.set_servo_angle(ServoName.PAN, 60.0)
        time.sleep(0.3)
        assert servo_controller.get_servo_angle(ServoName.PAN) == 60.0

        servo_controller.set_servo_angle(ServoName.PAN, BASE_PAN)
        time.sleep(0.3)

    def test_set_servo_angle_tilt(self, servo_controller) -> None:
        """Tilt servo moves to commanded angle."""
        servo_controller.set_servo_angle(ServoName.TILT, 50.0)
        time.sleep(0.3)
        assert servo_controller.get_servo_angle(ServoName.TILT) == 50.0

        servo_controller.set_servo_angle(ServoName.TILT, BASE_TILT)
        time.sleep(0.3)

    @pytest.mark.asyncio
    async def test_smooth_move_visible(self, servo_controller) -> None:
        """Smooth move produces gradual motion (not instant jump)."""
        servo_controller.set_servo_angle(ServoName.TILT, 50.0)
        await asyncio.sleep(0.3)

        start = time.monotonic()
        await servo_controller.smooth_move_to_angle(ServoName.TILT, 120.0, speed=0.5)
        elapsed = time.monotonic() - start

        # Smooth move should take measurable time (not instant)
        assert elapsed > 0.1
        assert servo_controller.get_servo_angle(ServoName.TILT) == 120.0

        servo_controller.set_servo_angle(ServoName.TILT, BASE_TILT)
        await asyncio.sleep(0.3)


class TestMotionControllerGestures:
    """Test gesture playback on real hardware."""

    @pytest.mark.asyncio
    async def test_play_nod(self, motion_controller) -> None:
        """NOD gesture produces visible tilt movement and completes."""
        assert not motion_controller.is_playing

        await motion_controller.play_gesture(NOD)

        assert not motion_controller.is_playing

    @pytest.mark.asyncio
    async def test_play_shake(self, motion_controller) -> None:
        """SHAKE gesture produces visible pan movement and completes."""
        await motion_controller.play_gesture(SHAKE)

        assert not motion_controller.is_playing

    @pytest.mark.asyncio
    async def test_play_attention(self, motion_controller) -> None:
        """ATTENTION gesture produces visible tilt movement and completes."""
        await motion_controller.play_gesture(ATTENTION)

        assert not motion_controller.is_playing

    @pytest.mark.asyncio
    async def test_gesture_returns_to_base(self, motion_controller, servo_controller) -> None:
        """Servos return to base angles after gesture completes."""
        await motion_controller.play_gesture(NOD)

        pan = servo_controller.get_servo_angle(ServoName.PAN)
        tilt = servo_controller.get_servo_angle(ServoName.TILT)

        assert pan == BASE_PAN
        assert tilt == BASE_TILT


class TestMotionControllerLayers:
    """Test offset layers on real hardware."""

    def test_apply_with_offset(self, motion_controller, servo_controller) -> None:
        """Offset shifts servo position from base."""
        # Use negative pan offset to stay below jitter zone (87-104°)
        motion_controller.set_offset("test", MotionOffset(pan=-20.0, tilt=-5.0))
        motion_controller.apply()
        time.sleep(0.3)

        assert servo_controller.get_servo_angle(ServoName.PAN) == BASE_PAN - 20.0
        assert servo_controller.get_servo_angle(ServoName.TILT) == BASE_TILT - 5.0

        motion_controller.clear_offset("test")
        motion_controller.apply()
        time.sleep(0.3)

    def test_clear_offset_returns_to_base(self, motion_controller, servo_controller) -> None:
        """Clearing offset returns servos to base position."""
        # Use negative offset to stay below jitter zone
        motion_controller.set_offset("test", MotionOffset(pan=-20.0))
        motion_controller.apply()
        time.sleep(0.3)

        motion_controller.clear_offset("test")
        motion_controller.apply()
        time.sleep(0.3)

        assert servo_controller.get_servo_angle(ServoName.PAN) == BASE_PAN
