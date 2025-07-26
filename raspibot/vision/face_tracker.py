"""Face tracking with optional advanced features."""

import time
from typing import Optional, Tuple, List

from .simple_face_tracker import SimpleFaceTracker
from .search_pattern import SearchPattern, SearchDirection
from ..movement.pan_tilt import PanTiltSystem
from ..config.hardware_config import SLEEP_TIMEOUT, SEARCH_PATTERN_ENABLED
from ..utils.logging_config import setup_logging


class FaceTracker:
    """
    Face tracker with optional advanced features.
    
    This class provides backward compatibility while using the new simplified components.
    For basic usage, consider using SimpleFaceTracker directly.
    """
    
    def __init__(self, pan_tilt: PanTiltSystem, 
                 camera_width: int = 1280, 
                 camera_height: int = 480):
        """
        Initialize face tracker with optional advanced features.
        
        Args:
            pan_tilt: Pan/tilt system for camera movement
            camera_width: Camera width in pixels
            camera_height: Camera height in pixels
        """
        self.pan_tilt = pan_tilt
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.logger = setup_logging(__name__)
        
        # Core tracking using simplified tracker
        self.simple_tracker = SimpleFaceTracker(pan_tilt, camera_width, camera_height)
        
        # Advanced features (optional)
        self.sleep_timeout = SLEEP_TIMEOUT
        self.is_sleeping = False
        
        # Search pattern integration
        self.search_pattern_enabled = SEARCH_PATTERN_ENABLED
        self.search_pattern: Optional[SearchPattern] = None
        self.last_search_time = 0
        self.search_interval = 30  # Search every 30 seconds if no faces
        
        if self.search_pattern_enabled:
            self.search_pattern = SearchPattern(pan_tilt, camera_width, camera_height)
            self.logger.info("Search pattern system initialized")
        
        self.logger.info(f"Face tracker initialized with advanced features: "
                        f"{camera_width}x{camera_height}, search_enabled={self.search_pattern_enabled}")
    
    def track_face(self, frame) -> Tuple[Optional[Tuple[int, int, int, int]], List[Tuple[int, int, int, int]]]:
        """
        Track faces and move camera with advanced features.
        
        Args:
            frame: Camera frame for face detection
            
        Returns:
            Tuple of (largest_stable_face, all_detected_faces)
        """
        # Use simple tracker for core functionality
        stable_face, all_faces = self.simple_tracker.track_face(frame)
        
        if stable_face:
            # Stop search pattern if active
            if self.search_pattern and self.search_pattern.is_searching_active():
                self.search_pattern.stop_search()
            
            # Wake up if sleeping
            if self.is_sleeping:
                self._wake_up()
            
            return stable_face, all_faces
        
        # No stable face found - handle advanced features
        # Check if we should start search pattern
        if (self.search_pattern_enabled and 
            self.search_pattern and 
            not self.search_pattern.is_searching_active() and
            not self.is_sleeping and
            time.time() - self.simple_tracker.last_face_time > self.search_interval):
            
            self._start_search_pattern(frame)
        
        # Check if we should go to sleep
        if (not self.is_sleeping and 
            time.time() - self.simple_tracker.last_face_time > self.sleep_timeout):
            self._go_to_sleep()
        
        return None, all_faces
    
    def get_stable_faces(self, all_faces: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Get list of faces that are considered stable."""
        return self.simple_tracker.get_stable_faces(all_faces)
    
    # Sleep/Wake functionality
    def _go_to_sleep(self) -> None:
        """Go to sleep position with dramatic sequence."""
        if self.is_sleeping:
            return
        
        self.logger.info("No faces detected for timeout period, going to sleep")
        self.is_sleeping = True
        
        try:
            # Dramatic sleep sequence
            self.logger.info("Performing dramatic sleep sequence")
            
            # Look left and horizontal
            self.pan_tilt.move_to_coordinates(-0.5, 0)
            time.sleep(0.5)
            
            # Look right and horizontal  
            self.pan_tilt.move_to_coordinates(0.5, 0)
            time.sleep(0.5)
            
            # Look center and slightly up
            self.pan_tilt.move_to_coordinates(0, 0.3)
            time.sleep(0.5)
            
            # Look center and down (sleep position)
            self.pan_tilt.move_to_coordinates(0, -1.0)
            
            self.logger.info("Sleep sequence complete")
            
        except Exception as e:
            self.logger.error(f"Error during sleep sequence: {e}")
    
    def _wake_up(self) -> None:
        """Wake up from sleep mode with dramatic sequence."""
        if not self.is_sleeping:
            return
        
        self.logger.info("Waking up from sleep mode")
        self.is_sleeping = False
        
        try:
            # Dramatic wake sequence (reverse of sleep)
            self.logger.info("Performing dramatic wake sequence")
            
            # Look center and slightly up
            self.pan_tilt.move_to_coordinates(0, 0.3)
            time.sleep(0.3)
            
            # Look right and horizontal
            self.pan_tilt.move_to_coordinates(0.5, 0)
            time.sleep(0.3)
            
            # Look left and horizontal
            self.pan_tilt.move_to_coordinates(-0.5, 0)
            time.sleep(0.3)
            
            # Look center and horizontal (ready position)
            self.pan_tilt.move_to_coordinates(0, 0)
            
            self.logger.info("Wake sequence complete")
            
        except Exception as e:
            self.logger.error(f"Error during wake sequence: {e}")
    
    def get_sleep_status(self) -> bool:
        """Check if currently in sleep mode."""
        return self.is_sleeping
    
    def force_wake_up(self) -> None:
        """Force wake up from sleep mode."""
        if self.is_sleeping:
            self._wake_up()
    
    def force_sleep(self) -> None:
        """Force sleep mode."""
        if not self.is_sleeping:
            self._go_to_sleep()
    
    def reset_sleep_timer(self) -> None:
        """Reset the sleep timer."""
        self.simple_tracker.last_face_time = time.time()
    
    def get_time_until_sleep(self) -> float:
        """Get time remaining until sleep mode."""
        if self.is_sleeping:
            return 0
        
        elapsed = time.time() - self.simple_tracker.last_face_time
        remaining = max(0, self.sleep_timeout - elapsed)
        return remaining
    
    # Search pattern methods
    def _start_search_pattern(self, frame) -> None:
        """Start search pattern if conditions are met."""
        if not self.search_pattern or self.search_pattern.is_searching_active():
            return
        
        self.logger.info("No faces detected, starting search pattern")
        self.last_search_time = time.time()
        
        # Define face detection callback for search pattern
        def face_detection_callback() -> bool:
            """Check for faces at current search position."""
            from .face_detector import FaceDetector
            detector = FaceDetector()
            faces = detector.detect_faces(frame)
            return len(faces) > 0
        
        # Start search pattern
        faces_found = self.search_pattern.start_search(face_detection_callback)
        
        if faces_found:
            self.logger.info("Faces found during search pattern")
            self.simple_tracker.last_face_time = time.time()  # Reset face timer
        else:
            self.logger.info("Search pattern completed without finding faces")
    
    def get_search_status(self) -> dict:
        """Get search pattern status information."""
        if not self.search_pattern:
            return {
                "enabled": False,
                "active": False,
                "progress": (0, 0),
                "time_elapsed": 0.0,
                "time_remaining": 0.0
            }
        
        return {
            "enabled": self.search_pattern_enabled,
            "active": self.search_pattern.is_searching_active(),
            "progress": self.search_pattern.get_search_progress(),
            "time_elapsed": self.search_pattern.get_search_time_elapsed(),
            "time_remaining": self.search_pattern.get_search_time_remaining()
        }
    
    def force_start_search(self) -> bool:
        """Force start search pattern immediately."""
        if not self.search_pattern:
            return False
        
        if self.search_pattern.is_searching_active():
            self.logger.warning("Search already in progress")
            return False
        
        self.logger.info("Force starting search pattern")
        return self.search_pattern.start_search(lambda: False)  # Dummy callback
    
    def stop_search(self) -> None:
        """Stop current search pattern."""
        if self.search_pattern:
            self.search_pattern.stop_search()
    
    def set_search_interval(self, interval: float) -> None:
        """Set the search interval."""
        self.search_interval = max(5.0, interval)  # Minimum 5 seconds
        self.logger.info(f"Search interval set to {self.search_interval} seconds") 