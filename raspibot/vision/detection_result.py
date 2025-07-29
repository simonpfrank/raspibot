"""Detection result classes for multi-stage face and person detection."""

from dataclasses import dataclass
from typing import Tuple, Optional
import time


@dataclass
class DetectionResult:
    """Simple detection result with coordinates and metadata."""
    
    object_type: str  # "person" or "face"
    bbox: Tuple[int, int, int, int]  # (x, y, w, h) in pixels
    confidence: float
    servo_angles: Tuple[float, float]  # (pan, tilt) when detected
    timestamp: float
    camera_resolution: Tuple[int, int]  # (width, height)
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp == 0:
            self.timestamp = time.time()
    
    @property
    def area(self) -> int:
        """Calculate area in pixels."""
        x, y, w, h = self.bbox
        return w * h
    
    @property
    def center(self) -> Tuple[int, int]:
        """Calculate center point."""
        x, y, w, h = self.bbox
        return (x + w // 2, y + h // 2)
    
    @property
    def relative_distance(self) -> float:
        """Calculate relative distance based on object size (bigger = closer)."""
        # Simple heuristic: larger objects are closer
        # Normalize by camera resolution
        width, height = self.camera_resolution
        frame_area = width * height
        return self.area / frame_area
    
    def is_moving_fast(self, other: 'DetectionResult', threshold: int = 50) -> bool:
        """Check if object moved significantly between detections."""
        if other.object_type != self.object_type:
            return True  # Different object types
        
        center1 = self.center
        center2 = other.center
        
        distance = ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
        return distance > threshold
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.object_type.capitalize()}({self.bbox}, conf:{self.confidence:.2f}, area:{self.area})" 