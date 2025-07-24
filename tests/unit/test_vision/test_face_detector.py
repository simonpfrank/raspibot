"""Unit tests for FaceDetector class."""

import pytest
import numpy as np
import os
from unittest.mock import Mock, patch, MagicMock

from raspibot.vision.face_detector import FaceDetector


class TestFaceDetector:
    """Test FaceDetector class functionality."""

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_face_detector_initialization(self, mock_exists, mock_create):
        """Test YuNet face detector initialization."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        assert detector.confidence_threshold == 0.5
        assert detector.nms_threshold == 0.3
        assert detector.detection_fps == 0.0
        assert "face_detection_yunet_2023mar.onnx" in detector.model_path

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_face_detector_custom_params(self, mock_exists, mock_create):
        """Test face detector with custom parameters."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector(confidence_threshold=0.7, nms_threshold=0.4)
        
        assert detector.confidence_threshold == 0.7
        assert detector.nms_threshold == 0.4

    @patch('os.path.exists')
    def test_face_detector_model_not_found(self, mock_exists):
        """Test face detector with missing model file."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError, match="YuNet model file not found"):
            FaceDetector()

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_face_detector_custom_model_path(self, mock_exists, mock_create):
        """Test face detector with custom model path."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        custom_path = "/custom/path/model.onnx"
        detector = FaceDetector(model_path=custom_path)
        
        assert detector.model_path == custom_path

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_detect_faces_success(self, mock_exists, mock_create):
        """Test successful face detection."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        # Mock YuNet detection result
        # YuNet returns: [x, y, w, h, landmarks..., confidence]
        mock_faces = np.array([
            [100, 100, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.8],  # Face 1
            [200, 150, 60, 60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9]   # Face 2
        ])
        mock_detector.detect.return_value = (None, mock_faces)
        
        detector = FaceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        faces = detector.detect_faces(frame)
        
        assert len(faces) == 2
        assert faces[0] == (100, 100, 50, 50)
        assert faces[1] == (200, 150, 60, 60)
        mock_detector.setInputSize.assert_called_with((640, 480))

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_detect_faces_no_faces(self, mock_exists, mock_create):
        """Test face detection with no faces found."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        # No faces detected
        mock_detector.detect.return_value = (None, None)
        
        detector = FaceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        faces = detector.detect_faces(frame)
        
        assert faces == []

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_detect_faces_confidence_filtering(self, mock_exists, mock_create):
        """Test face detection with confidence filtering."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        # Mock faces with different confidence levels
        mock_faces = np.array([
            [100, 100, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.8],  # Above threshold
            [200, 150, 60, 60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.3]   # Below threshold
        ])
        mock_detector.detect.return_value = (None, mock_faces)
        
        detector = FaceDetector(confidence_threshold=0.5)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        faces = detector.detect_faces(frame)
        
        # Only the high-confidence face should be returned
        assert len(faces) == 1
        assert faces[0] == (100, 100, 50, 50)

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_detect_faces_none_frame(self, mock_exists, mock_create):
        """Test face detection with None frame."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        faces = detector.detect_faces(None)
        
        assert faces == []

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_detect_faces_empty_frame(self, mock_exists, mock_create):
        """Test face detection with empty frame."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        frame = np.array([])
        
        faces = detector.detect_faces(frame)
        
        assert faces == []

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_detect_faces_input_size_caching(self, mock_exists, mock_create):
        """Test that input size is only set when it changes."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        mock_detector.detect.return_value = (None, None)
        
        detector = FaceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # First detection should set input size
        detector.detect_faces(frame)
        assert mock_detector.setInputSize.call_count == 1
        
        # Second detection with same size should not set input size again
        detector.detect_faces(frame)
        assert mock_detector.setInputSize.call_count == 1
        
        # Different size should set input size again
        larger_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        detector.detect_faces(larger_frame)
        assert mock_detector.setInputSize.call_count == 2

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_detect_faces_boundary_clipping(self, mock_exists, mock_create):
        """Test that face coordinates are clipped to frame boundaries."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        # Mock face that extends beyond frame boundaries
        mock_faces = np.array([
            [-10, -5, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.8],  # Negative x, y
            [600, 450, 100, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9]  # Extends beyond frame
        ])
        mock_detector.detect.return_value = (None, mock_faces)
        
        detector = FaceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)  # 640x480 frame
        
        faces = detector.detect_faces(frame)
        
        # First face should be clipped to start at (0, 0)
        assert faces[0][0] == 0  # x clipped to 0
        assert faces[0][1] == 0  # y clipped to 0
        
        # Second face should be clipped to frame boundaries
        assert faces[1][0] <= 639  # x within frame
        assert faces[1][1] <= 479  # y within frame

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_get_largest_face(self, mock_exists, mock_create):
        """Test getting the largest face from a list."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        faces = [(100, 100, 30, 30), (200, 200, 50, 50), (300, 300, 40, 40)]
        largest = detector.get_largest_face(faces)
        
        # Face at (200, 200) with 50x50 = 2500 area should be largest
        assert largest == (200, 200, 50, 50)

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_get_largest_face_empty_list(self, mock_exists, mock_create):
        """Test getting largest face from empty list."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        largest = detector.get_largest_face([])
        assert largest is None

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_get_face_center(self, mock_exists, mock_create):
        """Test getting face center point."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        face = (100, 100, 50, 50)
        center = detector.get_face_center(face)
        
        assert center == (125, 125)  # (100 + 50//2, 100 + 50//2)

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_get_face_area(self, mock_exists, mock_create):
        """Test getting face area."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        face = (100, 100, 50, 30)
        area = detector.get_face_area(face)
        
        assert area == 1500  # 50 * 30

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_filter_faces_by_size(self, mock_exists, mock_create):
        """Test filtering faces by minimum area."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        faces = [(100, 100, 20, 20), (200, 200, 40, 40), (300, 300, 10, 10)]
        filtered = detector.filter_faces_by_size(faces, min_area=800)
        
        # Only 40x40 = 1600 area face should remain
        assert len(filtered) == 1
        assert filtered[0] == (200, 200, 40, 40)

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_set_confidence_threshold(self, mock_exists, mock_create):
        """Test setting confidence threshold."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector()
        
        detector.set_confidence_threshold(0.8)
        assert detector.confidence_threshold == 0.8
        
        # Test boundary clamping
        detector.set_confidence_threshold(1.5)
        assert detector.confidence_threshold == 1.0
        
        detector.set_confidence_threshold(-0.1)
        assert detector.confidence_threshold == 0.0

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_get_model_info(self, mock_exists, mock_create):
        """Test getting model information."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        
        detector = FaceDetector(confidence_threshold=0.6, nms_threshold=0.4)
        info = detector.get_model_info()
        
        assert info["model_type"] == "YuNet DNN"
        assert info["confidence_threshold"] == 0.6
        assert info["nms_threshold"] == 0.4
        assert "face_detection_yunet_2023mar.onnx" in info["model_path"]

    @patch('cv2.FaceDetectorYN.create')
    @patch('os.path.exists')
    def test_fps_tracking(self, mock_exists, mock_create):
        """Test FPS tracking functionality."""
        mock_exists.return_value = True
        mock_detector = Mock()
        mock_create.return_value = mock_detector
        mock_detector.detect.return_value = (None, None)
        
        detector = FaceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Initial FPS should be 0
        assert detector.get_detection_fps() == 0.0
        
        # Simulate time passage for FPS calculation
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 0, 0, 1.0]  # 1 second elapsed
            
            detector.detect_faces(frame)  # First detection
            detector.detect_faces(frame)  # Second detection
            detector._update_detection_fps()  # Force FPS update
            
            # Should have some FPS now
            assert detector.get_detection_fps() > 0 