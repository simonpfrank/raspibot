#!/usr/bin/env python3
"""Unit tests for Camera face detection integration."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from raspibot.hardware.cameras.camera import Camera


class TestCameraFaceDetectionIntegration:
    """Test face detection integration in Camera class."""

    def test_camera_init_with_face_detection_enabled(self):
        """Test camera initialization with face detection enabled."""
        with patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True), \
             patch('raspibot.hardware.cameras.camera.Picamera2') as mock_picamera:
            
            mock_camera_instance = Mock()
            mock_picamera.return_value = mock_camera_instance
            mock_picamera.global_camera_info.return_value = [
                {"Model": "imx500", "Id": "0", "Num": 0}
            ]
            
            camera = Camera(face_detection=True)
            
            assert camera.face_detection_enabled is True
            assert camera.face_detector is not None

    def test_camera_init_with_face_detection_disabled(self):
        """Test camera initialization with face detection disabled."""
        with patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True), \
             patch('raspibot.hardware.cameras.camera.Picamera2') as mock_picamera:
            
            mock_camera_instance = Mock()
            mock_picamera.return_value = mock_camera_instance
            mock_picamera.global_camera_info.return_value = [
                {"Model": "imx500", "Id": "0", "Num": 0}
            ]
            
            camera = Camera(face_detection=False)
            
            assert camera.face_detection_enabled is False
            assert camera.face_detector is None

    def test_camera_init_default_face_detection_disabled(self):
        """Test camera initialization defaults to face detection disabled."""
        with patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True), \
             patch('raspibot.hardware.cameras.camera.Picamera2') as mock_picamera:
            
            mock_camera_instance = Mock()
            mock_picamera.return_value = mock_camera_instance
            mock_picamera.global_camera_info.return_value = [
                {"Model": "imx500", "Id": "0", "Num": 0}
            ]
            
            camera = Camera()
            
            assert camera.face_detection_enabled is False
            assert camera.face_detector is None

    @patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.hardware.cameras.camera.Picamera2')
    def test_process_face_detection_ai_camera(self, mock_picamera):
        """Test face detection processing for AI camera with person detections."""
        mock_camera_instance = Mock()
        mock_picamera.return_value = mock_camera_instance
        mock_picamera.global_camera_info.return_value = [
            {"Model": "imx500", "Id": "0", "Num": 0}
        ]
        
        camera = Camera(face_detection=True)
        
        # Mock MappedArray with frame
        mock_mapped_array = Mock()
        mock_mapped_array.array = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock person detection
        person_detection = {
            "label": "person",
            "box": [100, 100, 150, 200],
            "score": 0.8
        }
        camera.detections = [person_detection]
        
        # Mock face detection result
        mock_face_result = [{"box": (120, 110, 50, 60), "confidence": 0.75}]
        camera.face_detector.detect_faces_in_region = Mock(return_value=mock_face_result)
        
        # Test face detection processing
        camera._process_face_detections(mock_mapped_array)
        
        # Verify face detection was called with person bounding box
        camera.face_detector.detect_faces_in_region.assert_called_once_with(
            mock_mapped_array.array, (100, 100, 150, 200)
        )
        
        # Verify face data is stored
        assert len(camera.face_detections) == 1
        assert camera.face_detections[0]["box"] == (120, 110, 50, 60)
        assert camera.face_detections[0]["confidence"] == 0.75

    @patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.hardware.cameras.camera.Picamera2')
    def test_process_face_detection_non_ai_camera(self, mock_picamera):
        """Test face detection processing for non-AI camera (full frame detection)."""
        mock_camera_instance = Mock()
        mock_picamera.return_value = mock_camera_instance
        mock_picamera.global_camera_info.return_value = [
            {"Model": "imx219", "Id": "0", "Num": 0}
        ]
        
        camera = Camera(face_detection=True)
        
        # Mock MappedArray with frame
        mock_mapped_array = Mock()
        mock_mapped_array.array = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock face detection result
        mock_face_result = [{"box": (120, 110, 50, 60), "confidence": 0.75}]
        camera.face_detector.detect_faces = Mock(return_value=mock_face_result)
        
        # Test face detection processing
        camera._process_face_detections(mock_mapped_array)
        
        # Verify full frame face detection was called
        camera.face_detector.detect_faces.assert_called_once_with(mock_mapped_array.array)
        
        # Verify face data is stored
        assert len(camera.face_detections) == 1
        assert camera.face_detections[0]["box"] == (120, 110, 50, 60)
        assert camera.face_detections[0]["confidence"] == 0.75

    def test_draw_faces_on_display(self):
        """Test drawing face bounding boxes and center points."""
        with patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True), \
             patch('raspibot.hardware.cameras.camera.Picamera2') as mock_picamera:
            
            mock_camera_instance = Mock()
            mock_picamera.return_value = mock_camera_instance
            mock_picamera.global_camera_info.return_value = [
                {"Model": "imx500", "Id": "0", "Num": 0}
            ]
            
            camera = Camera(face_detection=True)
            
            # Mock MappedArray
            mock_mapped_array = Mock()
            mock_mapped_array.array = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Test face data
            face_detections = [
                {"box": (100, 100, 50, 60), "confidence": 0.8, "center": (125, 130)},
                {"box": (200, 150, 45, 55), "confidence": 0.7, "center": (222, 177)}
            ]
            
            with patch('cv2.rectangle') as mock_rectangle, \
                 patch('cv2.circle') as mock_circle:
                
                camera.draw_faces(mock_mapped_array, face_detections)
                
                # Verify rectangles drawn for each face (white color)
                assert mock_rectangle.call_count == 2
                mock_rectangle.assert_any_call(
                    mock_mapped_array.array, (100, 100), (150, 160), (255, 255, 255), thickness=2
                )
                mock_rectangle.assert_any_call(
                    mock_mapped_array.array, (200, 150), (245, 205), (255, 255, 255), thickness=2
                )
                
                # Verify center points drawn for each face
                assert mock_circle.call_count == 2
                mock_circle.assert_any_call(
                    mock_mapped_array.array, (125, 130), 3, (255, 255, 255), -1
                )
                mock_circle.assert_any_call(
                    mock_mapped_array.array, (222, 177), 3, (255, 255, 255), -1
                )

    def test_calculate_face_centers(self):
        """Test calculation of face center points from bounding boxes."""
        with patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True), \
             patch('raspibot.hardware.cameras.camera.Picamera2') as mock_picamera:
            
            mock_camera_instance = Mock()
            mock_picamera.return_value = mock_camera_instance
            mock_picamera.global_camera_info.return_value = [
                {"Model": "imx500", "Id": "0", "Num": 0}
            ]
            
            camera = Camera(face_detection=True)
            
            # Test face data without center points
            face_detections = [
                {"box": (100, 100, 50, 60), "confidence": 0.8},
                {"box": (200, 150, 40, 50), "confidence": 0.7}
            ]
            
            # Calculate centers
            enhanced_faces = camera._calculate_face_centers(face_detections)
            
            # Verify center points calculated correctly
            assert enhanced_faces[0]["center"] == (125, 130)  # (100 + 50/2, 100 + 60/2)
            assert enhanced_faces[1]["center"] == (220, 175)  # (200 + 40/2, 150 + 50/2)

    def test_face_detection_error_handling(self):
        """Test graceful error handling when face detection fails."""
        with patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True), \
             patch('raspibot.hardware.cameras.camera.Picamera2') as mock_picamera:
            
            mock_camera_instance = Mock()
            mock_picamera.return_value = mock_camera_instance
            mock_picamera.global_camera_info.return_value = [
                {"Model": "imx500", "Id": "0", "Num": 0}
            ]
            
            camera = Camera(face_detection=True)
            
            # Mock face detector to raise exception
            camera.face_detector.detect_faces = Mock(side_effect=Exception("Face detection error"))
            
            # Mock MappedArray with frame
            mock_mapped_array = Mock()
            mock_mapped_array.array = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Should not raise exception, should handle gracefully
            camera._process_face_detections(mock_mapped_array)
            
            # Face detections should be empty due to error
            assert camera.face_detections == []