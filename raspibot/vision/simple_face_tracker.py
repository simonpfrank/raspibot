"""Simple face tracker focused on core functionality."""

import time
from typing import Optional, Tuple, List

from .face_detector import FaceDetector
from .face_stability import FaceStabilityFilter
from ..movement.pan_tilt import PanTiltSystem
from ..config.hardware_config import FACE_MOVEMENT_THRESHOLD, FACE_MOVEMENT_SCALE
from ..utils.logging_config import setup_logging


class SimpleFaceTracker:
    """Simple face tracker - detect faces and center camera on the largest stable face."""
    
    def __init__(self, pan_tilt: PanTiltSystem, 
                 camera_width: int = 1280, 
                 camera_height: int = 480):
        """
        Initialize simple face tracker.
        
        Args:
            pan_tilt: Pan/tilt system for camera movement
            camera_width: Camera width in pixels
            camera_height: Camera height in pixels
        """
        self.pan_tilt = pan_tilt
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.face_detector = FaceDetector()
        self.stability_filter = FaceStabilityFilter()
        self.logger = setup_logging(__name__)
        
        # Movement settings
        self.movement_threshold = FACE_MOVEMENT_THRESHOLD
        self.movement_scale = FACE_MOVEMENT_SCALE
        
        # Tracking state
        self.last_face_time = time.time()
        
        self.logger.info(f"Simple face tracker initialized: {camera_width}x{camera_height}")
    
    def track_face(self, frame) -> Tuple[Optional[Tuple[int, int, int, int]], List[Tuple[int, int, int, int]]]:
        """
        Track faces and move camera to center on the largest stable face.
        
        Args:
            frame: Camera frame for face detection
            
        Returns:
            Tuple of (largest_stable_face, all_detected_faces)
        """
        # Detect all faces
        all_faces = self.face_detector.detect_faces(frame)
        
        if not all_faces:
            return None, []
        
        # Get the largest face
        largest_face = self.face_detector.get_largest_face(all_faces)
        
        if largest_face:
            # Check if face is stable enough to track
            stable_face = self.stability_filter.check_face_stability(largest_face)
            
            if stable_face:
                self.last_face_time = time.time()
                self._center_on_face(stable_face)
                return stable_face, all_faces
        
        return None, all_faces
    
    def get_stable_faces(self, all_faces: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Get list of faces that are considered stable.
        
        Args:
            all_faces: List of all detected faces
            
        Returns:
            List of stable faces
        """
        return self.stability_filter.get_stable_faces(all_faces)
    
    def reset_tracking(self) -> None:
        """Reset tracking state."""
        self.stability_filter.reset_history()
        self.last_face_time = time.time()
        self.logger.info("Face tracking reset")
    
    def get_time_since_last_face(self) -> float:
        """
        Get time since last face was detected.
        
        Returns:
            Seconds since last face detection
        """
        return time.time() - self.last_face_time
    
    def _center_on_face(self, face: Tuple[int, int, int, int]) -> None:
        """
        Center camera on face using coordinate conversion.
        
        Args:
            face: Face rectangle as (x, y, w, h)
        """
        face_x, face_y = self._get_face_center(face)
        
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
    
    def _get_face_center(self, face: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Calculate face center from bounding box."""
        x, y, w, h = face
        return (x + w // 2, y + h // 2) 