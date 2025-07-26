"""Unit tests for FaceTracker class (refactored version)."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import time

from raspibot.vision.face_tracker import FaceTracker


class TestFaceTracker:
    """Test FaceTracker class functionality (refactored version)."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_pan_tilt = Mock()
        self.mock_pan_tilt.get_current_coordinates.return_value = (0.0, 0.0)
        
    def test_face_tracker_initialization(self):
        """Test face tracker initialization."""
        tracker = FaceTracker(self.mock_pan_tilt, 1280, 480)
        
        assert tracker.camera_width == 1280
        assert tracker.camera_height == 480
        assert tracker.sleep_timeout == 300  # From config
        assert tracker.is_sleeping is False
        assert tracker.simple_tracker is not None
        assert tracker.search_pattern_enabled is not None

    def test_face_tracker_custom_resolution(self):
        """Test face tracker with custom resolution."""
        tracker = FaceTracker(self.mock_pan_tilt, 640, 360)
        
        assert tracker.camera_width == 640
        assert tracker.camera_height == 360

    def test_track_face_no_faces(self):
        """Test tracking with no faces detected."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        # Mock the simple tracker to return no faces
        tracker.simple_tracker.track_face = Mock(return_value=(None, []))
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face is None
        assert all_faces == []
        tracker.simple_tracker.track_face.assert_called_once_with(frame)

    def test_track_face_with_stable_face(self):
        """Test tracking with stable face detected."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        # Mock the simple tracker to return a stable face
        test_face = (100, 100, 50, 50)
        all_faces = [test_face]
        tracker.simple_tracker.track_face = Mock(return_value=(test_face, all_faces))
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, detected_faces = tracker.track_face(frame)
        
        assert stable_face == test_face
        assert detected_faces == all_faces
        tracker.simple_tracker.track_face.assert_called_once_with(frame)

    def test_track_face_wakes_up_from_sleep(self):
        """Test that detecting a face wakes up from sleep mode."""
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.is_sleeping = True
        
        # Mock wake up method
        tracker._wake_up = Mock()
        
        # Mock the simple tracker to return a stable face
        test_face = (100, 100, 50, 50)
        tracker.simple_tracker.track_face = Mock(return_value=(test_face, [test_face]))
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face == test_face
        tracker._wake_up.assert_called_once()

    def test_sleep_functionality(self):
        """Test sleep mode functionality."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        assert tracker.get_sleep_status() is False
        
        tracker.force_sleep()
        
        assert tracker.get_sleep_status() is True
        # Should have called move_to_coordinates for sleep sequence
        assert self.mock_pan_tilt.move_to_coordinates.call_count > 0

    def test_wake_functionality(self):
        """Test wake up functionality."""
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.is_sleeping = True
        
        tracker.force_wake_up()
        
        assert tracker.get_sleep_status() is False
        # Should have called move_to_coordinates for wake sequence
        assert self.mock_pan_tilt.move_to_coordinates.call_count > 0

    def test_sleep_timer_management(self):
        """Test sleep timer management."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        # Set a specific time
        test_time = time.time() - 100
        tracker.simple_tracker.last_face_time = test_time
        
        time_until_sleep = tracker.get_time_until_sleep()
        
        # Should be sleep_timeout - 100 seconds
        expected = tracker.sleep_timeout - 100
        assert abs(time_until_sleep - expected) < 1.0

    def test_reset_sleep_timer(self):
        """Test resetting the sleep timer."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        old_time = tracker.simple_tracker.last_face_time
        time.sleep(0.01)  # Small delay
        
        tracker.reset_sleep_timer()
        
        assert tracker.simple_tracker.last_face_time > old_time

    def test_get_stable_faces_delegation(self):
        """Test that get_stable_faces delegates to simple tracker."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        all_faces = [(100, 100, 50, 50), (200, 200, 60, 60)]
        expected_stable = [(100, 100, 50, 50)]
        
        tracker.simple_tracker.get_stable_faces = Mock(return_value=expected_stable)
        
        result = tracker.get_stable_faces(all_faces)
        
        assert result == expected_stable
        tracker.simple_tracker.get_stable_faces.assert_called_once_with(all_faces)

    @patch('raspibot.vision.face_tracker.SearchPattern')
    def test_search_pattern_initialization(self, mock_search_pattern_class):
        """Test search pattern initialization when enabled."""
        # Mock search pattern enabled
        with patch('raspibot.vision.face_tracker.SEARCH_PATTERN_ENABLED', True):
            tracker = FaceTracker(self.mock_pan_tilt)
            
            assert tracker.search_pattern is not None
            mock_search_pattern_class.assert_called_once()

    def test_search_pattern_disabled(self):
        """Test behavior when search pattern is disabled."""
        # Mock search pattern disabled
        with patch('raspibot.vision.face_tracker.SEARCH_PATTERN_ENABLED', False):
            tracker = FaceTracker(self.mock_pan_tilt)
            
            status = tracker.get_search_status()
            
            assert status["enabled"] is False
            assert status["active"] is False

    def test_search_interval_setting(self):
        """Test setting search interval."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        tracker.set_search_interval(60.0)
        
        assert tracker.search_interval == 60.0

    def test_search_interval_minimum(self):
        """Test search interval minimum value enforcement."""
        tracker = FaceTracker(self.mock_pan_tilt)
        
        tracker.set_search_interval(1.0)  # Below minimum
        
        assert tracker.search_interval == 5.0  # Should be set to minimum

    def test_auto_sleep_after_timeout(self):
        """Test automatic sleep after timeout period."""
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker._go_to_sleep = Mock()
        
        # Set last face time to long ago
        tracker.simple_tracker.last_face_time = time.time() - (tracker.sleep_timeout + 10)
        
        # Mock simple tracker to return no faces
        tracker.simple_tracker.track_face = Mock(return_value=(None, []))
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face is None
        tracker._go_to_sleep.assert_called_once()

    def test_no_auto_sleep_when_already_sleeping(self):
        """Test that auto sleep doesn't trigger when already sleeping."""
        tracker = FaceTracker(self.mock_pan_tilt)
        tracker.is_sleeping = True
        tracker._go_to_sleep = Mock()
        
        # Set last face time to long ago
        tracker.simple_tracker.last_face_time = time.time() - (tracker.sleep_timeout + 10)
        
        # Mock simple tracker to return no faces
        tracker.simple_tracker.track_face = Mock(return_value=(None, []))
        
        frame = np.zeros((480, 1280, 3), dtype=np.uint8)
        
        tracker.track_face(frame)
        
        # Should not call _go_to_sleep since already sleeping
        tracker._go_to_sleep.assert_not_called() 