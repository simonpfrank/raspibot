"""Unit tests for raspibot.vision.face_detection module."""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from typing import List, Dict, Optional, Tuple

from raspibot.vision.face_detection import FaceDetector


class TestFaceDetectorInitialization:
    """Test FaceDetector initialization."""
    
    def test_init_default_parameters(self):
        """Test default parameter initialization."""
        detector = FaceDetector()
        
        assert detector.confidence_threshold == 0.5
        assert detector.scale_factor == 1.1
        assert detector.min_neighbors == 5
        assert detector.min_size == (30, 30)
        assert detector.model_path is None
        assert detector.model_type == "haar"
    
    def test_init_custom_parameters(self):
        """Test custom parameter initialization."""
        detector = FaceDetector(
            confidence_threshold=0.7,
            scale_factor=1.2,
            min_neighbors=3,
            min_size=(40, 40)
        )
        
        assert detector.confidence_threshold == 0.7
        assert detector.scale_factor == 1.2
        assert detector.min_neighbors == 3
        assert detector.min_size == (40, 40)
        assert detector.model_path is None
        assert detector.model_type == "haar"
    
    def test_init_with_custom_model_path(self):
        """Test initialization with custom model path."""
        model_path = "data/models/face_detection_yunet_2023mar.onnx"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            with patch('raspibot.vision.face_detection.cv2.FaceDetectorYN.create') as mock_create:
                mock_exists.return_value = True
                mock_create.return_value = MagicMock()
                
                detector = FaceDetector(model_path=model_path)
                
                assert detector.model_path == model_path
                assert detector.model_type == "onnx"
                mock_create.assert_called_once()
    
    def test_init_loads_cascade_classifier_default(self):
        """Test that cascade classifier is loaded during initialization by default."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector()
            
            mock_cascade.assert_called_once()
            assert detector.face_cascade is not None
            assert detector.model_type == "haar"
    
    def test_init_invalid_model_path(self):
        """Test initialization with invalid model path raises error."""
        invalid_path = "data/models/nonexistent.onnx"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            with pytest.raises(FileNotFoundError):
                FaceDetector(model_path=invalid_path)
    
    def test_init_unsupported_model_format(self):
        """Test initialization with unsupported model format raises error."""
        unsupported_path = "data/models/face_model.pkl"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with pytest.raises(ValueError):
                FaceDetector(model_path=unsupported_path)


class TestONNXModelDetection:
    """Test ONNX model face detection functionality."""
    
    def test_detect_faces_onnx_single_face(self):
        """Test ONNX model detection with single face."""
        model_path = "data/models/face_detection_yunet_2023mar.onnx"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            with patch('raspibot.vision.face_detection.cv2.FaceDetectorYN.create') as mock_create:
                mock_exists.return_value = True
                mock_detector = MagicMock()
                mock_detector.detect.return_value = (1, np.array([[100, 150, 80, 80, 0.9]]))
                mock_create.return_value = mock_detector
                
                detector = FaceDetector(model_path=model_path, confidence_threshold=0.3)
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                
                result = detector.detect_faces(frame)
                
                assert result is not None
                assert len(result) == 1
                assert result[0]['box'] == (100, 150, 80, 80)
                assert result[0]['confidence'] == 0.9
    
    def test_detect_faces_onnx_multiple_faces(self):
        """Test ONNX model detection with multiple faces."""
        model_path = "data/models/face_detection_yunet_2023mar.onnx"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            with patch('raspibot.vision.face_detection.cv2.FaceDetectorYN.create') as mock_create:
                mock_exists.return_value = True
                mock_detector = MagicMock()
                mock_detector.detect.return_value = (2, np.array([
                    [100, 150, 80, 80, 0.9],
                    [300, 200, 60, 60, 0.8]
                ]))
                mock_create.return_value = mock_detector
                
                detector = FaceDetector(model_path=model_path, confidence_threshold=0.3)
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                
                result = detector.detect_faces(frame)
                
                assert result is not None
                assert len(result) == 2
                assert result[0]['box'] == (100, 150, 80, 80)
                assert result[0]['confidence'] == 0.9
                assert result[1]['box'] == (300, 200, 60, 60)
                assert result[1]['confidence'] == 0.8
    
    def test_detect_faces_onnx_no_faces(self):
        """Test ONNX model detection when no faces found."""
        model_path = "data/models/face_detection_yunet_2023mar.onnx"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            with patch('raspibot.vision.face_detection.cv2.FaceDetectorYN.create') as mock_create:
                mock_exists.return_value = True
                mock_detector = MagicMock()
                mock_detector.detect.return_value = (0, None)
                mock_create.return_value = mock_detector
                
                detector = FaceDetector(model_path=model_path, confidence_threshold=0.3)
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                
                result = detector.detect_faces(frame)
                
                assert result is None
    
    def test_detect_faces_onnx_confidence_filtering(self):
        """Test ONNX model detection with confidence filtering."""
        model_path = "data/models/face_detection_yunet_2023mar.onnx"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            with patch('raspibot.vision.face_detection.cv2.FaceDetectorYN.create') as mock_create:
                mock_exists.return_value = True
                mock_detector = MagicMock()
                mock_detector.detect.return_value = (2, np.array([
                    [100, 150, 80, 80, 0.9],  # Above threshold
                    [300, 200, 60, 60, 0.3]   # Below threshold
                ]))
                mock_create.return_value = mock_detector
                
                detector = FaceDetector(model_path=model_path, confidence_threshold=0.5)
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                
                result = detector.detect_faces(frame)
                
                assert result is not None
                assert len(result) == 1  # Only high confidence face
                assert result[0]['confidence'] == 0.9
    
    def test_detect_faces_in_region_onnx(self):
        """Test ONNX model detection within a bounding box region."""
        model_path = "data/models/face_detection_yunet_2023mar.onnx"
        
        with patch('raspibot.vision.face_detection.os.path.exists') as mock_exists:
            with patch('raspibot.vision.face_detection.cv2.FaceDetectorYN.create') as mock_create:
                mock_exists.return_value = True
                mock_detector = MagicMock()
                mock_detector.detect.return_value = (1, np.array([[20, 30, 40, 40, 0.9]]))
                mock_create.return_value = mock_detector
                
                detector = FaceDetector(model_path=model_path, confidence_threshold=0.3)
                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                person_box = (200, 100, 150, 200)
                
                result = detector.detect_faces_in_region(frame, person_box)
                
                assert result is not None
                assert len(result) == 1
                # Coordinates should be mapped back to original frame
                assert result[0]['box'] == (220, 130, 40, 40)  # 200+20, 100+30, 40, 40
                assert result[0]['confidence'] == 0.9


class TestFaceDetectionFullFrame:
    """Test face detection on full frames."""
    
    def test_detect_faces_empty_frame(self):
        """Test detection with empty frame."""
        detector = FaceDetector()
        empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = detector.detect_faces(empty_frame)
        
        assert result is None
    
    def test_detect_faces_no_faces_found(self):
        """Test detection when no faces are found."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = []
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            result = detector.detect_faces(frame)
            
            assert result is None
    
    def test_detect_faces_single_face(self):
        """Test detection with single face found."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = [(100, 150, 80, 80)]
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            result = detector.detect_faces(frame)
            
            assert result is not None
            assert len(result) == 1
            assert result[0]['box'] == (100, 150, 80, 80)
            assert result[0]['confidence'] >= 0.0
            assert result[0]['confidence'] <= 1.0
    
    def test_detect_faces_multiple_faces(self):
        """Test detection with multiple faces found."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = [(100, 150, 80, 80), (300, 200, 60, 60)]
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            result = detector.detect_faces(frame)
            
            assert result is not None
            assert len(result) == 2
            assert result[0]['box'] == (100, 150, 80, 80)
            assert result[1]['box'] == (300, 200, 60, 60)


