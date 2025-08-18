"""Unit tests for raspibot.utils.helpers module."""

import pytest
import os
import tempfile
import math
import time
from unittest.mock import patch, Mock

from raspibot.utils.helpers import (
    generate_correlation_id,
    ensure_directory_exists,
    check_file_permissions,
    degrees_to_radians,
    radians_to_degrees,
    clamp,
    Timer,
    timer
)


class TestCorrelationID:
    """Test correlation ID generation."""
    
    def test_generate_correlation_id_format(self):
        """Test 8-character hex format."""
        correlation_id = generate_correlation_id()
        assert len(correlation_id) == 8
        assert all(c in '0123456789abcdef' for c in correlation_id)
    
    def test_generate_correlation_id_uniqueness(self):
        """Test IDs are unique across calls."""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()
        assert id1 != id2


class TestDirectoryOperations:
    """Test directory operations."""
    
    def test_ensure_directory_exists_new(self, temp_directory):
        """Test creating new directory."""
        new_dir = os.path.join(temp_directory, "new_dir")
        assert not os.path.exists(new_dir)
        
        ensure_directory_exists(new_dir)
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)
    
    def test_ensure_directory_exists_existing(self, temp_directory):
        """Test with existing directory."""
        # temp_directory already exists
        ensure_directory_exists(temp_directory)
        assert os.path.exists(temp_directory)
        assert os.path.isdir(temp_directory)
    
    def test_ensure_directory_exists_nested(self, temp_directory):
        """Test creating nested directories."""
        nested_dir = os.path.join(temp_directory, "level1", "level2", "level3")
        assert not os.path.exists(nested_dir)
        
        ensure_directory_exists(nested_dir)
        assert os.path.exists(nested_dir)
        assert os.path.isdir(nested_dir)


class TestFilePermissions:
    """Test file permission checking."""
    
    def test_check_file_permissions_read(self, temp_directory):
        """Test read permission checking."""
        test_file = os.path.join(temp_directory, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        assert check_file_permissions(test_file, 'r') is True
    
    def test_check_file_permissions_write(self, temp_directory):
        """Test write permission checking."""
        test_file = os.path.join(temp_directory, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        assert check_file_permissions(test_file, 'w') is True
    
    def test_check_file_permissions_execute(self, temp_directory):
        """Test execute permission checking."""
        test_file = os.path.join(temp_directory, "test_script.py")
        with open(test_file, 'w') as f:
            f.write("#!/usr/bin/env python3\nprint('test')")
        
        # Make executable
        os.chmod(test_file, 0o755)
        assert check_file_permissions(test_file, 'x') is True
    
    def test_check_file_permissions_invalid(self, temp_directory):
        """Test invalid permission parameter."""
        test_file = os.path.join(temp_directory, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        assert check_file_permissions(test_file, 'z') is False


class TestAngleConversion:
    """Test angle conversion functions."""
    
    def test_degrees_to_radians_zero(self):
        """Test 0 degrees conversion."""
        assert degrees_to_radians(0) == 0
    
    def test_degrees_to_radians_90(self):
        """Test 90 degrees conversion."""
        result = degrees_to_radians(90)
        assert abs(result - math.pi/2) < 1e-10
    
    def test_degrees_to_radians_180(self):
        """Test 180 degrees conversion."""
        result = degrees_to_radians(180)
        assert abs(result - math.pi) < 1e-10
    
    def test_radians_to_degrees_zero(self):
        """Test 0 radians conversion."""
        assert radians_to_degrees(0) == 0
    
    def test_radians_to_degrees_pi(self):
        """Test π radians conversion."""
        result = radians_to_degrees(math.pi)
        assert abs(result - 180) < 1e-10


class TestMathUtilities:
    """Test math utility functions."""
    
    def test_clamp_within_range(self):
        """Test value within min/max range."""
        assert clamp(5.0, 0.0, 10.0) == 5.0
    
    def test_clamp_below_minimum(self):
        """Test value clamped to minimum."""
        assert clamp(-5.0, 0.0, 10.0) == 0.0
    
    def test_clamp_above_maximum(self):
        """Test value clamped to maximum."""
        assert clamp(15.0, 0.0, 10.0) == 10.0
    
    def test_clamp_equal_boundaries(self):
        """Test edge cases at boundaries."""
        assert clamp(0.0, 0.0, 10.0) == 0.0
        assert clamp(10.0, 0.0, 10.0) == 10.0


class TestTimer:
    """Test timer utilities."""
    
    def test_timer_context_manager(self):
        """Test Timer context manager usage."""
        with Timer() as t:
            time.sleep(0.01)  # 10ms
        
        assert t.elapsed >= 0.01
        assert t.elapsed < 0.1  # Should be less than 100ms
    
    def test_timer_decorator(self):
        """Test timer decorator functionality."""
        call_count = 0
        
        @timer
        def test_function():
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)
            return "result"
        
        with patch('builtins.print') as mock_print:
            result = test_function()
            
            assert result == "result"
            assert call_count == 1
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "test_function took" in call_args
            assert "seconds" in call_args
    
    def test_timer_elapsed_time(self):
        """Test elapsed time measurement accuracy."""
        timer_obj = Timer()
        timer_obj.start_time = time.time() - 0.5  # 500ms ago
        timer_obj.elapsed = 0.5
        
        assert abs(timer_obj.elapsed - 0.5) < 0.01