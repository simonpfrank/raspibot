"""Single source of truth for servo controller protocol.

This module defines the ServoControllerProtocol that all servo controllers
must satisfy. Import from here instead of defining local protocols.
"""

from typing import Protocol, runtime_checkable

from raspibot.hardware.servos.servo_types import ServoName


@runtime_checkable
class ServoControllerProtocol(Protocol):
    """Protocol for servo controller interface.

    All servo controllers (PCA9685, GPIO, mocks) must implement these methods.
    Uses ServoName enum for type-safe servo references.

    Methods:
        set_servo_angle: Set servo to an absolute angle.
        get_servo_angle: Get the current angle of a servo.
        smooth_move_to_angle: Async smooth movement to target angle.
    """

    def set_servo_angle(self, name: ServoName, angle: float) -> None:
        """Set servo angle.

        Args:
            name: Which servo to move.
            angle: Target angle in degrees.
        """
        ...

    def get_servo_angle(self, name: ServoName) -> float:
        """Get current servo angle.

        Args:
            name: Which servo to query.

        Returns:
            Current angle in degrees.
        """
        ...

    async def smooth_move_to_angle(
        self, name: ServoName, angle: float, speed: float = 1.0
    ) -> None:
        """Move servo smoothly to target angle.

        Args:
            name: Which servo to move.
            angle: Target angle in degrees.
            speed: Movement speed (0.1 to 1.0). Default 1.0.
        """
        ...
