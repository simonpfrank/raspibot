#!/usr/bin/env python3
"""Scan movement patterns for room scanning.

Handles servo movement patterns for systematic room scanning with optimal
camera position coverage.
"""

import asyncio
import time
from typing import List
from raspibot.settings.config import SERVO_CONFIGS


class ScanPattern:
    """Manages servo movement for room scanning."""

    def __init__(self, fov_degrees: float = 66.3, overlap_degrees: float = 10.0):
        """Initialize scan pattern with camera FOV and desired overlap."""
        self.fov_degrees = fov_degrees
        self.overlap_degrees = overlap_degrees

    def calculate_positions(self) -> List[float]:
        """Calculate pan angles for complete room coverage."""
        positions = []

        pan_config = SERVO_CONFIGS["pan"]
        pan_min = pan_config["min_angle"]
        pan_max = pan_config["max_angle"]

        # Calculate effective FOV per position (accounting for overlap)
        effective_fov = self.fov_degrees - self.overlap_degrees

        # Calculate scan range
        scan_range = pan_max - pan_min

        # Calculate number of positions needed
        num_positions = int(scan_range / effective_fov) + 1

        # Generate evenly spaced positions
        for i in range(num_positions):
            position = pan_min + (i * effective_fov)
            if position <= pan_max:
                positions.append(position)

        # Ensure we cover the full range
        if positions and positions[-1] < pan_max - 5:  # 5 degree tolerance
            positions.append(pan_max)

        return positions

    def move_to_position(self, servo_controller, pan_angle: float, tilt_angle: float):
        """Move servos to scan position (direct movement)."""
        print(f"Moving servos to Pan={pan_angle:.1f}°, Tilt={tilt_angle:.1f}°")
        servo_controller.set_servo_angle("pan", pan_angle)
        servo_controller.set_servo_angle("tilt", tilt_angle)
        print("Servo movement completed")

    async def move_to_position_async(
        self, servo_controller, pan_angle: float, tilt_angle: float, speed: float = 1.0
    ):
        """Async version using servo smooth movement if available."""
        if hasattr(servo_controller, 'smooth_move_to_angle'):
            # Move both servos concurrently
            await asyncio.gather(
                servo_controller.smooth_move_to_angle("pan", pan_angle, speed),
                servo_controller.smooth_move_to_angle("tilt", tilt_angle, speed)
            )
        else:
            # Fallback to direct movement
            await asyncio.to_thread(self.move_to_position, servo_controller, pan_angle, tilt_angle)