"""Tests for utility helper functions.

This module tests simple utility functions used across the project.
"""

import os
import tempfile
import pytest
from unittest.mock import patch

# Import the helpers module (will be created after tests)
# from raspibot.utils import helpers


class TestCorrelationIDGeneration:
    """Test correlation ID generation utilities."""

    def test_generate_correlation_id(self):
        """Test that correlation ID generation creates 8-character hex strings."""
        from raspibot.utils.helpers import generate_correlation_id
        
        # Test multiple generations
        for _ in range(10):
            correlation_id = generate_correlation_id()
            assert len(correlation_id) == 8
            assert correlation_id.isalnum()  # Should be alphanumeric
            # UUID hex can be mixed case, so we'll just check it's valid hex
            assert all(c in '0123456789abcdefABCDEF' for c in correlation_id)

    def test_correlation_id_uniqueness(self):
        """Test that generated correlation IDs are unique."""
        from raspibot.utils.helpers import generate_correlation_id
        
        # Generate multiple IDs and check uniqueness
        ids = set()
        for _ in range(100):
            correlation_id = generate_correlation_id()
            assert correlation_id not in ids
            ids.add(correlation_id)


class TestFileSystemUtilities:
    """Test file system utility functions."""

    def test_ensure_directory_exists(self):
        """Test that ensure_directory_exists creates directories."""
        from raspibot.utils.helpers import ensure_directory_exists
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test", "nested", "directory")
            
            # Directory should not exist initially
            assert not os.path.exists(test_dir)
            
            # Create directory
            ensure_directory_exists(test_dir)
            
            # Directory should exist now
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)

    def test_ensure_directory_exists_already_exists(self):
        """Test that ensure_directory_exists handles existing directories."""
        from raspibot.utils.helpers import ensure_directory_exists
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory already exists
            assert os.path.exists(temp_dir)
            
            # Should not raise an error
            ensure_directory_exists(temp_dir)
            
            # Directory should still exist
            assert os.path.exists(temp_dir)

    def test_check_file_permissions(self):
        """Test file permission checking."""
        from raspibot.utils.helpers import check_file_permissions
        
        with tempfile.NamedTemporaryFile() as temp_file:
            # Should be able to read and write temp file
            assert check_file_permissions(temp_file.name, 'r')
            assert check_file_permissions(temp_file.name, 'w')


class TestMathUtilities:
    """Test mathematical utility functions."""

    def test_angle_conversion_degrees_to_radians(self):
        """Test degrees to radians conversion."""
        from raspibot.utils.helpers import degrees_to_radians
        
        # Test common angles
        assert abs(degrees_to_radians(0) - 0) < 0.001
        assert abs(degrees_to_radians(90) - 1.5708) < 0.001
        assert abs(degrees_to_radians(180) - 3.1416) < 0.001
        assert abs(degrees_to_radians(360) - 6.2832) < 0.001

    def test_angle_conversion_radians_to_degrees(self):
        """Test radians to degrees conversion."""
        from raspibot.utils.helpers import radians_to_degrees
        
        # Test common angles
        assert abs(radians_to_degrees(0) - 0) < 0.1
        assert abs(radians_to_degrees(1.5708) - 90) < 0.1
        assert abs(radians_to_degrees(3.1416) - 180) < 0.1
        assert abs(radians_to_degrees(6.2832) - 360) < 0.1

    def test_clamp_value(self):
        """Test value clamping utility."""
        from raspibot.utils.helpers import clamp
        
        # Test clamping within range
        assert clamp(5, 0, 10) == 5
        
        # Test clamping below minimum
        assert clamp(-5, 0, 10) == 0
        
        # Test clamping above maximum
        assert clamp(15, 0, 10) == 10
        
        # Test edge cases
        assert clamp(0, 0, 10) == 0
        assert clamp(10, 0, 10) == 10


class TestTimingUtilities:
    """Test timing and performance utilities."""

    def test_timer_context_manager(self):
        """Test timer context manager."""
        from raspibot.utils.helpers import Timer
        import time
        
        with Timer() as timer:
            time.sleep(0.01)  # Sleep for 10ms
        
        # Should have recorded some elapsed time
        assert timer.elapsed > 0
        assert timer.elapsed < 1  # Should be less than 1 second

    def test_timer_as_decorator(self):
        """Test timer as a decorator."""
        from raspibot.utils.helpers import timer
        import time
        
        @timer
        def slow_function():
            time.sleep(0.01)
            return "done"
        
        result = slow_function()
        assert result == "done" 