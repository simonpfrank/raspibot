"""Systematic search patterns for face detection.

This module implements raster scan search patterns that systematically
cover the camera's field of view to find faces when none are detected.
"""

import time
import math
from typing import List, Tuple, Optional, Callable
from enum import Enum

from ..movement.pan_tilt import PanTiltSystem
from ..config.config import (
    SEARCH_PAN_STEPS, SEARCH_TILT_STEPS, SEARCH_MOVEMENT_SPEED,
    SEARCH_STABILIZATION_DELAY, SEARCH_FACE_DETECTION_DELAY,
    SEARCH_PATTERN_TIMEOUT, SEARCH_RETURN_TO_CENTER,
    SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE,
    SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE
)
from ..utils.logging_config import setup_logging


class SearchDirection(Enum):
    """Search pattern directions."""
    DOWN_FIRST = "down_first"  # Start from top, go down, then up
    UP_FIRST = "up_first"      # Start from bottom, go up, then down


class SearchPattern:
    """Systematic raster scan search pattern for face detection."""
    
    def __init__(self, pan_tilt: PanTiltSystem, 
                 camera_width: int = 1280, 
                 camera_height: int = 480,
                 direction: SearchDirection = SearchDirection.DOWN_FIRST):
        """
        Initialize search pattern.
        
        Args:
            pan_tilt: Pan/tilt system for camera movement
            camera_width: Camera width in pixels
            camera_height: Camera height in pixels
            direction: Search direction preference
        """
        self.pan_tilt = pan_tilt
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.direction = direction
        self.logger = setup_logging(__name__)
        
        # Search configuration
        self.pan_steps = SEARCH_PAN_STEPS
        self.tilt_steps = SEARCH_TILT_STEPS
        self.movement_speed = SEARCH_MOVEMENT_SPEED
        self.stabilization_delay = SEARCH_STABILIZATION_DELAY
        self.face_detection_delay = SEARCH_FACE_DETECTION_DELAY
        self.pattern_timeout = SEARCH_PATTERN_TIMEOUT
        self.return_to_center = SEARCH_RETURN_TO_CENTER
        
        # Search state
        self.is_searching = False
        self.search_start_time = 0
        self.current_position = (0, 0)
        self.search_positions: List[Tuple[float, float]] = []
        self.current_position_index = 0
        
        # Calculate search positions
        self._calculate_search_positions()
        
        self.logger.info(f"Search pattern initialized: {self.pan_steps}x{self.tilt_steps} grid, "
                        f"speed={self.movement_speed}, direction={self.direction.value}")
    
    def _calculate_search_positions(self) -> None:
        """Calculate all search positions in raster scan pattern."""
        self.search_positions = []
        
        # Calculate pan and tilt ranges
        pan_range = SERVO_PAN_MAX_ANGLE - SERVO_PAN_MIN_ANGLE
        tilt_range = SERVO_TILT_MAX_ANGLE - SERVO_TILT_MIN_ANGLE
        
        # Calculate step sizes
        pan_step_size = pan_range / (self.pan_steps - 1) if self.pan_steps > 1 else 0
        tilt_step_size = tilt_range / (self.tilt_steps - 1) if self.tilt_steps > 1 else 0
        
        # Generate tilt levels based on direction
        if self.direction == SearchDirection.DOWN_FIRST:
            tilt_levels = [SERVO_TILT_MIN_ANGLE + i * tilt_step_size for i in range(self.tilt_steps)]
        else:  # UP_FIRST
            tilt_levels = [SERVO_TILT_MAX_ANGLE - i * tilt_step_size for i in range(self.tilt_steps)]
        
        # Generate raster scan pattern
        for tilt_index, tilt_level in enumerate(tilt_levels):
            # Alternate direction for each tilt level (raster scan)
            if tilt_index % 2 == 0:
                # Left to right
                for i in range(self.pan_steps):
                    pan_angle = SERVO_PAN_MIN_ANGLE + i * pan_step_size
                    self.search_positions.append((pan_angle, tilt_level))
            else:
                # Right to left
                for i in range(self.pan_steps - 1, -1, -1):
                    pan_angle = SERVO_PAN_MIN_ANGLE + i * pan_step_size
                    self.search_positions.append((pan_angle, tilt_level))
        
        self.logger.info(f"Generated {len(self.search_positions)} search positions")
    
    def start_search(self, face_detection_callback: Callable[[], bool]) -> bool:
        """
        Start systematic search pattern.
        
        Args:
            face_detection_callback: Function to call for face detection at each position
                                    Should return True if faces are found
            
        Returns:
            True if faces were found during search, False if search completed without finding faces
        """
        if self.is_searching:
            self.logger.warning("Search already in progress")
            return False
        
        self.logger.info("Starting systematic search pattern")
        self.is_searching = True
        self.search_start_time = time.time()
        self.current_position_index = 0
        
        try:
            # Move to first search position
            if not self.search_positions:
                self.logger.error("No search positions calculated")
                return False
            
            # Start from center tilt, leftmost pan
            first_pan, first_tilt = self.search_positions[0]
            self.logger.info(f"Moving to first search position: pan={first_pan:.1f}°, tilt={first_tilt:.1f}°")
            
            self.pan_tilt.smooth_move_to_angles(first_pan, first_tilt, self.movement_speed)
            time.sleep(self.stabilization_delay)
            
            # Perform search pattern
            return self._execute_search_pattern(face_detection_callback)
            
        except Exception as e:
            self.logger.error(f"Error during search pattern: {e}")
            return False
        finally:
            self.is_searching = False
    
    def _execute_search_pattern(self, face_detection_callback: Callable[[], bool]) -> bool:
        """
        Execute the search pattern step by step.
        
        Args:
            face_detection_callback: Function to call for face detection
            
        Returns:
            True if faces were found, False if search completed without finding faces
        """
        for i, (pan_angle, tilt_angle) in enumerate(self.search_positions):
            # Check timeout
            if time.time() - self.search_start_time > self.pattern_timeout:
                self.logger.warning("Search pattern timeout reached")
                break
            
            # Move to position
            self.logger.debug(f"Search position {i+1}/{len(self.search_positions)}: "
                            f"pan={pan_angle:.1f}°, tilt={tilt_angle:.1f}°")
            
            self.pan_tilt.smooth_move_to_angles(pan_angle, tilt_angle, self.movement_speed)
            time.sleep(self.stabilization_delay)
            
            # Check for faces at this position
            self.logger.debug("Checking for faces at current position")
            if face_detection_callback():
                self.logger.info(f"Faces found at search position {i+1}: "
                               f"pan={pan_angle:.1f}°, tilt={tilt_angle:.1f}°")
                return True
            
            # Brief delay for face detection
            time.sleep(self.face_detection_delay)
        
        self.logger.info("Search pattern completed without finding faces")
        return False
    
    def stop_search(self) -> None:
        """Stop the current search pattern."""
        if not self.is_searching:
            return
        
        self.logger.info("Stopping search pattern")
        self.is_searching = False
        
        # Return to center if configured
        if self.return_to_center:
            self.logger.info("Returning to center position")
            self.pan_tilt.center_camera()
    
    def is_searching_active(self) -> bool:
        """
        Check if search is currently active.
        
        Returns:
            True if search is in progress
        """
        return self.is_searching
    
    def get_search_progress(self) -> Tuple[int, int]:
        """
        Get current search progress.
        
        Returns:
            Tuple of (current_position, total_positions)
        """
        if not self.is_searching:
            return (0, len(self.search_positions))
        
        return (self.current_position_index, len(self.search_positions))
    
    def get_search_time_elapsed(self) -> float:
        """
        Get time elapsed since search started.
        
        Returns:
            Time elapsed in seconds, or 0 if not searching
        """
        if not self.is_searching:
            return 0.0
        
        return time.time() - self.search_start_time
    
    def get_search_time_remaining(self) -> float:
        """
        Get estimated time remaining for search pattern.
        
        Returns:
            Time remaining in seconds, or 0 if not searching
        """
        if not self.is_searching:
            return 0.0
        
        elapsed = self.get_search_time_elapsed()
        remaining = max(0, self.pattern_timeout - elapsed)
        return remaining
    
    def set_search_parameters(self, 
                            pan_steps: Optional[int] = None,
                            tilt_steps: Optional[int] = None,
                            movement_speed: Optional[float] = None,
                            direction: Optional[SearchDirection] = None) -> None:
        """
        Update search parameters.
        
        Args:
            pan_steps: Number of pan steps per tilt level
            tilt_steps: Number of tilt levels to scan
            movement_speed: Movement speed (0.1-1.0)
            direction: Search direction
        """
        if self.is_searching:
            self.logger.warning("Cannot change parameters during active search")
            return
        
        # Update parameters
        if pan_steps is not None:
            self.pan_steps = pan_steps
        if tilt_steps is not None:
            self.tilt_steps = tilt_steps
        if movement_speed is not None:
            self.movement_speed = max(0.1, min(1.0, movement_speed))
        if direction is not None:
            self.direction = direction
        
        # Recalculate search positions
        self._calculate_search_positions()
        
        self.logger.info(f"Search parameters updated: {self.pan_steps}x{self.tilt_steps} grid, "
                        f"speed={self.movement_speed}, direction={self.direction.value}") 