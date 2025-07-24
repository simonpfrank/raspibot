"""Unit tests for Pi AI Camera implementation."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from raspibot.vision.pi_ai_camera import PiAICamera, PICAMERA2_AVAILABLE
from raspibot.vision.detection_models import PersonDetection
from raspibot.vision.camera_factory import CameraFactory, CameraType


class TestPiAICamera:
    """Test Pi AI Camera functionality."""
    
    def test_initialization_without_picamera2(self):
        """Test initialization when picamera2 is not available."""
        with patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', False):
            with pytest.raises(ImportError, match="picamera2 not available"):
                PiAICamera()
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_initialization_success(self, mock_picamera2, mock_imx500):
        """Test successful initialization."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.confidence_threshold = 0.55
        mock_intrinsics.iou_threshold = 0.65
        mock_intrinsics.max_detections = 10
        mock_intrinsics.inference_rate = 30
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        # Test initialization
        camera = PiAICamera()
        
        assert camera.model_path is not None
        assert camera.confidence_threshold == 0.55
        assert camera.iou_threshold == 0.65
        assert camera.max_detections == 10
        assert camera.inference_rate == 30
        assert camera.is_running is False
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_initialization_with_custom_parameters(self, mock_picamera2, mock_imx500):
        """Test initialization with custom parameters."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        # Test with custom parameters
        camera = PiAICamera(
            model_path="/custom/model.rpk",
            confidence_threshold=0.7,
            iou_threshold=0.5,
            max_detections=5,
            inference_rate=25
        )
        
        assert camera.model_path == "/custom/model.rpk"
        assert camera.confidence_threshold == 0.7
        assert camera.iou_threshold == 0.5
        assert camera.max_detections == 5
        assert camera.inference_rate == 25
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_initialization_wrong_task(self, mock_picamera2, mock_imx500):
        """Test initialization with wrong network task."""
        # Mock IMX500 with wrong task
        mock_intrinsics = Mock()
        mock_intrinsics.task = "classification"  # Wrong task
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        with pytest.raises(ValueError, match="Network is not an object detection task"):
            PiAICamera()
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_start_success(self, mock_picamera2, mock_imx500):
        """Test successful camera start."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.inference_rate = 30
        mock_intrinsics.preserve_aspect_ratio = False
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500_instance.show_network_fw_progress_bar = Mock()
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2_instance.create_preview_configuration.return_value = {}
        mock_picamera2_instance.start = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        result = camera.start()
        
        assert result is True
        assert camera.is_running is True
        mock_picamera2_instance.start.assert_called_once()
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_start_failure(self, mock_picamera2, mock_imx500):
        """Test camera start failure."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.inference_rate = 30
        mock_intrinsics.preserve_aspect_ratio = False
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500_instance.show_network_fw_progress_bar = Mock()
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2 with failure
        mock_picamera2_instance = Mock()
        mock_picamera2_instance.create_preview_configuration.return_value = {}
        mock_picamera2_instance.start.side_effect = Exception("Start failed")
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        result = camera.start()
        
        assert result is False
        assert camera.is_running is False
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_get_frame_success(self, mock_picamera2, mock_imx500):
        """Test successful frame capture."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2_instance.capture_array.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_picamera2_instance.capture_metadata.return_value = {"test": "metadata"}
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        camera.is_running = True
        
        frame = camera.get_frame()
        
        assert frame is not None
        assert frame.shape == (480, 640, 3)
        assert camera.last_metadata == {"test": "metadata"}
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_get_frame_not_running(self, mock_picamera2, mock_imx500):
        """Test frame capture when camera is not running."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        camera.is_running = False
        
        frame = camera.get_frame()
        
        assert frame is None
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_get_detections_empty(self, mock_picamera2, mock_imx500):
        """Test getting detections when no metadata available."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        camera.last_metadata = None
        
        detections = camera.get_detections()
        
        assert detections == []
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_get_resolution(self, mock_picamera2, mock_imx500):
        """Test getting camera resolution."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2_instance.camera_configuration.return_value = {
            "main": {"size": [1280, 720]}
        }
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        camera.picam2 = mock_picamera2_instance
        
        width, height = camera.get_resolution()
        
        assert width == 1280
        assert height == 720
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_get_resolution_fallback(self, mock_picamera2, mock_imx500):
        """Test getting camera resolution with fallback."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2_instance.camera_configuration.side_effect = Exception("Config error")
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        camera.picam2 = mock_picamera2_instance
        
        width, height = camera.get_resolution()
        
        assert width == 640
        assert height == 480
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_stop(self, mock_picamera2, mock_imx500):
        """Test camera stop."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        camera.is_running = True
        camera.picam2 = mock_picamera2_instance
        
        camera.stop()
        
        assert camera.is_running is False
        assert camera.picam2 is None
        mock_picamera2_instance.stop.assert_called_once()
        mock_picamera2_instance.close.assert_called_once()
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_is_available(self, mock_picamera2, mock_imx500):
        """Test camera availability check."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = None
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        
        # Test when not running
        assert camera.is_available() is False
        
        # Test when running
        camera.is_running = True
        camera.picam2 = mock_picamera2_instance
        assert camera.is_available() is True
    
    @patch('raspibot.vision.pi_ai_camera.PICAMERA2_AVAILABLE', True)
    @patch('raspibot.vision.pi_ai_camera.IMX500')
    @patch('raspibot.vision.pi_ai_camera.Picamera2')
    def test_get_model_info(self, mock_picamera2, mock_imx500):
        """Test getting model information."""
        # Mock IMX500 and intrinsics
        mock_intrinsics = Mock()
        mock_intrinsics.task = "object detection"
        mock_intrinsics.labels = ["person"]
        mock_intrinsics.update_with_defaults = Mock()
        
        mock_imx500_instance = Mock()
        mock_imx500_instance.network_intrinsics = mock_intrinsics
        mock_imx500_instance.camera_num = 0
        mock_imx500.return_value = mock_imx500_instance
        
        # Mock Picamera2
        mock_picamera2_instance = Mock()
        mock_picamera2.return_value = mock_picamera2_instance
        
        camera = PiAICamera()
        
        info = camera.get_model_info()
        
        assert "model_path" in info
        assert "task" in info
        assert "labels" in info
        assert "confidence_threshold" in info
        assert "iou_threshold" in info
        assert "max_detections" in info
        assert "inference_rate" in info


