"""Detection data structures for people and face detection."""

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class PersonDetection:
    """Person detection result."""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    category: str = "person"
    center: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        """Calculate center point if not provided."""
        if self.center is None:
            x, y, w, h = self.bbox
            self.center = (x + w // 2, y + h // 2)
    
    @property
    def area(self) -> int:
        """Calculate bounding box area."""
        x, y, w, h = self.bbox
        return w * h
    
    @property
    def x(self) -> int:
        """Get x coordinate of bounding box."""
        return self.bbox[0]
    
    @property
    def y(self) -> int:
        """Get y coordinate of bounding box."""
        return self.bbox[1]
    
    @property
    def width(self) -> int:
        """Get width of bounding box."""
        return self.bbox[2]
    
    @property
    def height(self) -> int:
        """Get height of bounding box."""
        return self.bbox[3]


@dataclass
class FaceDetection:
    """Face detection result with additional metadata."""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    landmarks: Optional[List[Tuple[int, int]]] = None
    person_association: Optional[PersonDetection] = None
    center: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        """Calculate center point if not provided."""
        if self.center is None:
            x, y, w, h = self.bbox
            self.center = (x + w // 2, y + h // 2)
    
    @property
    def area(self) -> int:
        """Calculate bounding box area."""
        x, y, w, h = self.bbox
        return w * h
    
    @property
    def x(self) -> int:
        """Get x coordinate of bounding box."""
        return self.bbox[0]
    
    @property
    def y(self) -> int:
        """Get y coordinate of bounding box."""
        return self.bbox[1]
    
    @property
    def width(self) -> int:
        """Get width of bounding box."""
        return self.bbox[2]
    
    @property
    def height(self) -> int:
        """Get height of bounding box."""
        return self.bbox[3]


@dataclass
class DetectionResult:
    """Combined detection result containing both people and faces."""
    people: List[PersonDetection]
    faces: List[FaceDetection]
    frame_timestamp: float
    detection_fps: float = 0.0
    
    @property
    def total_detections(self) -> int:
        """Get total number of detections."""
        return len(self.people) + len(self.faces)
    
    @property
    def has_people(self) -> bool:
        """Check if any people were detected."""
        return len(self.people) > 0
    
    @property
    def has_faces(self) -> bool:
        """Check if any faces were detected."""
        return len(self.faces) > 0
    
    def get_largest_person(self) -> Optional[PersonDetection]:
        """Get the person with the largest bounding box area."""
        if not self.people:
            return None
        return max(self.people, key=lambda p: p.area)
    
    def get_largest_face(self) -> Optional[FaceDetection]:
        """Get the face with the largest bounding box area."""
        if not self.faces:
            return None
        return max(self.faces, key=lambda f: f.area) 