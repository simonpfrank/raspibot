"""Unit tests for SimpleFaceTracker class."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import time

from raspibot.vision.simple_face_tracker import SimpleFaceTracker


class TestSimpleFaceTracker:
    """Test SimpleFaceTracker class functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_pan_tilt = Mock()
        self.mock_pan_tilt.get_current_coordinates.return_value = (0.0, 0.0)
        
    def test_simple_face_tracker_initialization(self):
        """Test simple face tracker initialization."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt, 1280, 480)
        
        assert tracker.camera_width == 1280
        assert tracker.camera_height == 480
        assert tracker.movement_threshold == 50  # From config
        assert tracker.movement_scale == 0.3     # From config
        assert tracker.face_detector is not None
        assert tracker.stability_filter is not None

    def test_simple_face_tracker_custom_resolution(self):
        """Test simple face tracker with custom resolution."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt, 640, 360)
        
        assert tracker.camera_width == 640
        assert tracker.camera_height == 360

    @patch('raspibot.vision.simple_face_tracker.FaceDetector')
    def test_track_face_no_faces(self, mock_face_detector_class):
        """Test tracking with no faces detected."""
        mock_detector = Mock()
        mock_detector.detect_faces.return_value = []
        mock_face_detector_class.return_value = mock_detector
        
        tracker = SimpleFaceTracker(self.mock_pan_tilt)
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face is None
        assert all_faces == []
        mock_detector.detect_faces.assert_called_once_with(frame)

    @patch('raspibot.vision.simple_face_tracker.FaceDetector')
    def test_track_face_with_faces_unstable(self, mock_face_detector_class):
        """Test tracking with unstable faces."""
        mock_detector = Mock()
        mock_detector.detect_faces.return_value = [(100, 100, 50, 50), (200, 200, 60, 60)]
        mock_detector.get_largest_face.return_value = (200, 200, 60, 60)
        mock_face_detector_class.return_value = mock_detector
        
        tracker = SimpleFaceTracker(self.mock_pan_tilt)
        # Mock stability filter to return None (unstable)
        tracker.stability_filter.check_face_stability = Mock(return_value=None)
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face is None
        assert all_faces == [(100, 100, 50, 50), (200, 200, 60, 60)]
        tracker.stability_filter.check_face_stability.assert_called_once_with((200, 200, 60, 60))

    @patch('raspibot.vision.simple_face_tracker.FaceDetector')
    def test_track_face_with_stable_face(self, mock_face_detector_class):
        """Test tracking with stable face."""
        mock_detector = Mock()
        mock_detector.detect_faces.return_value = [(100, 100, 50, 50)]
        mock_detector.get_largest_face.return_value = (100, 100, 50, 50)
        mock_face_detector_class.return_value = mock_detector
        
        tracker = SimpleFaceTracker(self.mock_pan_tilt)
        # Mock stability filter to return stable face
        tracker.stability_filter.check_face_stability = Mock(return_value=(100, 100, 50, 50))
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face == (100, 100, 50, 50)
        assert all_faces == [(100, 100, 50, 50)]
        
        # Should update last_face_time
        assert tracker.last_face_time > 0

    def test_center_on_face_no_movement_needed(self):
        """Test centering on face when already centered."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt, 1280, 480)
        
        # Face at center of camera (640, 240)
        face = (615, 215, 50, 50)  # Center at (640, 240)
        
        tracker._center_on_face(face)
        
        # Should not move pan/tilt since face is centered within threshold
        self.mock_pan_tilt.move_to_coordinates.assert_not_called()

    def test_center_on_face_movement_needed(self):
        """Test centering on face when movement is needed."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt, 1280, 480)
        self.mock_pan_tilt.get_current_coordinates.return_value = (0.0, 0.0)
        
        # Face significantly off-center
        face = (800, 300, 50, 50)  # Center at (825, 325)
        
        tracker._center_on_face(face)
        
        # Should move pan/tilt to center on face
        self.mock_pan_tilt.move_to_coordinates.assert_called_once()
        args = self.mock_pan_tilt.move_to_coordinates.call_args[0]
        new_x, new_y = args
        
        # Should move right and down
        assert new_x > 0
        assert new_y > 0

    def test_get_face_center(self):
        """Test face center calculation."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt)
        
        face = (100, 200, 50, 60)
        center = tracker._get_face_center(face)
        
        assert center == (125, 230)  # (100 + 50//2, 200 + 60//2)

    def test_reset_tracking(self):
        """Test tracking reset."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt)
        tracker.stability_filter.reset_history = Mock()
        
        old_time = tracker.last_face_time
        time.sleep(0.01)  # Small delay
        
        tracker.reset_tracking()
        
        tracker.stability_filter.reset_history.assert_called_once()
        assert tracker.last_face_time > old_time

    def test_get_time_since_last_face(self):
        """Test time since last face calculation."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt)
        
        # Set known time
        test_time = time.time() - 5.0
        tracker.last_face_time = test_time
        
        time_since = tracker.get_time_since_last_face()
        
        assert abs(time_since - 5.0) < 0.1  # Allow small tolerance

    def test_get_stable_faces(self):
        """Test getting stable faces."""
        tracker = SimpleFaceTracker(self.mock_pan_tilt)
        tracker.stability_filter.get_stable_faces = Mock(return_value=[(100, 100, 50, 50)])
        
        all_faces = [(100, 100, 50, 50), (200, 200, 60, 60)]
        stable_faces = tracker.get_stable_faces(all_faces)
        
        assert stable_faces == [(100, 100, 50, 50)]
        tracker.stability_filter.get_stable_faces.assert_called_once_with(all_faces) 