class TestCameraFactory:
    """Test camera factory functionality."""
    
    def test_create_camera_auto_with_pi_ai_available(self):
        """Test auto camera creation when Pi AI is available."""
        with patch.object(CameraFactory, 'is_pi_ai_available', return_value=True):
            with patch('raspibot.vision.pi_ai_camera.PiAICamera') as mock_pi_ai:
                mock_camera = Mock()
                mock_pi_ai.return_value = mock_camera
    
                camera = CameraFactory.create_camera(CameraType.AUTO)
    
                # Check that the camera is the right type, not necessarily the same object
                assert isinstance(camera, type(mock_camera))
                mock_pi_ai.assert_called_once()
    
    def test_create_camera_auto_with_pi_ai_unavailable(self):
        """Test auto camera creation when Pi AI is unavailable."""
        with patch.object(CameraFactory, 'is_pi_ai_available', return_value=False):
            with patch('raspibot.vision.camera.Camera') as mock_webcam:
                mock_camera = Mock()
                mock_webcam.return_value = mock_camera
    
                camera = CameraFactory.create_camera(CameraType.AUTO)
    
                # Check that the camera is the right type, not necessarily the same object
                assert isinstance(camera, type(mock_camera))
                mock_webcam.assert_called_once()
    
    def test_create_camera_webcam(self):
        """Test explicit webcam creation."""
        with patch('raspibot.vision.camera.Camera') as mock_webcam:
            mock_camera = Mock()
            mock_webcam.return_value = mock_camera
    
            camera = CameraFactory.create_camera(CameraType.WEBCAM)
    
            # Check that the camera is the right type, not necessarily the same object
            assert isinstance(camera, type(mock_camera))
            mock_webcam.assert_called_once()
    
    def test_create_camera_pi_ai(self):
        """Test explicit Pi AI camera creation."""
        with patch('raspibot.vision.pi_ai_camera.PiAICamera') as mock_pi_ai:
            mock_camera = Mock()
            mock_pi_ai.return_value = mock_camera
            
            camera = CameraFactory.create_camera(CameraType.PI_AI)
            
            # Check that the camera is the right type, not necessarily the same object
            assert isinstance(camera, type(mock_camera))
            mock_pi_ai.assert_called_once()
    
    def test_create_camera_invalid_type(self):
        """Test camera creation with invalid type."""
        with pytest.raises(ValueError, match="Invalid camera type"):
            CameraFactory.create_camera("invalid")
    
    def test_is_pi_ai_available_true(self):
        """Test Pi AI availability check when available."""
        with patch('raspibot.vision.pi_ai_camera.PiAICamera') as mock_pi_ai:
            mock_camera = Mock()
            mock_camera.stop = Mock()
            mock_pi_ai.return_value = mock_camera
            
            result = CameraFactory.is_pi_ai_available()
            
            # Since we're mocking PiAICamera, it should return True
            assert result is True
            mock_camera.stop.assert_called_once()
    
    def test_is_pi_ai_available_false(self):
        """Test Pi AI availability check when unavailable."""
        with patch('raspibot.vision.pi_ai_camera.PiAICamera', side_effect=ImportError):
            result = CameraFactory.is_pi_ai_available()
            
            assert result is False
    
    def test_get_available_cameras(self):
        """Test getting available camera types."""
        with patch.object(CameraFactory, 'is_pi_ai_available', return_value=True):
            available = CameraFactory.get_available_cameras()
            
            assert CameraType.WEBCAM in available
            assert CameraType.PI_AI in available
            assert len(available) == 2
    
    def test_get_recommended_camera_pi_ai(self):
        """Test getting recommended camera when Pi AI is available."""
        with patch.object(CameraFactory, 'is_pi_ai_available', return_value=True):
            recommended = CameraFactory.get_recommended_camera()
            
            assert recommended == CameraType.PI_AI
    
    def test_get_recommended_camera_webcam(self):
        """Test getting recommended camera when Pi AI is unavailable."""
        with patch.object(CameraFactory, 'is_pi_ai_available', return_value=False):
            recommended = CameraFactory.get_recommended_camera()
            
            assert recommended == CameraType.WEBCAM 