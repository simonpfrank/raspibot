"""Face tracking with stability filtering and coordinate conversion."""

import time
import math
from typing import Optional, Tuple, List

from .face_detector import FaceDetector
from .search_pattern import SearchPattern, SearchDirection
from ..movement.pan_tilt import PanTiltSystem
from ..config.hardware_config import (
    FACE_MOVEMENT_THRESHOLD, FACE_MOVEMENT_SCALE, FACE_STABILITY_THRESHOLD,
    FACE_STABILITY_FRAMES, SLEEP_TIMEOUT, SEARCH_PATTERN_ENABLED
)
from ..utils.logging_config import setup_logging


class FaceTracker:
    """Simple face tracking - center camera on largest stable face with search patterns."""
    
    def __init__(self, pan_tilt: PanTiltSystem, 
                 camera_width: int = 1280, 
                 camera_height: int = 480):
        """
        Initialize face tracker.
        
        Args:
            pan_tilt: Pan/tilt system for camera movement
            camera_width: Camera width in pixels
            camera_height: Camera height in pixels
        """
        self.pan_tilt = pan_tilt
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.face_detector = FaceDetector()
        self.logger = setup_logging(__name__)
        
        # Timing and sleep management
        self.last_face_time = time.time()
        self.sleep_timeout = SLEEP_TIMEOUT
        self.is_sleeping = False
        
        # Movement and stability thresholds
        self.movement_threshold = FACE_MOVEMENT_THRESHOLD
        self.movement_scale = FACE_MOVEMENT_SCALE
        self.stability_threshold = FACE_STABILITY_THRESHOLD
        self.stability_frames = FACE_STABILITY_FRAMES
        
        # Face history for stability tracking
        self.face_history: List[Tuple[float, Tuple[int, int], Tuple[int, int, int, int]]] = []
        
        # Search pattern integration
        self.search_pattern_enabled = SEARCH_PATTERN_ENABLED
        self.search_pattern: Optional[SearchPattern] = None
        self.last_search_time = 0
        self.search_interval = 30  # Search every 30 seconds if no faces
        
        if self.search_pattern_enabled:
            self.search_pattern = SearchPattern(pan_tilt, camera_width, camera_height)
            self.logger.info("Search pattern system initialized")
        
        self.logger.info(f"Face tracker initialized: {camera_width}x{camera_height}, "
                        f"movement_threshold={self.movement_threshold}, "
                        f"stability_threshold={self.stability_threshold}, "
                        f"search_enabled={self.search_pattern_enabled}")
    
    def track_face(self, frame) -> Tuple[Optional[Tuple[int, int, int, int]], List[Tuple[int, int, int, int]]]:
        """
        Track faces and move camera. 
        
        Args:
            frame: Camera frame for face detection
            
        Returns:
            Tuple of (largest_stable_face, all_detected_faces)
        """
        # Detect all faces
        all_faces = self.face_detector.detect_faces(frame)
        largest_face = self.face_detector.get_largest_face(all_faces)
        
        if largest_face:
            stable_face = self._check_face_stability(largest_face)
            if stable_face:
                self.last_face_time = time.time()
                self._center_on_face(stable_face)
                
                # Stop search pattern if active
                if self.search_pattern and self.search_pattern.is_searching_active():
                    self.search_pattern.stop_search()
                
                # Wake up if sleeping
                if self.is_sleeping:
                    self._wake_up()
                
                return stable_face, all_faces
        
        # Clean up old face history
        self._cleanup_face_history()
        
        # Check if we should start search pattern
        if (self.search_pattern_enabled and 
            self.search_pattern and 
            not self.search_pattern.is_searching_active() and
            not self.is_sleeping and
            time.time() - self.last_face_time > self.search_interval):
            
            self._start_search_pattern(frame)
        
        # Check if we should go to sleep
        if not self.is_sleeping and time.time() - self.last_face_time > self.sleep_timeout:
            self._go_to_sleep()
        
        return None, all_faces
    
    def get_stable_faces(self, all_faces: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Get list of faces that are considered stable.
        
        Args:
            all_faces: List of all detected faces
            
        Returns:
            List of stable faces
        """
        stable_faces = []
        
        for face in all_faces:
            if self._is_face_stable(face):
                stable_faces.append(face)
        
        return stable_faces
    
    def _check_face_stability(self, face: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        """
        Check if face is stable enough to track (not fast-moving).
        
        Args:
            face: Face rectangle as (x, y, w, h)
            
        Returns:
            Face if stable, None if not stable enough
        """
        face_center = self.face_detector.get_face_center(face)
        current_time = time.time()
        
        # Add current face to history
        self.face_history.append((current_time, face_center, face))
        
        # Keep only recent history (2 second window)
        self.face_history = [(t, center, f) for t, center, f in self.face_history 
                            if current_time - t < 2.0]
        
        # Need at least stability_frames to consider stable
        if len(self.face_history) < self.stability_frames:
            self.logger.debug(f"Face not stable: only {len(self.face_history)} frames, need {self.stability_frames}")
            return None
        
        # Check if recent faces are close together (stable)
        recent_centers = [center for _, center, _ in self.face_history[-self.stability_frames:]]
        
        for i in range(1, len(recent_centers)):
            distance = self._calculate_distance(recent_centers[i], recent_centers[0])
            if distance > self.stability_threshold:
                self.logger.debug(f"Face not stable: movement {distance:.1f} > {self.stability_threshold}")
                return None  # Face is moving too fast, ignore
        
        self.logger.debug(f"Face is stable: {self.stability_frames} frames within {self.stability_threshold} pixels")
        return face  # Face is stable, track it
    
    def _is_face_stable(self, face: Tuple[int, int, int, int]) -> bool:
        """
        Check if a specific face is currently considered stable.
        
        Args:
            face: Face rectangle to check
            
        Returns:
            True if face is stable
        """
        face_center = self.face_detector.get_face_center(face)
        current_time = time.time()
        
        # Check if this face center is close to any recent stable faces
        for hist_time, hist_center, hist_face in reversed(self.face_history[-self.stability_frames:]):
            if current_time - hist_time > 1.0:  # Only check recent history
                continue
            
            distance = self._calculate_distance(face_center, hist_center)
            if distance <= self.stability_threshold:
                return True
        
        return False
    
    def _cleanup_face_history(self) -> None:
        """Remove old face history entries."""
        current_time = time.time()
        self.face_history = [(t, center, f) for t, center, f in self.face_history 
                            if current_time - t < 2.0]
    
    def _center_on_face(self, face: Tuple[int, int, int, int]) -> None:
        """
        Center camera on face using simple coordinate conversion.
        
        Note: This coordinate system is designed to be extensible for future 
        view mapping experiments where we'll map camera coordinates to 
        world/room coordinates.
        
        Args:
            face: Face rectangle as (x, y, w, h)
        """
        face_x, face_y = self.face_detector.get_face_center(face)
        
        # Convert to camera center offset
        offset_x = face_x - (self.camera_width // 2)
        offset_y = face_y - (self.camera_height // 2)
        
        # Only move if offset is significant
        if abs(offset_x) > self.movement_threshold or abs(offset_y) > self.movement_threshold:
            # Simple proportion-based movement
            move_x = offset_x / (self.camera_width // 2)   # -1.0 to 1.0
            move_y = offset_y / (self.camera_height // 2)  # -1.0 to 1.0
            
            # Get current position and adjust
            current_x, current_y = self.pan_tilt.get_current_coordinates()
            new_x = max(-1.0, min(1.0, current_x + move_x * self.movement_scale))
            new_y = max(-1.0, min(1.0, current_y + move_y * self.movement_scale))
            
            self.logger.debug(f"Moving servo: face at ({face_x}, {face_y}), "
                            f"offset ({offset_x}, {offset_y}), "
                            f"servo ({current_x:.2f}, {current_y:.2f}) -> ({new_x:.2f}, {new_y:.2f})")
            
            self.pan_tilt.move_to_coordinates(new_x, new_y)
    
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
        """
        Check if currently in sleep mode.
        
        Returns:
            True if sleeping
        """
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
        self.last_face_time = time.time()
    
    def get_time_until_sleep(self) -> float:
        """
        Get time remaining until sleep mode.
        
        Returns:
            Seconds until sleep, or 0 if sleeping or timer expired
        """
        if self.is_sleeping:
            return 0
        
        elapsed = time.time() - self.last_face_time
        remaining = max(0, self.sleep_timeout - elapsed)
        return remaining
    
    def _calculate_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
        """
        Calculate Euclidean distance between two points.
        
        Args:
            point1: First point as (x, y)
            point2: Second point as (x, y)
            
        Returns:
            Distance in pixels
        """
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _start_search_pattern(self, frame) -> None:
        """Start search pattern if conditions are met."""
        if not self.search_pattern or self.search_pattern.is_searching_active():
            return
        
        self.logger.info("No faces detected, starting search pattern")
        self.last_search_time = time.time()
        
        # Define face detection callback for search pattern
        def face_detection_callback() -> bool:
            """Check for faces at current search position."""
            faces = self.face_detector.detect_faces(frame)
            return len(faces) > 0
        
        # Start search pattern
        faces_found = self.search_pattern.start_search(face_detection_callback)
        
        if faces_found:
            self.logger.info("Faces found during search pattern")
            self.last_face_time = time.time()  # Reset face timer
        else:
            self.logger.info("Search pattern completed without finding faces")
    
    def get_search_status(self) -> dict:
        """
        Get search pattern status information.
        
        Returns:
            Dictionary with search status information
        """
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
        """
        Force start search pattern immediately.
        
        Returns:
            True if search started successfully
        """
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
        """
        Set the search interval (how often to search when no faces detected).
        
        Args:
            interval: Search interval in seconds
        """
        self.search_interval = max(5.0, interval)  # Minimum 5 seconds
        self.logger.info(f"Search interval set to {self.search_interval} seconds") 