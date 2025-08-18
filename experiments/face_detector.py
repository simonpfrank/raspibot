"""Face detection using multiple methods (OpenCV DNN YuNet or AI Camera)."""

import cv2
import numpy as np
import time
import os
from typing import List, Tuple, Optional

from ..utils.logging_config import setup_logging


class FaceDetector:
    """Face detection using multiple methods for better flexibility."""
    
    def __init__(self, 
                 confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.3,
                 model_path: Optional[str] = None,
                 detection_method: str = "auto",
                 camera_instance=None):
        """
        Initialize face detector with multiple detection methods.
        
        Args:
            confidence_threshold: Minimum confidence for face detection
            nms_threshold: Non-maximum suppression threshold (OpenCV only)
            model_path: Path to YuNet ONNX model file (OpenCV only)
            detection_method: Detection method ("opencv", "ai_camera", or "auto")
            camera_instance: Camera instance for AI camera detection
        """
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.detection_method = detection_method
        self.camera_instance = camera_instance
        self.logger = setup_logging(__name__)
        
        # Determine detection method
        if detection_method == "auto":
            if camera_instance and hasattr(camera_instance, 'get_detections'):
                self.detection_method = "ai_camera"
                self.logger.info("Auto-detected AI camera for face detection")
            else:
                self.detection_method = "opencv"
                self.logger.info("Auto-detected OpenCV for face detection")
        elif detection_method == "ai_camera" and not camera_instance:
            raise ValueError("AI camera detection requires camera_instance parameter")
        
        self.logger.info(f"Face detection method: {self.detection_method}")
        
        # Initialize based on method
        if self.detection_method == "opencv":
            self._initialize_opencv(model_path)
        elif self.detection_method == "ai_camera":
            self._initialize_ai_camera()
        
        # Performance tracking
        self.detection_count = 0
        self.detection_start_time = time.time()
        self.detection_fps = 0.0
        self._current_input_size = None
    
    def _initialize_opencv(self, model_path: Optional[str]) -> None:
        """Initialize OpenCV YuNet face detector."""
        # Set default model path if not provided
        if model_path is None:
            # Get the project root directory (4 levels up from this file)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, "data", "models", "face_detection_yunet_2023mar.onnx")
        
        self.model_path = model_path
        
        # Initialize YuNet face detector
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"YuNet model file not found: {self.model_path}")
            
            # Create the YuNet face detector
            self.detector = cv2.FaceDetectorYN.create(
                model=self.model_path,
                config="",  # Empty config for ONNX
                input_size=(0, 0),  # Will be set dynamically
                score_threshold=self.confidence_threshold,
                nms_threshold=self.nms_threshold
            )
            
            self.logger.info(f"YuNet face detector initialized with model: {self.model_path}")
            self.logger.info(f"Confidence threshold: {self.confidence_threshold}")
            self.logger.info(f"NMS threshold: {self.nms_threshold}")
            
        except Exception as e:
            self.logger.error(f"Error initializing YuNet face detector: {e}")
            raise
    
    def _initialize_ai_camera(self) -> None:
        """Initialize AI camera face detection."""
        if not self.camera_instance:
            raise ValueError("Camera instance required for AI camera detection")
        
        self.logger.info("AI camera face detection initialized")
        self.logger.info(f"Confidence threshold: {self.confidence_threshold}")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in frame using AI Camera or YuNet DNN model.
        
        Args:
            frame: Input image as numpy array (BGR or RGBA format)
            
        Returns:
            List of face rectangles as (x, y, w, h) tuples
        """
        if frame is None or frame.size == 0:
            return []
        
        # Use AI Camera detection if available
        if self.detection_method == "ai_camera" and self.camera_instance:
            return self._detect_faces_ai_camera()
        
        # Fallback to OpenCV YuNet detection
        return self._detect_faces_opencv(frame)
    
    def _detect_faces_ai_camera(self) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using AI Camera's person detection.
        
        Returns:
            List of face rectangles as (x, y, w, h) tuples
        """
        try:
            # Get detections from AI Camera
            detections = self.camera_instance.get_detections()
            
            face_list = []
            for detection in detections:
                # Convert PersonDetection to face rectangle
                x, y, w, h = detection.bbox
                confidence = detection.confidence
                
                # Filter by confidence threshold
                if confidence >= self.confidence_threshold:
                    face_list.append((x, y, w, h))
            
            self._update_detection_fps()
            
            if face_list:
                self.logger.debug(f"Detected {len(face_list)} faces with AI Camera")
            
            return face_list
            
        except Exception as e:
            self.logger.error(f"Error detecting faces with AI Camera: {e}")
            return []
    
    def _detect_faces_opencv(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using OpenCV YuNet DNN model.
        
        Args:
            frame: Input image as numpy array (BGR or RGBA format)
            
        Returns:
            List of face rectangles as (x, y, w, h) tuples
        """
        try:
            height, width = frame.shape[:2]
            input_size = (width, height)
            
            # Convert RGBA to BGR if needed (Pi AI camera returns RGBA)
            if frame.shape[2] == 4:
                # RGBA to BGR conversion
                frame_bgr = frame[:, :, :3]  # Remove alpha channel
                # Note: Pi AI camera returns RGBA, but we need BGR for OpenCV
                # The channels are already in the right order for BGR
            else:
                frame_bgr = frame
            
            # Convert to grayscale for better detection
            frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            # Convert back to BGR for YuNet (it expects BGR)
            frame_bgr = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2BGR)
            
            # Set input size if it has changed
            if self._current_input_size != input_size:
                self.detector.setInputSize(input_size)
                self._current_input_size = input_size
                self.logger.debug(f"Set YuNet input size to: {input_size}")
            
            # Detect faces
            _, faces = self.detector.detect(frame_bgr)
            
            face_list = []
            if faces is not None:
                for face in faces:
                    # YuNet returns: [x, y, w, h, x_re, y_re, x_le, y_le, x_nose, y_nose, x_mouth_r, y_mouth_r, x_mouth_l, y_mouth_l, confidence]
                    x, y, w, h = face[:4].astype(int)
                    confidence = face[-1]
                    
                    # Additional confidence filtering (YuNet already applies score_threshold)
                    if confidence >= self.confidence_threshold:
                        # Ensure coordinates are within frame bounds
                        x = max(0, min(x, width - 1))
                        y = max(0, min(y, height - 1))
                        w = max(1, min(w, width - x))
                        h = max(1, min(h, height - y))
                        
                        face_list.append((x, y, w, h))
            
            self._update_detection_fps()
            
            if face_list:
                self.logger.debug(f"Detected {len(face_list)} faces with YuNet")
            
            return face_list
            
        except Exception as e:
            self.logger.error(f"Error detecting faces with YuNet: {e}")
            return []
    
    def get_largest_face(self, faces: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the largest face from the list.
        
        Args:
            faces: List of face rectangles as (x, y, w, h) tuples
            
        Returns:
            Largest face rectangle, or None if no faces
        """
        if not faces:
            return None
        
        # Find face with maximum area (w * h)
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        
        self.logger.debug(f"Largest face: {largest_face} (area: {largest_face[2] * largest_face[3]})")
        
        return largest_face
    
    def get_face_center(self, face: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Get center point of face rectangle.
        
        Args:
            face: Face rectangle as (x, y, w, h) tuple
            
        Returns:
            Center point as (x, y) tuple
        """
        x, y, w, h = face
        center_x = x + w // 2
        center_y = y + h // 2
        
        return (center_x, center_y)
    
    def get_face_area(self, face: Tuple[int, int, int, int]) -> int:
        """
        Get area of face rectangle.
        
        Args:
            face: Face rectangle as (x, y, w, h) tuple
            
        Returns:
            Area in pixels
        """
        x, y, w, h = face
        return w * h
    
    def filter_faces_by_size(self, faces: List[Tuple[int, int, int, int]], 
                            min_area: int = 900) -> List[Tuple[int, int, int, int]]:
        """
        Filter faces by minimum area.
        
        Args:
            faces: List of face rectangles
            min_area: Minimum area in pixels (default: 30x30 = 900)
            
        Returns:
            Filtered list of faces
        """
        filtered_faces = [face for face in faces if self.get_face_area(face) >= min_area]
        
        if len(filtered_faces) != len(faces):
            self.logger.debug(f"Filtered {len(faces)} faces to {len(filtered_faces)} (min_area: {min_area})")
        
        return filtered_faces
    
    def get_detection_fps(self) -> float:
        """
        Get current detection FPS.
        
        Returns:
            Detection FPS as float
        """
        return self.detection_fps
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Update confidence threshold.
        
        Args:
            threshold: New confidence threshold (0.0 to 1.0)
        """
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        # Update the detector's score threshold
        try:
            # Note: YuNet doesn't have a direct method to update threshold after creation
            # For now, we'll handle it in detect_faces method
            self.logger.info(f"Updated confidence threshold to: {self.confidence_threshold}")
        except Exception as e:
            self.logger.warning(f"Could not update detector threshold: {e}")
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            "detection_method": self.detection_method,
            "confidence_threshold": self.confidence_threshold,
            "current_input_size": self._current_input_size
        }
        
        if self.detection_method == "opencv":
            info.update({
                "model_type": "YuNet DNN",
                "model_path": self.model_path,
                "nms_threshold": self.nms_threshold
            })
        elif self.detection_method == "ai_camera":
            info.update({
                "model_type": "AI Camera Person Detection",
                "model_path": "Hardware Accelerated (IMX500)"
            })
        
        return info
    
    def _update_detection_fps(self) -> None:
        """Update detection FPS counter."""
        self.detection_count += 1
        current_time = time.time()
        elapsed = current_time - self.detection_start_time
        
        if elapsed >= 1.0:  # Update FPS every second
            self.detection_fps = self.detection_count / elapsed
            self.detection_count = 0
            self.detection_start_time = current_time 