class TestFaceDetectionBoundingBoxRegion:
    """Test face detection on bounding box regions."""
    
    def test_detect_faces_in_region_valid_box(self):
        """Test detection within a valid bounding box region."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = [(20, 30, 40, 40)]  # Relative to cropped region
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            person_box = (200, 100, 150, 200)  # x, y, w, h
            
            result = detector.detect_faces_in_region(frame, person_box)
            
            assert result is not None
            assert len(result) == 1
            # Coordinates should be mapped back to original frame
            assert result[0]['box'] == (220, 130, 40, 40)  # 200+20, 100+30, 40, 40
    
    def test_detect_faces_in_region_no_faces(self):
        """Test detection in region when no faces are found."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = []
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            person_box = (200, 100, 150, 200)
            
            result = detector.detect_faces_in_region(frame, person_box)
            
            assert result is None
    
    def test_detect_faces_in_region_invalid_box(self):
        """Test detection with invalid bounding box."""
        detector = FaceDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        invalid_box = (700, 500, 100, 100)  # Outside frame bounds
        
        result = detector.detect_faces_in_region(frame, invalid_box)
        
        assert result is None
    
    def test_detect_faces_in_region_edge_case_box(self):
        """Test detection with edge case bounding box (at frame edges)."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = [(10, 15, 30, 30)]
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            edge_box = (0, 0, 100, 100)  # Top-left corner
            
            result = detector.detect_faces_in_region(frame, edge_box)
            
            assert result is not None
            assert result[0]['box'] == (10, 15, 30, 30)


class TestCoordinateMapping:
    """Test coordinate mapping functionality."""
    
    def test_map_coordinates_to_original_simple(self):
        """Test coordinate mapping from region to original frame."""
        detector = FaceDetector()
        region_box = (50, 25, 30, 30)  # Face in region coordinates
        region_offset = (200, 100)     # Region offset in original frame
        
        original_box = detector._map_coordinates_to_original(region_box, region_offset)
        
        assert original_box == (250, 125, 30, 30)  # 200+50, 100+25, 30, 30
    
    def test_map_coordinates_to_original_zero_offset(self):
        """Test coordinate mapping with zero offset."""
        detector = FaceDetector()
        region_box = (10, 20, 40, 40)
        region_offset = (0, 0)
        
        original_box = detector._map_coordinates_to_original(region_box, region_offset)
        
        assert original_box == (10, 20, 40, 40)


class TestConfidenceCalculation:
    """Test confidence calculation methods."""
    
    def test_calculate_confidence_default(self):
        """Test default confidence calculation."""
        detector = FaceDetector()
        face_box = (100, 150, 80, 80)
        
        confidence = detector._calculate_confidence(face_box)
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
    
    def test_calculate_confidence_larger_face_higher_confidence(self):
        """Test that larger faces get higher confidence scores."""
        detector = FaceDetector()
        small_face = (100, 150, 40, 40)
        large_face = (100, 150, 120, 120)
        
        small_confidence = detector._calculate_confidence(small_face)
        large_confidence = detector._calculate_confidence(large_face)
        
        assert large_confidence > small_confidence


class TestValidationMethods:
    """Test input validation methods."""
    
    def test_validate_frame_valid(self):
        """Test frame validation with valid frame."""
        detector = FaceDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        assert detector._validate_frame(frame) is True
    
    def test_validate_frame_none(self):
        """Test frame validation with None."""
        detector = FaceDetector()
        
        assert detector._validate_frame(None) is False
    
    def test_validate_frame_wrong_dimensions(self):
        """Test frame validation with wrong dimensions."""
        detector = FaceDetector()
        frame = np.random.randint(0, 255, (480, 640), dtype=np.uint8)  # Missing color channel
        
        assert detector._validate_frame(frame) is False
    
    def test_validate_bounding_box_valid(self):
        """Test bounding box validation with valid box."""
        detector = FaceDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        box = (100, 150, 200, 180)
        
        assert detector._validate_bounding_box(box, frame) is True
    
    def test_validate_bounding_box_outside_frame(self):
        """Test bounding box validation with box outside frame."""
        detector = FaceDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        box = (700, 500, 100, 100)  # Outside frame bounds
        
        assert detector._validate_bounding_box(box, frame) is False
    
    def test_validate_bounding_box_negative_coordinates(self):
        """Test bounding box validation with negative coordinates."""
        detector = FaceDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        box = (-10, -20, 100, 100)
        
        assert detector._validate_bounding_box(box, frame) is False


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features."""
    
    def test_person_tracking_scenario(self):
        """Test scenario where we track a person and detect their face."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = [(50, 20, 60, 60)]  # Face in person region
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Person detected at this location
            person_box = (200, 100, 150, 200)
            
            result = detector.detect_faces_in_region(frame, person_box)
            
            assert result is not None
            assert len(result) == 1
            # Face coordinates mapped to original frame
            face = result[0]
            assert face['box'] == (250, 120, 60, 60)  # 200+50, 100+20, 60, 60
            
            # Face should be within the person bounding box area
            fx, fy, fw, fh = face['box']
            px, py, pw, ph = person_box
            assert fx >= px
            assert fy >= py
            assert fx + fw <= px + pw
            assert fy + fh <= py + ph
    
    def test_false_positive_detection_scenario(self):
        """Test scenario where object has moved (false positive detection)."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = []  # No face found - object moved or false positive
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Person was detected here but may have moved
            person_box = (300, 200, 100, 150)
            
            result = detector.detect_faces_in_region(frame, person_box)
            
            # Should return None indicating no face found
            assert result is None
    
    def test_multiple_faces_in_person_region(self):
        """Test scenario with multiple faces in a person region."""
        with patch('raspibot.vision.face_detection.cv2.CascadeClassifier') as mock_cascade:
            mock_instance = MagicMock()
            mock_instance.empty.return_value = False
            mock_instance.detectMultiScale.return_value = [(50, 30, 60, 60), (250, 100, 70, 70)]
            mock_cascade.return_value = mock_instance
            
            detector = FaceDetector(confidence_threshold=0.3)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Large person region that might contain multiple people
            person_box = (100, 50, 400, 300)
            
            result = detector.detect_faces_in_region(frame, person_box)
            
            assert result is not None
            assert len(result) == 2
            
            # Check both faces are mapped correctly
            face1 = result[0]
            face2 = result[1]
            assert face1['box'] == (150, 80, 60, 60)   # 100+50, 50+30
            assert face2['box'] == (350, 150, 70, 70)  # 100+250, 50+100