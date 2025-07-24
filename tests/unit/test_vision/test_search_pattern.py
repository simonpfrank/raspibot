"""Unit tests for SearchPattern class."""

import pytest
import time
from unittest.mock import Mock, patch

from raspibot.vision.search_pattern import SearchPattern, SearchDirection
from raspibot.movement.pan_tilt import PanTiltSystem


class TestSearchPattern:
    """Test SearchPattern class functionality."""

    def test_search_pattern_initialization(self):
        """Test search pattern initialization."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        assert search_pattern.pan_steps == 8
        assert search_pattern.tilt_steps == 6
        assert search_pattern.movement_speed == 0.3
        assert search_pattern.is_searching is False
        assert len(search_pattern.search_positions) > 0

    def test_search_pattern_down_first_direction(self):
        """Test search pattern with down-first direction."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480, SearchDirection.DOWN_FIRST)
        
        # Should start from top (minimum tilt angle)
        first_position = search_pattern.search_positions[0]
        assert first_position[1] == 90  # Tilt should start at 90° (up)

    def test_search_pattern_up_first_direction(self):
        """Test search pattern with up-first direction."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480, SearchDirection.UP_FIRST)
        
        # Should start from bottom (maximum tilt angle)
        first_position = search_pattern.search_positions[0]
        assert first_position[1] == 310  # Tilt should start at 310° (down)

    def test_search_pattern_raster_scan(self):
        """Test that search positions follow raster scan pattern."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        # Check that we have the expected number of positions
        # For raster scan: pan_steps * tilt_steps (each tilt level goes left-right, then right-left)
        expected_positions = 8 * 6  # pan_steps * tilt_steps
        assert len(search_pattern.search_positions) == expected_positions
        
        # Check that pan angles are within valid range
        for pan_angle, tilt_angle in search_pattern.search_positions:
            assert 0 <= pan_angle <= 180  # Valid pan range
            assert 90 <= tilt_angle <= 310  # Valid tilt range

    @patch('time.sleep')
    def test_start_search_success(self, mock_sleep):
        """Test successful search pattern start."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        mock_pan_tilt.smooth_move_to_angles.return_value = None
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        # Mock face detection callback that returns True (faces found)
        def face_callback():
            return True
        
        result = search_pattern.start_search(face_callback)
        
        assert result is True
        assert search_pattern.is_searching is False  # Should be False after completion
        mock_pan_tilt.smooth_move_to_angles.assert_called()

    @patch('time.sleep')
    def test_start_search_no_faces(self, mock_sleep):
        """Test search pattern when no faces are found."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        mock_pan_tilt.smooth_move_to_angles.return_value = None
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        # Mock face detection callback that returns False (no faces)
        def face_callback():
            return False
        
        result = search_pattern.start_search(face_callback)
        
        assert result is False
        assert search_pattern.is_searching is False

    def test_stop_search(self):
        """Test stopping search pattern."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        mock_pan_tilt.center_camera = Mock()  # Explicitly add center_camera method
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        # Should not crash when stopping inactive search
        search_pattern.stop_search()
        
        # When not searching, center_camera should not be called
        mock_pan_tilt.center_camera.assert_not_called()
        
        # Now test stopping an active search
        search_pattern.is_searching = True  # Simulate active search
        search_pattern.stop_search()
        
        # Should call center_camera when stopping active search (if return_to_center is True)
        if search_pattern.return_to_center:
            mock_pan_tilt.center_camera.assert_called()

    def test_search_status_methods(self):
        """Test search status methods."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        # Test status methods when not searching
        assert search_pattern.is_searching_active() is False
        assert search_pattern.get_search_progress() == (0, 48)  # 8*6 positions
        assert search_pattern.get_search_time_elapsed() == 0.0
        assert search_pattern.get_search_time_remaining() == 0.0

    def test_set_search_parameters(self):
        """Test updating search parameters."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        # Update parameters
        search_pattern.set_search_parameters(
            pan_steps=4,
            tilt_steps=3,
            movement_speed=0.5,
            direction=SearchDirection.UP_FIRST
        )
        
        assert search_pattern.pan_steps == 4
        assert search_pattern.tilt_steps == 3
        assert search_pattern.movement_speed == 0.5
        assert search_pattern.direction == SearchDirection.UP_FIRST
        
        # Should recalculate positions (4*3 = 12 positions)
        assert len(search_pattern.search_positions) == 12

    def test_search_parameters_validation(self):
        """Test search parameter validation."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        
        # Test speed clamping
        search_pattern.set_search_parameters(movement_speed=2.0)  # Too high
        assert search_pattern.movement_speed == 1.0
        
        search_pattern.set_search_parameters(movement_speed=-0.5)  # Too low
        assert search_pattern.movement_speed == 0.1

    def test_search_timeout(self):
        """Test search pattern timeout."""
        mock_pan_tilt = Mock(spec=PanTiltSystem)
        mock_pan_tilt.smooth_move_to_angles.return_value = None
        
        search_pattern = SearchPattern(mock_pan_tilt, 1280, 480)
        search_pattern.pattern_timeout = 0.1  # Very short timeout for testing
        
        def face_callback():
            time.sleep(0.2)  # Longer than timeout
            return False
        
        with patch('time.sleep'):
            result = search_pattern.start_search(face_callback)
        
        assert result is False  # Should timeout and return False 