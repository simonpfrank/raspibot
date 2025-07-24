"""Unit tests for Camera class."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from raspibot.vision.camera import Camera


class TestCamera:
    """Test Camera class functionality."""

    def test_camera_initialization(self):
        """Test camera initialization with default parameters."""
        camera = Camera()
        
        assert camera.device_id == 0
        assert camera.width == 1280
        assert camera.height == 480
        assert camera.cap is None
        assert camera.is_running is False
        assert camera.current_fps == 0.0

    def test_camera_initialization_custom_params(self):
        """Test camera initialization with custom parameters."""
        camera = Camera(device_id=1, width=640, height=480)
        
        assert camera.device_id == 1
        assert camera.width == 640
        assert camera.height == 480

    @patch('cv2.VideoCapture')
    def test_camera_start_success(self, mock_video_capture):
        """Test successful camera start."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]  # Return requested resolution
        mock_video_capture.return_value = mock_cap
        
        camera = Camera()
        result = camera.start()
        
        assert result is True
        assert camera.is_running is True
        assert camera.cap == mock_cap
        
        # Verify OpenCV calls
        mock_video_capture.assert_called_once_with(0)
        mock_cap.set.assert_any_call(3, 1280)  # CAP_PROP_FRAME_WIDTH
        mock_cap.set.assert_any_call(4, 480)   # CAP_PROP_FRAME_HEIGHT

    @patch('cv2.VideoCapture')
    def test_camera_start_failure(self, mock_video_capture):
        """Test camera start failure."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        camera = Camera()
        result = camera.start()
        
        assert result is False
        assert camera.is_running is False
        assert camera.cap is None

    @patch('cv2.VideoCapture')
    def test_camera_start_exception(self, mock_video_capture):
        """Test camera start with exception."""
        mock_video_capture.side_effect = Exception("Camera error")
        
        camera = Camera()
        result = camera.start()
        
        assert result is False
        assert camera.is_running is False

    @patch('cv2.VideoCapture')
    def test_camera_resolution_adjustment(self, mock_video_capture):
        """Test camera resolution adjustment when actual differs from requested."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [640, 360]  # Return different resolution
        mock_video_capture.return_value = mock_cap
        
        camera = Camera(width=1280, height=480)
        result = camera.start()
        
        assert result is True
        assert camera.width == 640
        assert camera.height == 360

    def test_get_frame_not_started(self):
        """Test get_frame when camera not started."""
        camera = Camera()
        frame = camera.get_frame()
        
        assert frame is None

    @patch('cv2.VideoCapture')
    def test_get_frame_success(self, mock_video_capture):
        """Test successful frame capture."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]
        mock_cap.read.return_value = (True, np.zeros((480, 1280, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_cap
        
        camera = Camera()
        camera.start()
        frame = camera.get_frame()
        
        assert frame is not None
        assert frame.shape == (480, 1280, 3)

    @patch('cv2.VideoCapture')
    def test_get_frame_failure(self, mock_video_capture):
        """Test frame capture failure."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]
        mock_cap.read.return_value = (False, None)
        mock_video_capture.return_value = mock_cap
        
        camera = Camera()
        camera.start()
        frame = camera.get_frame()
        
        assert frame is None

    @patch('cv2.VideoCapture')
    def test_get_frame_exception(self, mock_video_capture):
        """Test frame capture with exception."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]
        mock_cap.read.side_effect = Exception("Read error")
        mock_video_capture.return_value = mock_cap
        
        camera = Camera()
        camera.start()
        frame = camera.get_frame()
        
        assert frame is None

    def test_get_resolution(self):
        """Test get_resolution method."""
        camera = Camera(width=640, height=480)
        width, height = camera.get_resolution()
        
        assert width == 640
        assert height == 480

    def test_get_fps_initial(self):
        """Test get_fps returns 0 initially."""
        camera = Camera()
        fps = camera.get_fps()
        
        assert fps == 0.0

    def test_is_available_not_started(self):
        """Test is_available when camera not started."""
        camera = Camera()
        available = camera.is_available()
        
        assert available is False

    @patch('cv2.VideoCapture')
    def test_is_available_started(self, mock_video_capture):
        """Test is_available when camera started."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]
        mock_video_capture.return_value = mock_cap
        
        camera = Camera()
        camera.start()
        available = camera.is_available()
        
        assert available is True

    @patch('cv2.VideoCapture')
    def test_stop_camera(self, mock_video_capture):
        """Test camera stop."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]
        mock_video_capture.return_value = mock_cap
        
        camera = Camera()
        camera.start()
        camera.stop()
        
        assert camera.is_running is False
        assert camera.cap is None
        mock_cap.release.assert_called_once()

    def test_stop_camera_not_started(self):
        """Test stop when camera not started."""
        camera = Camera()
        camera.stop()  # Should not raise exception
        
        assert camera.is_running is False

    @patch('cv2.VideoCapture')
    def test_context_manager_success(self, mock_video_capture):
        """Test camera as context manager with successful start."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]
        mock_video_capture.return_value = mock_cap
        
        with Camera() as camera:
            assert camera.is_running is True
        
        mock_cap.release.assert_called_once()

    @patch('cv2.VideoCapture')
    def test_context_manager_failure(self, mock_video_capture):
        """Test camera as context manager with failed start."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        with pytest.raises(RuntimeError, match="Failed to start camera"):
            with Camera() as camera:
                pass

    @patch('cv2.VideoCapture')
    @patch('time.time')
    def test_fps_calculation(self, mock_time, mock_video_capture):
        """Test FPS calculation."""
        # Setup mock
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = [1280, 480]
        mock_cap.read.return_value = (True, np.zeros((480, 1280, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_cap
        
        # Mock time progression - need more time values for logging
        mock_time.side_effect = [0, 0, 0, 0, 0, 1.0, 1.0, 1.0]  # 1 second elapsed after 2 frames
        
        camera = Camera()
        camera.start()
        
        # Capture 2 frames
        camera.get_frame()
        camera.get_frame()
        
        # Should have calculated FPS
        assert camera.get_fps() == 2.0 