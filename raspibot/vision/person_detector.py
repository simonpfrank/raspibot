"""Person detection using Pi AI camera's built-in IMX500 hardware acceleration."""

import numpy as np
from typing import List, Optional, Tuple
import logging

from .detection_result import DetectionResult
from .pi_ai_camera import PiAICamera
from ..utils.logging_config import setup_logging


class PersonDetector:
    """Person detector using Pi AI camera's built-in IMX500 hardware acceleration."""
    
    def __init__(self, confidence_threshold: float = 0.3, camera_instance: Optional[PiAICamera] = None, camera_mode: str = "ai_detection"):
        """
        Initialize person detector.
        
        Args:
            confidence_threshold: Minimum confidence for person detection (0.0-1.0)
            camera_instance: Optional existing PiAICamera instance to use
            camera_mode: Camera mode to use for detection
        """
        self.logger = setup_logging(__name__)
        self.confidence_threshold = confidence_threshold
        
        # Use existing camera instance or create new one
        if camera_instance is not None:
            self.camera = camera_instance
            self.logger.info("Using existing Pi AI camera instance for person detection")
        else:
            # Initialize Pi AI camera for person detection
            try:
                self.camera = PiAICamera(
                    camera_mode=camera_mode,
                    confidence_threshold=confidence_threshold
                )
                self.camera.start()
                self.logger.info(f"Pi AI camera person detector initialized with mode: {camera_mode}")
            except Exception as e:
                self.logger.error(f"Failed to initialize Pi AI camera: {e}")
                self.camera = None
        
        self.logger.info(f"Confidence threshold: {confidence_threshold}")
    
    def detect_persons(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Detect persons in the given frame using on-camera AI.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of DetectionResult objects for detected persons
        """
        if self.camera is None:
            self.logger.warning("Pi AI camera not available, returning empty detections")
            return []
        
        try:
            # Get detections from Pi AI camera
            detections = self.camera.get_detections()
            
            # Debug: Print raw detections
            if detections:
                print(f"Raw detections from camera: {len(detections)}")
                for i, det in enumerate(detections):
                    print(f"  {i+1}. {det.category}: {det.bbox}, conf:{det.confidence:.2f}")
            else:
                # Debug: Print when no raw detections
                if hasattr(self, '_debug_counter'):
                    self._debug_counter += 1
                else:
                    self._debug_counter = 1
                
                if self._debug_counter % 30 == 0:  # Print every 30 calls
                    print(f"PersonDetector: No raw detections from camera (call {self._debug_counter})")
            
            # Convert to DetectionResult objects
            results = []
            for detection in detections:
                if detection.category.lower() in ['person', 'people']:
                    # Get frame dimensions for relative distance calculation
                    height, width = frame.shape[:2]
                    
                    # Get camera resolution for bounds checking
                    camera_resolution = self.camera.get_resolution()
                    
                    # Use the bounding box directly (already scaled by PiAICamera)
                    x, y, w, h = detection.bbox
                    
                    # Ensure coordinates are within frame bounds
                    x = max(0, min(x, width - 1))
                    y = max(0, min(y, height - 1))
                    w = max(1, min(w, width - x))
                    h = max(1, min(h, height - y))
                    
                    result = DetectionResult(
                        object_type="person",
                        bbox=(x, y, w, h),
                        confidence=detection.confidence,
                        servo_angles=(None, None),  # Will be set by caller
                        timestamp=None,  # Will be set by caller
                        camera_resolution=camera_resolution
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting persons with Pi AI camera: {e}")
            return []
    
    def get_detection_fps(self) -> float:
        """Get current detection FPS from the camera."""
        if self.camera and hasattr(self.camera, 'current_fps'):
            return self.camera.current_fps
        return 0.0
    
    def __del__(self):
        """Cleanup camera resources."""
        if self.camera:
            try:
                self.camera.stop()
            except Exception as e:
                self.logger.error(f"Error stopping Pi AI camera: {e}") 