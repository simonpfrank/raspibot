"""Unit tests for raspibot.settings.config module."""

import pytest
import os
from unittest.mock import patch

from raspibot.settings import config


class TestEnvironmentVariables:
    """Test environment variable parsing."""
    
    def test_debug_setting_true(self):
        """Test DEBUG environment variable parsing."""
        with patch.dict(os.environ, {'RASPIBOT_DEBUG': 'true'}):
            # Need to reload module to get new environment values
            import importlib
            importlib.reload(config)
            assert config.DEBUG is True
    
    def test_debug_setting_false(self):
        """Test DEBUG default/false values."""
        with patch.dict(os.environ, {'RASPIBOT_DEBUG': 'false'}, clear=True):
            import importlib
            importlib.reload(config)
            assert config.DEBUG is False
        
        # Test default (no env var)
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            assert config.DEBUG is False
    
    def test_log_level_setting(self):
        """Test LOG_LEVEL environment variable."""
        with patch.dict(os.environ, {'RASPIBOT_LOG_LEVEL': 'DEBUG'}):
            import importlib
            importlib.reload(config)
            assert config.LOG_LEVEL == 'DEBUG'
        
        # Test default
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            assert config.LOG_LEVEL == 'INFO'
    
    def test_log_to_file_setting(self):
        """Test LOG_TO_FILE environment variable."""
        with patch.dict(os.environ, {'RASPIBOT_LOG_TO_FILE': 'false'}):
            import importlib
            importlib.reload(config)
            assert config.LOG_TO_FILE is False
        
        # Test default
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            assert config.LOG_TO_FILE is True
    
    def test_log_stacktrace_setting(self):
        """Test LOG_STACKTRACE environment variable."""
        with patch.dict(os.environ, {'RASPIBOT_LOG_STACKTRACE': 'true'}):
            import importlib
            importlib.reload(config)
            assert config.LOG_STACKTRACE is True
        
        # Test default
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            assert config.LOG_STACKTRACE is False
    
    def test_log_file_path_setting(self):
        """Test LOG_FILE_PATH environment variable."""
        custom_path = "/custom/path/log.txt"
        with patch.dict(os.environ, {'RASPIBOT_LOG_FILE_PATH': custom_path}):
            import importlib
            importlib.reload(config)
            assert config.LOG_FILE_PATH == custom_path
        
        # Test default
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            importlib.reload(config)
            assert config.LOG_FILE_PATH == "data/logs/raspibot.log"


class TestHardwareConfiguration:
    """Test hardware configuration constants."""
    
    def test_servo_angle_constants(self):
        """Test servo angle min/max/default values."""
        assert config.SERVO_MIN_ANGLE == 0
        assert config.SERVO_MAX_ANGLE == 180
        assert config.SERVO_DEFAULT_ANGLE == 90
        
        # Validate logical relationships
        assert config.SERVO_MIN_ANGLE < config.SERVO_DEFAULT_ANGLE < config.SERVO_MAX_ANGLE
    
    def test_servo_channel_constants(self):
        """Test servo channel assignments."""
        assert config.SERVO_PAN_CHANNEL == 0
        assert config.SERVO_TILT_CHANNEL == 1
        assert config.SERVO_CHANNELS == [0, 1]
        
        # Ensure channels are in the list
        assert config.SERVO_PAN_CHANNEL in config.SERVO_CHANNELS
        assert config.SERVO_TILT_CHANNEL in config.SERVO_CHANNELS
    
    def test_servo_pulse_width_constants(self):
        """Test calibrated pulse width values."""
        # Pan servo calibration
        assert config.SERVO_PAN_0_PULSE == 0.4
        assert config.SERVO_PAN_90_PULSE == 1.47
        assert config.SERVO_PAN_180_PULSE == 2.52
        
        # Tilt servo calibration
        assert config.SERVO_TILT_0_PULSE == 0.4
        assert config.SERVO_TILT_90_PULSE == 1.4  # Actual value from config
        assert config.SERVO_TILT_180_PULSE == 2.47
        
        # Validate logical ordering
        assert config.SERVO_PAN_0_PULSE < config.SERVO_PAN_90_PULSE < config.SERVO_PAN_180_PULSE
        assert config.SERVO_TILT_0_PULSE < config.SERVO_TILT_90_PULSE < config.SERVO_TILT_180_PULSE
    
    def test_i2c_configuration(self):
        """Test I2C bus and address constants."""
        assert config.I2C_BUS == 1
        assert config.PCA9685_ADDRESS == 0x40
        
        # Validate reasonable values
        assert 0 <= config.I2C_BUS <= 1  # RPi typically has I2C0 and I2C1
        assert 0x00 <= config.PCA9685_ADDRESS <= 0x7F  # Valid I2C address range
    
    def test_camera_configuration(self):
        """Test camera-related constants."""
        assert config.PI_DISPLAY_MODE == "connect"
        assert config.PI_CAMERA_DEVICE_ID is None
        
        # Font configuration
        assert hasattr(config, 'DEFAULT_SCREEN_FONT')
        assert hasattr(config, 'DEFAULT_SCREEN_FONT_SIZE')
        assert hasattr(config, 'DEFAULT_SCREEN_FONT_COLOUR')
        assert hasattr(config, 'DEFAULT_SCREEN_FONT_THIKCNESS')  # Note: keeping original typo
        
        # Validate font size is positive
        assert config.DEFAULT_SCREEN_FONT_SIZE > 0
        
        # Validate color is RGB tuple
        assert len(config.DEFAULT_SCREEN_FONT_COLOUR) == 3
        assert all(0 <= c <= 255 for c in config.DEFAULT_SCREEN_FONT_COLOUR)
    
    def test_servo_center_positions(self):
        """Test servo center position constants."""
        assert hasattr(config, 'SERVO_PAN_CENTER')
        assert hasattr(config, 'SERVO_TILT_CENTER')
        
        # Center positions should be within valid angle range
        assert config.SERVO_MIN_ANGLE <= config.SERVO_PAN_CENTER <= config.SERVO_MAX_ANGLE
        assert config.SERVO_MIN_ANGLE <= config.SERVO_TILT_CENTER <= config.SERVO_MAX_ANGLE
    
    def test_servo_range_limits(self):
        """Test servo range limit constants."""
        assert hasattr(config, 'SERVO_PAN_MIN_ANGLE')
        assert hasattr(config, 'SERVO_PAN_MAX_ANGLE')
        assert hasattr(config, 'SERVO_TILT_MIN_ANGLE')
        assert hasattr(config, 'SERVO_TILT_MAX_ANGLE')
        
        # Range limits should be within global limits
        assert config.SERVO_MIN_ANGLE <= config.SERVO_PAN_MIN_ANGLE <= config.SERVO_PAN_MAX_ANGLE <= config.SERVO_MAX_ANGLE
        assert config.SERVO_MIN_ANGLE <= config.SERVO_TILT_MIN_ANGLE <= config.SERVO_TILT_MAX_ANGLE <= config.SERVO_MAX_ANGLE