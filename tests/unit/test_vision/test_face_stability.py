"""Unit tests for FaceStabilityFilter class."""

import pytest
import time
from unittest.mock import patch

from raspibot.vision.face_stability import FaceStabilityFilter


class TestFaceStabilityFilter:
    """Test FaceStabilityFilter class functionality."""

    def test_face_stability_filter_initialization(self):
        """Test face stability filter initialization."""
        filter = FaceStabilityFilter()
        
        assert filter.stability_threshold == 30.0
        assert filter.stability_frames == 3
        assert filter.history_window == 2.0
        assert len(filter.face_history) == 0

    def test_face_stability_filter_custom_params(self):
        """Test face stability filter with custom parameters."""
        filter = FaceStabilityFilter(
            stability_threshold=50.0,
            stability_frames=5,
            history_window=3.0
        )
        
        assert filter.stability_threshold == 50.0
        assert filter.stability_frames == 5
        assert filter.history_window == 3.0

    def test_get_face_center(self):
        """Test face center calculation."""
        filter = FaceStabilityFilter()
        
        face = (100, 200, 50, 60)
        center = filter._get_face_center(face)
        
        assert center == (125, 230)  # (100 + 50//2, 200 + 60//2)

    def test_calculate_distance(self):
        """Test distance calculation between points."""
        filter = FaceStabilityFilter()
        
        point1 = (0, 0)
        point2 = (3, 4)
        distance = filter._calculate_distance(point1, point2)
        
        assert distance == 5.0  # 3-4-5 triangle

    def test_check_face_stability_insufficient_frames(self):
        """Test stability check with insufficient frames."""
        filter = FaceStabilityFilter(stability_frames=3)
        
        # Add only 2 faces (less than required 3)
        face1 = (100, 100, 50, 50)
        face2 = (105, 105, 50, 50)
        
        result1 = filter.check_face_stability(face1)
        result2 = filter.check_face_stability(face2)
        
        assert result1 is None
        assert result2 is None
        assert len(filter.face_history) == 2

    def test_check_face_stability_stable_face(self):
        """Test stability check with stable face sequence."""
        filter = FaceStabilityFilter(stability_threshold=30.0, stability_frames=3)
        
        # Add 3 stable faces (small movements)
        face1 = (100, 100, 50, 50)
        face2 = (105, 105, 50, 50)  # 5px movement
        face3 = (110, 110, 50, 50)  # 5px movement
        
        filter.check_face_stability(face1)
        filter.check_face_stability(face2)
        result = filter.check_face_stability(face3)
        
        assert result == face3  # Should return stable face
        assert len(filter.face_history) == 3

    def test_check_face_stability_unstable_face(self):
        """Test stability check with unstable face sequence."""
        filter = FaceStabilityFilter(stability_threshold=20.0, stability_frames=3)
        
        # Add faces with large movements
        face1 = (100, 100, 50, 50)
        face2 = (150, 150, 50, 50)  # 70px movement
        face3 = (110, 110, 50, 50)  # Large movement from face2
        
        filter.check_face_stability(face1)
        filter.check_face_stability(face2)
        result = filter.check_face_stability(face3)
        
        assert result is None  # Should be unstable due to large movements

    def test_is_face_stable_with_history(self):
        """Test is_face_stable with existing history."""
        filter = FaceStabilityFilter(stability_threshold=30.0)
        
        # Build up some history
        face1 = (100, 100, 50, 50)
        face2 = (105, 105, 50, 50)
        filter.check_face_stability(face1)
        filter.check_face_stability(face2)
        
        # Test a face close to existing history
        test_face = (108, 108, 50, 50)
        result = filter.is_face_stable(test_face)
        
        assert result is True

    def test_is_face_stable_no_history(self):
        """Test is_face_stable with no history."""
        filter = FaceStabilityFilter()
        
        face = (100, 100, 50, 50)
        result = filter.is_face_stable(face)
        
        assert result is False

    def test_get_stable_faces(self):
        """Test getting stable faces from a list."""
        filter = FaceStabilityFilter()
        
        # Mock is_face_stable to return specific results
        def mock_is_stable(face):
            if face == (100, 100, 50, 50):
                return True
            return False
        
        filter.is_face_stable = mock_is_stable
        
        all_faces = [(100, 100, 50, 50), (200, 200, 60, 60), (300, 300, 40, 40)]
        stable_faces = filter.get_stable_faces(all_faces)
        
        assert stable_faces == [(100, 100, 50, 50)]

    def test_reset_history(self):
        """Test history reset."""
        filter = FaceStabilityFilter()
        
        # Add some history
        filter.face_history = [(time.time(), (100, 100), (100, 100, 50, 50))]
        assert len(filter.face_history) == 1
        
        filter.reset_history()
        
        assert len(filter.face_history) == 0

    @patch('time.time')
    def test_cleanup_history_removes_old_entries(self, mock_time):
        """Test that cleanup removes old history entries."""
        filter = FaceStabilityFilter(history_window=2.0)
        
        # Set current time
        current_time = 1000.0
        mock_time.return_value = current_time
        
        # Add entries with different timestamps
        filter.face_history = [
            (current_time - 3.0, (100, 100), (100, 100, 50, 50)),  # Too old
            (current_time - 1.0, (110, 110), (110, 110, 50, 50)),  # Recent
            (current_time - 0.5, (120, 120), (120, 120, 50, 50)),  # Recent
        ]
        
        filter._cleanup_history()
        
        # Should keep only recent entries
        assert len(filter.face_history) == 2
        assert all(current_time - t < 2.0 for t, _, _ in filter.face_history)

    @patch('time.time')
    def test_stability_over_time_window(self, mock_time):
        """Test stability checking over time window."""
        filter = FaceStabilityFilter(stability_frames=2, stability_threshold=20.0)
        
        # Start at time 0
        mock_time.return_value = 0.0
        face1 = (100, 100, 50, 50)
        filter.check_face_stability(face1)
        
        # Move to time 1
        mock_time.return_value = 1.0
        face2 = (110, 110, 50, 50)  # 14px movement, should be stable
        result = filter.check_face_stability(face2)
        
        assert result == face2  # Should be stable
        assert len(filter.face_history) == 2 