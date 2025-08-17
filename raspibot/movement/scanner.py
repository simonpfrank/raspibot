#!/usr/bin/env python3
"""Scan movement patterns for room scanning.

Handles servo movement patterns for systematic room scanning with optimal
camera position coverage.
"""

import asyncio
import time
from typing import List
from raspibot.settings.config import (
    SERVO_PAN_CHANNEL,
    SERVO_TILT_CHANNEL,
    SERVO_PAN_MIN_ANGLE,
    SERVO_PAN_MAX_ANGLE,
)


class ScanPattern:
    """Manages servo movement for room scanning."""

    def __init__(self, fov_degrees: float = 66.3, overlap_degrees: float = 10.0):
        """Initialize scan pattern with camera FOV and desired overlap."""
        self.fov_degrees = fov_degrees
        self.overlap_degrees = overlap_degrees

    def calculate_positions(self) -> List[float]:
        """Calculate pan angles for complete room coverage."""
        positions = []

        # Calculate effective FOV per position (accounting for overlap)
        effective_fov = self.fov_degrees - self.overlap_degrees

        # Calculate scan range
        scan_range = SERVO_PAN_MAX_ANGLE - SERVO_PAN_MIN_ANGLE

        # Calculate number of positions needed
        num_positions = int(scan_range / effective_fov) + 1

        # Generate evenly spaced positions
        for i in range(num_positions):
            position = SERVO_PAN_MIN_ANGLE + (i * effective_fov)
            if position <= SERVO_PAN_MAX_ANGLE:
                positions.append(position)

        # Ensure we cover the full range
        if positions and positions[-1] < SERVO_PAN_MAX_ANGLE - 5:  # 5 degree tolerance
            positions.append(SERVO_PAN_MAX_ANGLE)

        return positions

    def move_to_position(self, servo_controller, pan_angle: float, tilt_angle: float):
        """Move servos to scan position (direct movement)."""
        print(f"Moving servos to Pan={pan_angle:.1f}°, Tilt={tilt_angle:.1f}°")
        servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, pan_angle)
        servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, tilt_angle)
        print(f"Servo movement completed")

    async def move_to_position_async(self, servo_controller, pan_angle: float, tilt_angle: float, speed: float = 1.0):
        """Async version using servo smooth movement if available."""
        if hasattr(servo_controller, 'smooth_move_to_angle'):
            # Move both servos concurrently
            await asyncio.gather(
                servo_controller.smooth_move_to_angle(SERVO_PAN_CHANNEL, pan_angle, speed),
                servo_controller.smooth_move_to_angle(SERVO_TILT_CHANNEL, tilt_angle, speed)
            )
        else:
            # Fallback to direct movement
            await asyncio.to_thread(self.move_to_position, servo_controller, pan_angle, tilt_angle)