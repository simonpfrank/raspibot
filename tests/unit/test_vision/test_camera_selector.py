"""Unit tests for camera factory functions."""

import pytest
from unittest.mock import Mock, patch

from raspibot.vision.camera_selector import (
    CameraType, get_camera, is_pi_ai_available, 
    get_available_cameras, get_best_available_camera
)


class TestCameraFactory:
    """Test camera factory functions."""

    def test_camera_type_enum(self):
        """Test CameraType enum values."""
        assert CameraType.WEBCAM.value == "webcam"
        assert CameraType.PI_AI.value == "pi_ai"
        assert CameraType.AUTO.value == "auto"

    @patch('raspibot.vision.camera_selector.Camera')
    def test_get_camera_webcam(self, mock_camera_class):
        """Test getting webcam camera."""
        mock_camera = Mock()
        mock_camera_class.return_value = mock_camera
        
        camera = get_camera(CameraType.WEBCAM)
        
        assert camera == mock_camera
        mock_camera_class.assert_called_once_with()

    @patch('raspibot.vision.camera_selector.Camera')
    def test_get_camera_webcam_string(self, mock_camera_class):
        """Test getting webcam camera with string type."""
        mock_camera = Mock()
        mock_camera_class.return_value = mock_camera
        
        camera = get_camera("webcam")
        
        assert camera == mock_camera
        mock_camera_class.assert_called_once_with()

    @patch('raspibot.vision.camera_selector.PiAICamera')
    def test_get_camera_pi_ai(self, mock_pi_ai_class):
        """Test getting Pi AI camera."""
        mock_camera = Mock()
        mock_pi_ai_class.return_value = mock_camera
        
        camera = get_camera(CameraType.PI_AI)
        
        assert camera == mock_camera
        mock_pi_ai_class.assert_called_once_with()

    @patch('raspibot.vision.camera_selector.PiAICamera')
    @patch('raspibot.vision.camera_selector.Camera')
    def test_get_camera_auto_pi_ai_available(self, mock_camera_class, mock_pi_ai_class):
        """Test auto camera selection when Pi AI is available."""
        mock_pi_ai = Mock()
        mock_pi_ai_class.return_value = mock_pi_ai
        
        camera = get_camera(CameraType.AUTO)
        
        assert camera == mock_pi_ai
        mock_pi_ai_class.assert_called_once()
        mock_camera_class.assert_not_called()

    @patch('raspibot.vision.camera_selector.PiAICamera')
    @patch('raspibot.vision.camera_selector.Camera')
    def test_get_camera_auto_pi_ai_not_available(self, mock_camera_class, mock_pi_ai_class):
        """Test auto camera selection when Pi AI is not available."""
        # Pi AI raises exception
        mock_pi_ai_class.side_effect = ImportError("Pi AI not available")
        
        mock_camera = Mock()
        mock_camera_class.return_value = mock_camera
        
        camera = get_camera(CameraType.AUTO)
        
        assert camera == mock_camera
        mock_pi_ai_class.assert_called_once()
        mock_camera_class.assert_called_once()

    def test_get_camera_invalid_string(self):
        """Test getting camera with invalid string type."""
        with pytest.raises(ValueError, match="Invalid camera type"):
            get_camera("invalid_type")

    def test_get_camera_with_kwargs(self):
        """Test getting camera with additional arguments."""
        with patch('raspibot.vision.camera_selector.Camera') as mock_camera_class:
            mock_camera = Mock()
            mock_camera_class.return_value = mock_camera
            
            camera = get_camera(CameraType.WEBCAM, device_id=1, width=640, height=480)
            
            mock_camera_class.assert_called_once_with(device_id=1, width=640, height=480)

    def test_get_camera_with_camera_mode(self):
        """Test getting camera with camera mode parameter."""
        with patch('raspibot.vision.camera_selector.PiAICamera') as mock_pi_ai_class:
            mock_camera = Mock()
            mock_pi_ai_class.return_value = mock_camera
            
            camera = get_camera(CameraType.PI_AI, camera_mode="ai_detection")
            
            mock_pi_ai_class.assert_called_once_with(camera_mode="ai_detection")

    def test_get_camera_with_camera_mode_basic(self):
        """Test getting basic camera with camera mode parameter."""
        with patch('raspibot.vision.camera_selector.PiCamera') as mock_basic_class:
            mock_camera = Mock()
            mock_basic_class.return_value = mock_camera
            
            camera = get_camera(CameraType.BASIC, camera_mode="opencv_detection")
            
            mock_basic_class.assert_called_once_with(camera_mode="opencv_detection")

    @patch('raspibot.vision.camera_selector.PiAICamera')
    def test_is_pi_ai_available_true(self, mock_pi_ai_class):
        """Test Pi AI availability check when available."""
        mock_camera = Mock()
        mock_pi_ai_class.return_value = mock_camera
        
        result = is_pi_ai_available()
        
        assert result is True
        mock_camera.stop.assert_called_once()

    @patch('raspibot.vision.camera_selector.PiAICamera')
    def test_is_pi_ai_available_false(self, mock_pi_ai_class):
        """Test Pi AI availability check when not available."""
        mock_pi_ai_class.side_effect = ImportError("Pi AI not available")
        
        result = is_pi_ai_available()
        
        assert result is False

    @patch('raspibot.vision.camera_selector.is_pi_ai_available')
    def test_get_available_cameras_with_pi_ai(self, mock_is_available):
        """Test getting available cameras when Pi AI is available."""
        mock_is_available.return_value = True
        
        cameras = get_available_cameras()
        
        assert CameraType.WEBCAM in cameras
        assert CameraType.PI_AI in cameras
        assert len(cameras) == 2

    @patch('raspibot.vision.camera_selector.is_pi_ai_available')
    def test_get_available_cameras_without_pi_ai(self, mock_is_available):
        """Test getting available cameras when Pi AI is not available."""
        mock_is_available.return_value = False
        
        cameras = get_available_cameras()
        
        assert CameraType.WEBCAM in cameras
        assert CameraType.PI_AI not in cameras
        assert len(cameras) == 1

    @patch('raspibot.vision.camera_selector.is_pi_ai_available')
    def test_get_best_available_camera_pi_ai(self, mock_is_available):
        """Test getting recommended camera when Pi AI is available."""
        mock_is_available.return_value = True
        
        recommended = get_best_available_camera()
        
        assert recommended == CameraType.PI_AI

    @patch('raspibot.vision.camera_selector.is_pi_ai_available')
    def test_get_best_available_camera_webcam(self, mock_is_available):
        """Test getting recommended camera when Pi AI is not available."""
        mock_is_available.return_value = False
        
        recommended = get_best_available_camera()
        
        assert recommended == CameraType.WEBCAM 