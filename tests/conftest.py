"""Pytest configuration and shared fixtures for Raspibot tests."""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any


@pytest.fixture
def temp_directory():
    """Create a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_environment():
    """Provide a clean environment variable setup."""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_servo_controller():
    """Mock servo controller for testing."""
    controller = Mock()
    controller.set_servo_angle = Mock()
    controller.get_servo_angle = Mock(return_value=90.0)
    controller.initialize = Mock()
    controller.shutdown = Mock()
    controller.smooth_move_to_angle = Mock()
    controller.set_calibration_offset = Mock()
    return controller


@pytest.fixture
def mock_camera():
    """Mock camera for testing."""
    camera = Mock()
    camera.start = Mock(return_value=True)
    camera.stop = Mock()
    camera.process = Mock()
    camera.tracked_objects = []
    camera.clear_tracked_objects = Mock()
    camera._running = True
    return camera


@pytest.fixture
def mock_adafruit_libs():
    """Mock Adafruit CircuitPython libraries."""
    # Create mock modules
    mock_board = Mock()
    mock_board.SCL = 'SCL'
    mock_board.SDA = 'SDA'
    
    mock_busio = Mock()
    mock_i2c = Mock()
    mock_busio.I2C.return_value = mock_i2c
    
    mock_pca9685_module = Mock()
    mock_pca_instance = Mock()
    mock_pca9685_module.PCA9685.return_value = mock_pca_instance
    mock_pca_instance.frequency = 50
    
    mock_servo_module = Mock()
    mock_servo_instance = Mock()
    mock_servo_module.Servo.return_value = mock_servo_instance
    mock_servo_instance.angle = 90
    
    # Mock the modules at system level AND in servo module namespace
    with patch.dict('sys.modules', {
        'board': mock_board,
        'busio': mock_busio, 
        'adafruit_pca9685': mock_pca9685_module,
        'adafruit_motor': Mock(),
        'adafruit_motor.servo': mock_servo_module
    }):
        with patch('raspibot.hardware.servos.servo.ADAFRUIT_AVAILABLE', True):
            with patch('raspibot.hardware.servos.servo.board', mock_board):
                with patch('raspibot.hardware.servos.servo.busio', mock_busio):
                    with patch('raspibot.hardware.servos.servo.PCA9685', mock_pca9685_module.PCA9685):
                        with patch('raspibot.hardware.servos.servo.servo', mock_servo_module):
                            yield {
                                'board': mock_board,
                                'busio': mock_busio,
                                'pca': mock_pca9685_module.PCA9685,
                                'servo': mock_servo_module,
                                'i2c': mock_i2c,
                                'pca_instance': mock_pca_instance,
                                'servo_instance': mock_servo_instance
                            }


@pytest.fixture
def mock_gpio():
    """Mock RPi.GPIO library."""
    with patch.dict('sys.modules', {'RPi': Mock(), 'RPi.GPIO': Mock()}):
        mock_gpio_module = Mock()
        mock_gpio_module.BCM = 'BCM'
        mock_gpio_module.OUT = 'OUT'
        mock_gpio_module.setup = Mock()
        mock_gpio_module.setmode = Mock()
        mock_gpio_module.PWM = Mock()
        mock_gpio_module.cleanup = Mock()
        
        mock_pwm_instance = Mock()
        mock_pwm_instance.start = Mock()
        mock_pwm_instance.ChangeDutyCycle = Mock()
        mock_pwm_instance.stop = Mock()
        mock_gpio_module.PWM.return_value = mock_pwm_instance
        
        import sys
        sys.modules['RPi.GPIO'] = mock_gpio_module
        
        yield {
            'gpio': mock_gpio_module,
            'pwm_instance': mock_pwm_instance
        }


@pytest.fixture
def mock_picamera2():
    """Mock Picamera2 library."""
    with patch('raspibot.hardware.cameras.camera.PICAMERA2_AVAILABLE', True):
        with patch('raspibot.hardware.cameras.camera.Picamera2') as mock_picamera2:
            with patch('raspibot.hardware.cameras.camera.Preview') as mock_preview:
                with patch('raspibot.hardware.cameras.camera.MappedArray') as mock_mapped_array:
                    mock_instance = Mock()
                    mock_picamera2.return_value = mock_instance
                    mock_picamera2.global_camera_info.return_value = [
                        {'Model': 'imx500', 'Num': 0},
                        {'Model': 'imx708', 'Num': 1}
                    ]
                    
                    yield {
                        'picamera2': mock_picamera2,
                        'preview': mock_preview,
                        'mapped_array': mock_mapped_array,
                        'instance': mock_instance
                    }


@pytest.fixture
def sample_detections():
    """Sample detection data for testing."""
    return [
        {
            "label": "person",
            "confidence": 0.85,
            "box": (100, 100, 50, 100),
            "pan_angle": 45.0,
            "world_angle": 45.0,
            "position_index": 0,
            "timestamp": 1234567890.0
        },
        {
            "label": "person", 
            "confidence": 0.75,
            "box": (110, 110, 55, 105),
            "pan_angle": 50.0,
            "world_angle": 50.0,
            "position_index": 1,
            "timestamp": 1234567891.0
        },
        {
            "label": "chair",
            "confidence": 0.65,
            "box": (200, 150, 80, 120),
            "pan_angle": 90.0,
            "world_angle": 90.0,
            "position_index": 2,
            "timestamp": 1234567892.0
        }
    ]


@pytest.fixture
def mock_logging():
    """Mock logging to capture log output."""
    with patch('raspibot.utils.logging_config.logging') as mock_log:
        mock_logger = Mock()
        mock_log.getLogger.return_value = mock_logger
        yield mock_logger


# Test markers
pytest_mark_unit = pytest.mark.unit
pytest_mark_servo = pytest.mark.servo  
pytest_mark_camera = pytest.mark.camera
pytest_mark_async = pytest.mark.asyncio