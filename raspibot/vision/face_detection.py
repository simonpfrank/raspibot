"""OpenCV-based face detection for robotics applications.

This module provides face detection functionality that can work with either
full camera frames or bounding box regions from person detection. It returns
face coordinates mapped to the original frame coordinates for screen annotation.

Supports both Haar cascade classifiers (default) and ONNX models (e.g., YuNet).
"""

import cv2
import numpy as np
import os
from typing import List, Dict, Optional, Tuple, Union
from raspibot.utils.logging_config import setup_logging


class FaceDetector:
    """OpenCV-based face detector with coordinate mapping support."""

    # Type annotations for instance variables
    face_cascade: Optional[cv2.CascadeClassifier]
    onnx_detector: Optional[cv2.FaceDetectorYN]  # type: ignore
    model_type: str

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_size: Tuple[int, int] = (30, 30),
        model_path: Optional[str] = None,
    ):
        """
        Initialize face detector with OpenCV Haar cascade or custom model.

        Args:
            confidence_threshold: Minimum confidence for face detection (0.0-1.0)
            scale_factor: How much the image size is reduced at each scale (Haar cascade only)
            min_neighbors: How many neighbors each candidate rectangle should have (Haar cascade only)
            min_size: Minimum possible face size (width, height) (Haar cascade only)
            model_path: Optional path to custom model file (e.g., ONNX). If None, uses default Haar cascade
        """
        self.confidence_threshold = confidence_threshold
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size
        self.model_path = model_path
        self.logger = setup_logging(__name__)

        # Initialize appropriate detector based on model path
        if model_path is None:
            self._init_haar_cascade()
            self.model_type = "haar"
        else:
            self._init_custom_model(model_path)

        self.logger.info("Face detector initialised")

    def _init_haar_cascade(self) -> None:
        """Initialize Haar cascade classifier."""
        # Load OpenCV's pre-trained Haar cascade for face detection
        # Note: cv2.data may not be typed, so we ignore the mypy error
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise RuntimeError("Failed to load face cascade classifier")

        # Set placeholder for ONNX detector
        self.onnx_detector = None

    def _init_custom_model(self, model_path: str) -> None:
        """Initialize custom model detector."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Determine model type based on file extension
        file_extension = os.path.splitext(model_path)[1].lower()

        if file_extension == ".onnx":
            self._init_onnx_model(model_path)
            self.model_type = "onnx"
        else:
            raise ValueError(
                f"Unsupported model format: {file_extension}. Supported formats: .onnx"
            )

        # Set placeholder for Haar cascade
        self.face_cascade = None

    def _init_onnx_model(self, model_path: str) -> None:
        """Initialize ONNX model detector (e.g., YuNet)."""
        try:
            # Create YuNet face detector for ONNX models
            # Default input size for YuNet is 320x320, but it can be resized
            input_size = (320, 320)
            self.onnx_detector = cv2.FaceDetectorYN.create(
                model_path,
                "",  # config path (empty for ONNX)
                input_size,
                score_threshold=self.confidence_threshold,
                nms_threshold=0.3,
                top_k=5000,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {e}")

    def detect_faces(self, frame: np.ndarray) -> Optional[List[Dict]]:
        """
        Detect faces in a full camera frame.

        Args:
            frame: Input camera frame (BGR format)

        Returns:
            List of face dictionaries with 'box' and 'confidence' keys,
            or None if no faces found
        """
        if not self._validate_frame(frame):
            return None

        if self.model_type == "haar":
            return self._detect_faces_haar(frame)
        elif self.model_type == "onnx":
            return self._detect_faces_onnx(frame)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def _detect_faces_haar(self, frame: np.ndarray) -> Optional[List[Dict]]:
        """Detect faces using Haar cascade classifier."""
        if self.face_cascade is None:
            raise RuntimeError("Haar cascade not initialized")

        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size,
        )

        if len(faces) == 0:
            return None

        # Convert to list of dictionaries with confidence scores
        face_detections = []
        for x, y, w, h in faces:
            confidence = self._calculate_confidence((x, y, w, h))

            if confidence >= self.confidence_threshold:
                face_detections.append({"box": (x, y, w, h), "confidence": confidence})

        return face_detections if face_detections else None

    def _detect_faces_onnx(self, frame: np.ndarray) -> Optional[List[Dict]]:
        """Detect faces using ONNX model (e.g., YuNet)."""
        if self.onnx_detector is None:
            raise RuntimeError("ONNX detector not initialized")

        # Resize frame to match model input size
        height, width = frame.shape[:2]
        self.onnx_detector.setInputSize((width, height))

        # Detect faces
        _, faces = self.onnx_detector.detect(frame)

        if faces is None or len(faces) == 0:
            return None

        # Convert to list of dictionaries with confidence scores
        face_detections = []
        for face in faces:
            # ONNX detector returns: [x, y, w, h, confidence, ...]
            x, y, w, h, confidence = face[:5]
            x, y, w, h = int(x), int(y), int(w), int(h)

            if confidence >= self.confidence_threshold:
                face_detections.append(
                    {"box": (x, y, w, h), "confidence": float(confidence)}
                )

        return face_detections if face_detections else None

    def detect_faces_in_region(
        self, frame: np.ndarray, region_box: Tuple[int, int, int, int]
    ) -> Optional[List[Dict]]:
        """
        Detect faces within a specific bounding box region of the frame.

        Args:
            frame: Input camera frame (BGR format)
            region_box: Bounding box (x, y, width, height) to search within

        Returns:
            List of face dictionaries with coordinates mapped to original frame,
            or None if no faces found or region is invalid
        """

        if not self._validate_frame(frame):
            return None

        if not self._validate_bounding_box(region_box, frame):
            return None

        x, y, w, h = region_box

        # Extract region of interest
        roi = frame[y : y + h, x : x + w]

        if roi.size == 0:
            return None

        # Detect faces in the cropped region
        region_faces = self.detect_faces(roi)

        if region_faces is None:
            return None

        # Map coordinates back to original frame
        mapped_faces = []
        for face in region_faces:
            original_box = self._map_coordinates_to_original(face["box"], (x, y))

            mapped_faces.append({"box": original_box, "confidence": face["confidence"]})

        return mapped_faces

    def _map_coordinates_to_original(
        self, region_box: Tuple[int, int, int, int], region_offset: Tuple[int, int]
    ) -> Tuple[int, int, int, int]:
        """
        Map coordinates from region space to original frame space.

        Args:
            region_box: Bounding box in region coordinates (x, y, w, h)
            region_offset: Offset of region in original frame (x_offset, y_offset)

        Returns:
            Bounding box in original frame coordinates (x, y, w, h)
        """
        rx, ry, rw, rh = region_box
        ox, oy = region_offset

        return (rx + ox, ry + oy, rw, rh)

    def _calculate_confidence(self, face_box: Tuple[int, int, int, int]) -> float:
        """
        Calculate confidence score for a detected face.

        Since Haar cascades don't provide confidence scores, we estimate
        based on face size (larger faces are generally more reliable).

        Args:
            face_box: Face bounding box (x, y, w, h)

        Returns:
            Confidence score between 0.0 and 1.0
        """
        x, y, w, h = face_box
        area = w * h

        # Normalize area to confidence score
        # Faces smaller than min_size get lower confidence
        # Faces larger than 200x200 get high confidence
        min_area = self.min_size[0] * self.min_size[1]
        max_area = 200 * 200

        if area <= min_area:
            confidence = 0.3
        elif area >= max_area:
            confidence = 0.9
        else:
            # Linear interpolation between min and max
            confidence = 0.3 + (area - min_area) / (max_area - min_area) * 0.6

        return min(0.9, max(0.3, confidence))

    def _validate_frame(self, frame) -> bool:
        """
        Validate that frame is suitable for face detection.

        Args:
            frame: Input frame to validate

        Returns:
            True if frame is valid, False otherwise
        """
        if frame is None:
            return False

        if not isinstance(frame, np.ndarray):
            return False

        if len(frame.shape) != 3:
            return False

        if frame.shape[2] < 3:  # BGR channels
            return False

        return True

    def _validate_bounding_box(
        self, box: Tuple[int, int, int, int], frame: np.ndarray
    ) -> bool:
        """
        Validate that bounding box is within frame bounds.

        Args:
            box: Bounding box (x, y, w, h) to validate
            frame: Frame to check bounds against

        Returns:
            True if box is valid, False otherwise
        """
        if len(box) != 4:
            return False

        x, y, w, h = box
        frame_height, frame_width = frame.shape[:2]

        # Check if box is within frame bounds
        if x < 0 or y < 0:
            return False

        if x + w > frame_width or y + h > frame_height:
            return False

        if w <= 0 or h <= 0:
            return False

        return True
