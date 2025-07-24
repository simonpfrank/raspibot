"""Unit tests for FaceTracker class."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import time

from raspibot.vision.face_tracker import FaceTracker


class TestFaceTracker:
    """Test FaceTracker class functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_pan_tilt = Mock()
        self.mock_pan_tilt.get_current_coordinates.return_value = (0.0, 0.0)
        
    def test_face_tracker_initialization(self):
        """Test face tracker initialization."""
        tracker = FaceTracker(self.mock_pan_tilt, 1280, 480)
        
        assert tracker.camera_width == 1280
        assert tracker.camera_height == 480
        assert tracker.movement_threshold == 50
        assert tracker.movement_scale == 0.3
        assert tracker.stability_threshold == 100
        assert tracker.stability_frames == 3
        assert tracker.sleep_timeout == 300
        assert tracker.is_sleeping is False
        assert len(tracker.face_history) == 0

    def test_face_tracker_custom_resolution(self):
        """Test face tracker with custom resolution."""
        tracker = FaceTracker(self.mock_pan_tilt, 640, 360)
        
        assert tracker.camera_width == 640
        assert tracker.camera_height == 360

    @patch('raspibot.vision.face_tracker.FaceDetector')
    def test_track_face_no_faces(self, mock_face_detector_class):
        """Test tracking with no faces detected."""
        mock_detector = Mock()
        mock_detector.detect_faces.return_value = []
        mock_detector.get_largest_face.return_value = None
        mock_face_detector_class.return_value = mock_detector
        
        tracker = FaceTracker(self.mock_pan_tilt)
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face is None
        assert all_faces == []

    @patch('raspibot.vision.face_tracker.FaceDetector')
    @patch('time.time')
    def test_track_face_stable_face(self, mock_time, mock_face_detector_class):
        """Test tracking with stable face."""
        mock_detector = Mock()
        mock_detector.detect_faces.return_value = [(100, 100, 80, 80)]
        mock_detector.get_largest_face.return_value = (100, 100, 80, 80)
        mock_detector.get_face_center.return_value = (140, 140)
        mock_face_detector_class.return_value = mock_detector
        
        # Mock time for stability check
        mock_time.return_value = 1.0
        
        tracker = FaceTracker(self.mock_pan_tilt)
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        # Need multiple frames for stability
        for i in range(4):
            mock_time.return_value = 1.0 + i * 0.1
            stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face == (100, 100, 80, 80)
        assert all_faces == [(100, 100, 80, 80)]

    @patch('raspibot.vision.face_tracker.FaceDetector')
    @patch('time.time')
    def test_track_face_unstable_face(self, mock_time, mock_face_detector_class):
        """Test tracking with unstable (moving) face."""
        mock_detector = Mock()
        # Simulate moving face
        mock_detector.detect_faces.side_effect = [
            [(100, 100, 80, 80)],
            [(250, 250, 80, 80)],  # Moved too far
        ]
        mock_detector.get_largest_face.side_effect = [
            (100, 100, 80, 80),
            (250, 250, 80, 80),
        ]
        mock_detector.get_face_center.side_effect = [
            (140, 140),
            (290, 290),
        ]
        mock_face_detector_class.return_value = mock_detector
        
        mock_time.return_value = 1.0
        
        tracker = FaceTracker(self.mock_pan_tilt)
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        # First frame
        stable_face, all_faces = tracker.track_face(frame)
        assert stable_face is None  # Not enough frames for stability
        
        # Second frame with moved face
        mock_time.return_value = 1.1
        stable_face, all_faces = tracker.track_face(frame)
        assert stable_face is None  # Face moved too much

    @patch('raspibot.vision.face_tracker.FaceDetector')
    @patch('time.time')
    def test_sleep_mode_activation(self, mock_time, mock_face_detector_class):
        """Test sleep mode activation after timeout."""
        mock_detector = Mock()
        mock_detector.detect_faces.return_value = []
        mock_detector.get_largest_face.return_value = None
        mock_face_detector_class.return_value = mock_detector
        
        # Set initial time
        mock_time.return_value = 1000.0
        
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.sleep_timeout = 5  # Short timeout for testing
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        # First call - no sleep yet
        stable_face, all_faces = tracker.track_face(frame)
        assert tracker.is_sleeping is False
        
        # Move time forward past timeout
        mock_time.return_value = 1006.0
        stable_face, all_faces = tracker.track_face(frame)
        assert tracker.is_sleeping is True
        
        # Verify sleep sequence was called
        assert self.mock_pan_tilt.move_to_coordinates.call_count >= 4

    @patch('raspibot.vision.face_tracker.FaceDetector')
    @patch('time.time')
    def test_wake_up_from_sleep(self, mock_time, mock_face_detector_class):
        """Test waking up from sleep when face detected."""
        mock_detector = Mock()
        mock_detector.get_face_center.return_value = (140, 140)
        mock_face_detector_class.return_value = mock_detector
        
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.is_sleeping = True  # Start in sleep mode
        
        # Mock stable face detection
        mock_detector.detect_faces.return_value = [(100, 100, 80, 80)]
        mock_detector.get_largest_face.return_value = (100, 100, 80, 80)
        mock_time.return_value = 1.0
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        # Need multiple frames for stability
        for i in range(4):
            mock_time.return_value = 1.0 + i * 0.1
            stable_face, all_faces = tracker.track_face(frame)
        
        assert tracker.is_sleeping is False
        # Verify wake sequence was called
        assert self.mock_pan_tilt.move_to_coordinates.call_count >= 4

    def test_get_stable_faces(self):
        """Test getting list of stable faces."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        # Mock face history with stable face
        tracker.face_history = [
            (1.0, (140, 140), (100, 100, 80, 80)),
            (1.1, (142, 142), (100, 100, 80, 80)),
            (1.2, (141, 141), (100, 100, 80, 80)),
        ]
        
        all_faces = [(100, 100, 80, 80), (300, 300, 60, 60)]
        stable_faces = tracker.get_stable_faces(all_faces)
        
        assert len(stable_faces) <= len(all_faces)

    def test_center_on_face_significant_offset(self):
        """Test centering on face with significant offset."""
        tracker = FaceTracker(self.mock_pan_tilt, 1280, 480)
        
        with patch.object(tracker.face_detector, 'get_face_center', return_value=(100, 100)):
            tracker._center_on_face((50, 50, 100, 100))
        
        # Should have called move_to_coordinates due to significant offset
        self.mock_pan_tilt.move_to_coordinates.assert_called_once()

    def test_center_on_face_small_offset(self):
        """Test centering on face with small offset (below threshold)."""
        tracker = FaceTracker(self.mock_pan_tilt, 1280, 480)
        
        # Center of frame is (640, 240), face center at (650, 250) - small offset
        with patch.object(tracker.face_detector, 'get_face_center', return_value=(650, 250)):
            tracker._center_on_face((600, 200, 100, 100))
        
        # Should not move due to small offset
        self.mock_pan_tilt.move_to_coordinates.assert_not_called()

    def test_force_wake_up(self):
        """Test force wake up functionality."""
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.is_sleeping = True
        
        tracker.force_wake_up()
        
        assert tracker.is_sleeping is False
        # Verify wake sequence was called
        assert self.mock_pan_tilt.move_to_coordinates.call_count >= 4

    def test_force_sleep(self):
        """Test force sleep functionality."""
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.is_sleeping = False
        
        tracker.force_sleep()
        
        assert tracker.is_sleeping is True
        # Verify sleep sequence was called
        assert self.mock_pan_tilt.move_to_coordinates.call_count >= 4

    def test_get_sleep_status(self):
        """Test get sleep status."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        assert tracker.get_sleep_status() is False
        
        tracker.is_sleeping = True
        assert tracker.get_sleep_status() is True

    @patch('time.time')
    def test_reset_sleep_timer(self, mock_time):
        """Test reset sleep timer."""
        mock_time.return_value = 1000.0
        
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.reset_sleep_timer()
        
        assert tracker.last_face_time == 1000.0

    @patch('time.time')
    def test_get_time_until_sleep(self, mock_time):
        """Test get time until sleep."""
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.sleep_timeout = 300
        tracker.last_face_time = 1000.0
        
        # 100 seconds elapsed, 200 remaining
        mock_time.return_value = 1100.0
        remaining = tracker.get_time_until_sleep()
        assert remaining == 200.0
        
        # Past timeout
        mock_time.return_value = 1400.0
        remaining = tracker.get_time_until_sleep()
        assert remaining == 0.0
        
        # Already sleeping
        tracker.is_sleeping = True
        remaining = tracker.get_time_until_sleep()
        assert remaining == 0.0

    def test_calculate_distance(self):
        """Test distance calculation between points."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        # Test distance calculation
        distance = tracker._calculate_distance((0, 0), (3, 4))
        assert distance == 5.0  # 3-4-5 triangle
        
        distance = tracker._calculate_distance((100, 100), (100, 100))
        assert distance == 0.0  # Same point

    @patch('time.time')
    def test_cleanup_face_history(self, mock_time):
        """Test cleanup of old face history."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        # Add old and new history
        tracker.face_history = [
            (1.0, (140, 140), (100, 100, 80, 80)),  # Old
            (4.5, (142, 142), (100, 100, 80, 80)),  # Recent
        ]
        
        mock_time.return_value = 5.0
        tracker._cleanup_face_history()
        
        # Should keep only recent history (within 2 seconds)
        assert len(tracker.face_history) == 1
        assert tracker.face_history[0][0] == 4.5 