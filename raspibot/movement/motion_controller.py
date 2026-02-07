"""Motion controller that wires the movement stack to servo hardware.

Connects OffsetComposer (base + layers) and SequencePlayer (gesture playback)
to a ServoControllerProtocol, sending resolved angles to physical servos.

Example:
    >>> from raspibot.movement.motion_controller import MotionController
    >>> controller = MotionController(servo_controller)
    >>> controller.set_base(90.0, 75.0)
    >>> controller.apply()
    >>> await controller.play_gesture(NOD)
"""

import asyncio
import time
from typing import Tuple

from raspibot.hardware.servos.servo_protocol import ServoControllerProtocol
from raspibot.hardware.servos.servo_types import ServoName
from raspibot.movement.motion_offset import MotionOffset, OffsetComposer
from raspibot.movement.sequence import MotionSequence, SequencePlayer

_DEFAULT_PAN_LIMITS: Tuple[float, float] = (0.0, 180.0)
_DEFAULT_TILT_LIMITS: Tuple[float, float] = (0.0, 150.0)
_DEFAULT_TICK_INTERVAL: float = 0.02


class MotionController:
    """Connects movement stack to servo hardware.

    Wraps OffsetComposer for offset layering and SequencePlayer for gesture
    playback. Sends resolved (pan, tilt) angles to the servo controller.

    Args:
        servo: Servo controller implementing ServoControllerProtocol.
        pan_limits: (min, max) pan angle in degrees.
        tilt_limits: (min, max) tilt angle in degrees.
        tick_interval: Seconds between ticks during gesture playback.

    Example:
        >>> mc = MotionController(servo)
        >>> mc.set_base(90.0, 75.0)
        >>> mc.set_offset("tracking", MotionOffset(pan=5.0))
        >>> mc.apply()  # sends (95.0, 75.0) to servos
    """

    def __init__(
        self,
        servo: ServoControllerProtocol,
        pan_limits: Tuple[float, float] = _DEFAULT_PAN_LIMITS,
        tilt_limits: Tuple[float, float] = _DEFAULT_TILT_LIMITS,
        tick_interval: float = _DEFAULT_TICK_INTERVAL,
    ) -> None:
        """Initialize with servo controller and limits."""
        self._servo = servo
        self._composer = OffsetComposer(pan_limits, tilt_limits)
        self._tick_interval = tick_interval
        self._playing = False

    @property
    def is_playing(self) -> bool:
        """Whether a gesture is currently being played."""
        return self._playing

    def set_base(self, pan: float, tilt: float) -> None:
        """Set the base pan/tilt position.

        Args:
            pan: Base pan angle in degrees.
            tilt: Base tilt angle in degrees.
        """
        self._composer.set_base(pan, tilt)

    def set_offset(self, layer_name: str, offset: MotionOffset) -> None:
        """Set a named offset layer.

        Args:
            layer_name: Name for this offset layer.
            offset: The offset to apply.
        """
        self._composer.set_offset(layer_name, offset)

    def clear_offset(self, layer_name: str) -> None:
        """Remove a named offset layer.

        Args:
            layer_name: Name of the layer to remove.
        """
        self._composer.clear_offset(layer_name)

    def apply(self) -> None:
        """Resolve all layers and send angles to servos."""
        pan, tilt = self._composer.resolve()
        self._servo.set_servo_angle(ServoName.PAN, pan)
        self._servo.set_servo_angle(ServoName.TILT, tilt)

    async def play_gesture(self, sequence: MotionSequence) -> None:
        """Play a gesture sequence, sending interpolated angles each tick.

        Sets a "gesture" offset layer during playback and clears it when done.
        Other offset layers are preserved throughout.

        Args:
            sequence: The MotionSequence to play.
        """
        player = SequencePlayer(sequence)
        self._playing = True

        start = time.monotonic()
        player.start(start)

        while not player.is_complete:
            now = time.monotonic()
            offset = player.evaluate(now)
            self._composer.set_offset("gesture", offset)
            self.apply()
            await asyncio.sleep(self._tick_interval)

        self._composer.clear_offset("gesture")
        self.apply()
        self._playing = False
