"""Pan/tilt camera control system.

This module provides coordinate-based pan/tilt control for camera movement,
using the abstract servo interface for hardware independence.
"""

import math
import time
from typing import Tuple, Optional

from raspibot.hardware.servos.servo_interface import ServoInterface
from raspibot.exceptions import HardwareException
from raspibot.utils.logging_config import setup_logging
from raspibot.settings.config import (
    SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE, SERVO_PAN_CENTER,
    SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE, SERVO_TILT_CENTER,
    SERVO_TILT_UP_ANGLE, SERVO_TILT_DOWN_ANGLE
)


class PanTiltSystem:
    """Pan/tilt camera control system using servo controllers."""
    
    def __init__(
        self,
        servo_controller: ServoInterface,
        pan_channel: int = 0,
        tilt_channel: int = 1,
        pan_range: Optional[Tuple[float, float]] = None,
        tilt_range: Optional[Tuple[float, float]] = None,
        pan_center: Optional[float] = None,
        tilt_center: Optional[float] = None
    ):
        """Initialize pan/tilt system.
        
        Args:
            servo_controller: Servo controller instance
            pan_channel: Servo channel for pan movement
            tilt_channel: Servo channel for tilt movement
            pan_range: Pan angle range (min, max) in degrees (defaults to config)
            tilt_range: Tilt angle range (min, max) in degrees (defaults to config)
            pan_center: Center position for pan servo (defaults to config)
            tilt_center: Center position for tilt servo (defaults to config)
        """
        self.logger = setup_logging(__name__)
        self.servo_controller = servo_controller
        self.pan_channel = pan_channel
        self.tilt_channel = tilt_channel
        
        # Use config defaults if not specified
        self.pan_range = pan_range or (SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE)
        self.tilt_range = tilt_range or (SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE)
        self.pan_center = pan_center or SERVO_PAN_CENTER
        self.tilt_center = tilt_center or SERVO_TILT_CENTER
        
        # Current positions
        self.current_pan = pan_center
        self.current_tilt = tilt_center
        
        # Validate channels are available
        available_channels = servo_controller.get_available_channels()
        if pan_channel not in available_channels:
            raise HardwareException(f"Pan channel {pan_channel} not available")
        if tilt_channel not in available_channels:
            raise HardwareException(f"Tilt channel {tilt_channel} not available")
        
        # Initialize to center position
        self.center_camera()
        
        self.logger.info(f"Pan/tilt system initialized with {servo_controller.get_controller_type()} controller")
        self.logger.info(f"Pan: channel {pan_channel}, range {self.pan_range}, center {self.pan_center}")
        self.logger.info(f"Tilt: channel {tilt_channel}, range {self.tilt_range}, center {self.tilt_center}")
    
    def center_camera(self) -> None:
        """Move camera to center position."""
        self.logger.info("Moving camera to center position")
        self.move_to_angles(self.pan_center, self.tilt_center)
    
    def point_up(self) -> None:
        """Point camera straight up (tilt to 90°)."""
        self.logger.info("Pointing camera straight up")
        self.move_to_angles(self.current_pan, SERVO_TILT_UP_ANGLE)
    
    def point_down(self) -> None:
        """Point camera straight down (tilt to 310°)."""
        self.logger.info("Pointing camera straight down")
        self.move_to_angles(self.current_pan, SERVO_TILT_DOWN_ANGLE)
    
    def point_horizontal(self) -> None:
        """Point camera horizontally (tilt to center)."""
        self.logger.info("Pointing camera horizontally")
        self.move_to_angles(self.current_pan, self.tilt_center)
    
    def move_to_angles(self, pan_angle: float, tilt_angle: float) -> None:
        """Move camera to specific pan and tilt angles.
        
        Args:
            pan_angle: Pan angle in degrees
            tilt_angle: Tilt angle in degrees
        """
        # Validate angles
        if not self.pan_range[0] <= pan_angle <= self.pan_range[1]:
            raise HardwareException(f"Pan angle {pan_angle}° out of range {self.pan_range}")
        if not self.tilt_range[0] <= tilt_angle <= self.tilt_range[1]:
            raise HardwareException(f"Tilt angle {tilt_angle}° out of range {self.tilt_range}")
        
        # Move servos
        self.servo_controller.set_servo_angle(self.pan_channel, pan_angle)
        self.servo_controller.set_servo_angle(self.tilt_channel, tilt_angle)
        
        # Update current positions
        self.current_pan = pan_angle
        self.current_tilt = tilt_angle
        
        self.logger.debug(f"Camera moved to pan={pan_angle}°, tilt={tilt_angle}°")
    
    def move_to_coordinates(self, x: float, y: float) -> None:
        """Move camera to coordinates (x, y) where (0,0) is center.
        
        Args:
            x: X coordinate (-1.0 to 1.0, where 0 is center)
            y: Y coordinate (-1.0 to 1.0, where 0 is center)
        """
        # Clamp coordinates to valid range
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        # Convert coordinates to angles
        pan_angle = self.pan_center + (x * (self.pan_range[1] - self.pan_range[0]) / 2)
        tilt_angle = self.tilt_center + (y * (self.tilt_range[1] - self.tilt_range[0]) / 2)
        
        # Clamp to servo ranges
        pan_angle = max(self.pan_range[0], min(self.pan_range[1], pan_angle))
        tilt_angle = max(self.tilt_range[0], min(self.tilt_range[1], tilt_angle))
        
        self.move_to_angles(pan_angle, tilt_angle)
    
    def smooth_move_to_angles(
        self,
        pan_angle: float,
        tilt_angle: float,
        speed: float = 1.0
    ) -> None:
        """Smoothly move camera to specific pan and tilt angles.
        
        Args:
            pan_angle: Pan angle in degrees
            tilt_angle: Tilt angle in degrees
            speed: Movement speed (0.1 to 1.0)
        """
        # Validate angles
        if not self.pan_range[0] <= pan_angle <= self.pan_range[1]:
            raise HardwareException(f"Pan angle {pan_angle}° out of range {self.pan_range}")
        if not self.tilt_range[0] <= tilt_angle <= self.tilt_range[1]:
            raise HardwareException(f"Tilt angle {tilt_angle}° out of range {self.tilt_range}")
        
        # Move servos smoothly
        self.servo_controller.smooth_move_to_angle(self.pan_channel, pan_angle, speed)
        self.servo_controller.smooth_move_to_angle(self.tilt_channel, tilt_angle, speed)
        
        # Update current positions
        self.current_pan = pan_angle
        self.current_tilt = tilt_angle
        
        self.logger.debug(f"Camera smoothly moved to pan={pan_angle}°, tilt={tilt_angle}°")
    
    def smooth_move_to_coordinates(
        self,
        x: float,
        y: float,
        speed: float = 1.0
    ) -> None:
        """Smoothly move camera to coordinates (x, y).
        
        Args:
            x: X coordinate (-1.0 to 1.0, where 0 is center)
            y: Y coordinate (-1.0 to 1.0, where 0 is center)
            speed: Movement speed (0.1 to 1.0)
        """
        # Clamp coordinates to valid range
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        # Convert coordinates to angles
        pan_angle = self.pan_center + (x * (self.pan_range[1] - self.pan_range[0]) / 2)
        tilt_angle = self.tilt_center + (y * (self.tilt_range[1] - self.tilt_range[0]) / 2)
        
        # Clamp to servo ranges
        pan_angle = max(self.pan_range[0], min(self.pan_range[1], pan_angle))
        tilt_angle = max(self.tilt_range[0], min(self.tilt_range[1], tilt_angle))
        
        self.smooth_move_to_angles(pan_angle, tilt_angle, speed)
    
    def track_target(self, target_x: float, target_y: float, speed: float = 0.8) -> None:
        """Track a moving target by smoothly following coordinates.
        
        Args:
            target_x: Target X coordinate (-1.0 to 1.0)
            target_y: Target Y coordinate (-1.0 to 1.0)
            speed: Tracking speed (0.1 to 1.0)
        """
        # Clamp target coordinates
        target_x = max(-1.0, min(1.0, target_x))
        target_y = max(-1.0, min(1.0, target_y))
        
        # Convert to angles
        pan_angle = self.pan_center + (target_x * (self.pan_range[1] - self.pan_range[0]) / 2)
        tilt_angle = self.tilt_center + (target_y * (self.tilt_range[1] - self.tilt_range[0]) / 2)
        
        # Clamp to servo ranges
        pan_angle = max(self.pan_range[0], min(self.pan_range[1], pan_angle))
        tilt_angle = max(self.tilt_range[0], min(self.tilt_range[1], tilt_angle))
        
        # Smooth movement for tracking
        self.smooth_move_to_angles(pan_angle, tilt_angle, speed)
    
    def get_current_position(self) -> Tuple[float, float]:
        """Get current pan and tilt angles.
        
        Returns:
            Tuple of (pan_angle, tilt_angle)
        """
        return (self.current_pan, self.current_tilt)
    
    def get_current_coordinates(self) -> Tuple[float, float]:
        """Get current position as coordinates.
        
        Returns:
            Tuple of (x, y) coordinates where (0,0) is center
        """
        x = (self.current_pan - self.pan_center) / ((self.pan_range[1] - self.pan_range[0]) / 2)
        y = (self.current_tilt - self.tilt_center) / ((self.tilt_range[1] - self.tilt_range[0]) / 2)
        
        # Clamp to valid range
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        return (x, y)
    
    def emergency_stop(self) -> None:
        """Emergency stop all camera movement."""
        self.logger.warning("Emergency stop triggered for pan/tilt system")
        self.servo_controller.emergency_stop()
    
    def shutdown(self) -> None:
        """Safely shutdown the pan/tilt system."""
        self.logger.info("Shutting down pan/tilt system")
        self.center_camera()
        time.sleep(0.5)  # Allow time for movement to complete
        self.servo_controller.shutdown() 