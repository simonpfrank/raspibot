"""Watch controller for minor camera adjustments during watch phase.

This module provides the WatchController class which makes small adjustments
to keep detected people centered in the frame during the watch phase between
room scans.
"""

import logging
from typing import Any, Dict, Final, List, Tuple

from raspibot.core.tracking_events import EdgePosition
from raspibot.hardware.servos.servo_protocol import ServoControllerProtocol

logger = logging.getLogger(__name__)

# Default parameters
DEFAULT_MAX_ADJUSTMENT: Final[float] = 5.0  # Max degrees per update
DEFAULT_DEADBAND: Final[float] = 1.0  # Min adjustment to apply
DEFAULT_FRAME_WIDTH: Final[int] = 1280
DEFAULT_FRAME_HEIGHT: Final[int] = 720
DEFAULT_FOV_DEGREES: Final[float] = 66.3
DAMPING_FACTOR: Final[float] = 0.3  # Damped response to prevent overshoot
SERVO_MIN_ANGLE: Final[float] = 0.0
SERVO_MAX_ANGLE: Final[float] = 180.0


class WatchController:
    """Control minor camera adjustments during watch phase.

    During the watch phase (between room scans), this controller makes
    small adjustments to keep detected people centered in the camera's
    field of view. Adjustments are damped and clamped to prevent
    overcorrection and servo jitter.

    Key behaviors:
    - Only adjusts when in watching state
    - Only considers "person" detections
    - Uses damped proportional control
    - Clamps adjustments to max_adjustment
    - Ignores small offsets below deadband (prevents jitter)
    - Does NOT chase if people leave the frame

    Args:
        servo_controller: Servo controller for pan/tilt movement.
        max_adjustment: Maximum adjustment per update in degrees. Default 5.0.
        deadband: Minimum adjustment to apply in degrees. Default 1.0.
        frame_width: Camera frame width in pixels. Default 1280.
        frame_height: Camera frame height in pixels. Default 720.
        fov_degrees: Horizontal field of view in degrees. Default 66.3.

    Example:
        >>> controller = WatchController(servo)
        >>> controller.start_watching((90.0, 90.0))
        >>> controller.update(detections)  # Makes minor adjustments
        >>> controller.stop_watching()
    """

    def __init__(
        self,
        servo_controller: ServoControllerProtocol,
        max_adjustment: float = DEFAULT_MAX_ADJUSTMENT,
        deadband: float = DEFAULT_DEADBAND,
        frame_width: int = DEFAULT_FRAME_WIDTH,
        frame_height: int = DEFAULT_FRAME_HEIGHT,
        fov_degrees: float = DEFAULT_FOV_DEGREES
    ) -> None:
        """Initialize the watch controller."""
        self.servo_controller = servo_controller
        self.max_adjustment = max_adjustment
        self.deadband = deadband
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fov_degrees = fov_degrees

        self._watching = False
        self.current_position: Tuple[float, float] = (90.0, 90.0)

        # Calculate degrees per pixel for offset conversion
        self._degrees_per_pixel = fov_degrees / frame_width

    def is_watching(self) -> bool:
        """Check if controller is in watching state.

        Returns:
            True if watching, False otherwise.
        """
        return self._watching

    def start_watching(self, position: Tuple[float, float]) -> None:
        """Start watching at the given position.

        Args:
            position: Initial (pan, tilt) position to watch from.
        """
        self._watching = True
        self.current_position = position
        logger.debug("Started watching at position (%.1f, %.1f)", position[0], position[1])

    def stop_watching(self) -> None:
        """Stop watching and clear state."""
        self._watching = False
        logger.debug("Stopped watching")

    def update(self, detections: List[Dict[str, Any]]) -> None:
        """Update camera position based on current detections.

        Makes minor adjustments to center detected people in the frame.
        Does nothing if:
        - Not in watching state
        - No people detected (don't chase)
        - Adjustment would be below deadband

        Args:
            detections: List of detection dictionaries with 'label' and 'box' keys.
                Box format is (x, y, width, height) in pixels.
        """
        if not self._watching:
            return

        # Filter for person detections only
        people = [d for d in detections if d.get("label") == "person"]
        if not people:
            # Don't chase if people left frame
            return

        # Calculate centroid of all people
        frame_center_x = self.frame_width / 2
        frame_center_y = self.frame_height / 2

        people_centers_x = []
        people_centers_y = []
        for person in people:
            box = person["box"]
            center_x = box[0] + box[2] / 2
            center_y = box[1] + box[3] / 2
            people_centers_x.append(center_x)
            people_centers_y.append(center_y)

        people_centroid_x = sum(people_centers_x) / len(people_centers_x)
        people_centroid_y = sum(people_centers_y) / len(people_centers_y)

        # Calculate offset from frame center
        offset_x = people_centroid_x - frame_center_x
        offset_y = people_centroid_y - frame_center_y

        # Convert to angle adjustment with damping
        # Negative for pan because positive x offset needs negative pan adjustment
        pan_adj = -offset_x * self._degrees_per_pixel * DAMPING_FACTOR
        tilt_adj = offset_y * self._degrees_per_pixel * DAMPING_FACTOR

        # Clamp to max adjustment
        pan_adj = max(-self.max_adjustment, min(self.max_adjustment, pan_adj))
        tilt_adj = max(-self.max_adjustment, min(self.max_adjustment, tilt_adj))

        # Apply if above deadband
        if abs(pan_adj) > self.deadband or abs(tilt_adj) > self.deadband:
            new_pan = self.current_position[0] + pan_adj
            new_tilt = self.current_position[1] + tilt_adj

            # Clamp to servo limits
            new_pan = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, new_pan))
            new_tilt = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, new_tilt))

            self.servo_controller.set_servo_angle("pan", new_pan)
            self.servo_controller.set_servo_angle("tilt", new_tilt)
            self.current_position = (new_pan, new_tilt)

            logger.debug(
                "Adjusted position to (%.1f, %.1f), adjustment (%.2f, %.2f)",
                new_pan, new_tilt, pan_adj, tilt_adj
            )

    def pan_to_keep_in_frame(
        self, edge_position: EdgePosition, velocity: float
    ) -> float:
        """Preemptively pan to keep a person in frame.

        Calculates and applies a pan adjustment based on edge position and
        velocity to prevent a person from exiting the frame.

        Args:
            edge_position: Current edge position of the person.
            velocity: Horizontal velocity toward the edge (pixels/frame).

        Returns:
            The pan adjustment applied in degrees. Negative = left, positive = right.
        """
        if not self._watching:
            return 0.0

        if edge_position == EdgePosition.CENTER:
            return 0.0

        # Base adjustment for edge position
        if edge_position.is_critical():
            base_adjustment = 8.0  # More aggressive for critical
        else:
            base_adjustment = 4.0  # Moderate for warning

        # Scale by velocity (faster movement = larger adjustment)
        velocity_factor = min(abs(velocity) / 10.0, 2.0)  # Cap at 2x
        adjustment = base_adjustment * (0.5 + velocity_factor * 0.5)

        # Direction based on edge
        direction = edge_position.direction()
        if direction == "left":
            pan_adjustment = -adjustment  # Pan left (decrease angle)
        else:
            pan_adjustment = adjustment  # Pan right (increase angle)

        # Apply adjustment
        new_pan = self.current_position[0] + pan_adjustment
        new_pan = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, new_pan))

        self.servo_controller.set_servo_angle("pan", new_pan)
        self.current_position = (new_pan, self.current_position[1])

        logger.debug(
            "Pan to keep in frame: edge=%s, velocity=%.1f, adjustment=%.2f, new_pan=%.1f",
            edge_position.value, velocity, pan_adjustment, new_pan
        )

        return pan_adjustment
