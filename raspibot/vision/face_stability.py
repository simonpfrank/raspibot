"""Face stability filtering for consistent tracking."""

import time
import math
from typing import List, Tuple, Optional

from ..utils.logging_config import setup_logging


class FaceStabilityFilter:
    """Filters face detections to ensure stable tracking."""
    
    def __init__(self, 
                 stability_threshold: float = 30.0,
                 stability_frames: int = 3,
                 history_window: float = 2.0):
        """
        Initialize face stability filter.
        
        Args:
            stability_threshold: Maximum pixel movement to consider stable
            stability_frames: Number of consecutive frames needed for stability
            history_window: Time window to keep face history (seconds)
        """
        self.stability_threshold = stability_threshold
        self.stability_frames = stability_frames
        self.history_window = history_window
        self.logger = setup_logging(__name__)
        
        # Face history: List of (timestamp, center, face_rect)
        self.face_history: List[Tuple[float, Tuple[int, int], Tuple[int, int, int, int]]] = []
        
        self.logger.info(f"Face stability filter initialized: "
                        f"threshold={stability_threshold}, frames={stability_frames}")
    
    def check_face_stability(self, face: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        """
        Check if face is stable enough to track.
        
        Args:
            face: Face rectangle as (x, y, w, h)
            
        Returns:
            Face if stable, None if not stable enough
        """
        face_center = self._get_face_center(face)
        current_time = time.time()
        
        # Add current face to history
        self.face_history.append((current_time, face_center, face))
        
        # Clean up old history
        self._cleanup_history()
        
        # Need at least stability_frames to consider stable
        if len(self.face_history) < self.stability_frames:
            self.logger.debug(f"Face not stable: only {len(self.face_history)} frames, "
                            f"need {self.stability_frames}")
            return None
        
        # Check if recent faces are close together (stable)
        recent_centers = [center for _, center, _ in self.face_history[-self.stability_frames:]]
        
        for i in range(1, len(recent_centers)):
            distance = self._calculate_distance(recent_centers[i], recent_centers[0])
            if distance > self.stability_threshold:
                self.logger.debug(f"Face not stable: movement {distance:.1f} > {self.stability_threshold}")
                return None
        
        self.logger.debug(f"Face is stable: {self.stability_frames} frames within {self.stability_threshold} pixels")
        return face
    
    def is_face_stable(self, face: Tuple[int, int, int, int]) -> bool:
        """
        Check if a specific face is currently considered stable.
        
        Args:
            face: Face rectangle to check
            
        Returns:
            True if face is stable
        """
        face_center = self._get_face_center(face)
        current_time = time.time()
        
        # Check if this face center is close to any recent stable faces
        for hist_time, hist_center, _ in reversed(self.face_history[-self.stability_frames:]):
            if current_time - hist_time > 1.0:  # Only check recent history
                continue
            
            distance = self._calculate_distance(face_center, hist_center)
            if distance <= self.stability_threshold:
                return True
        
        return False
    
    def get_stable_faces(self, all_faces: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Get list of faces that are considered stable.
        
        Args:
            all_faces: List of all detected faces
            
        Returns:
            List of stable faces
        """
        return [face for face in all_faces if self.is_face_stable(face)]
    
    def reset_history(self) -> None:
        """Clear face history."""
        self.face_history.clear()
        self.logger.debug("Face history reset")
    
    def _cleanup_history(self) -> None:
        """Remove old face history entries."""
        current_time = time.time()
        self.face_history = [(t, center, f) for t, center, f in self.face_history 
                            if current_time - t < self.history_window]
    
    def _get_face_center(self, face: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Calculate face center from bounding box."""
        x, y, w, h = face
        return (x + w // 2, y + h // 2)
    
    def _calculate_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two points."""
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return math.sqrt(dx * dx + dy * dy) 