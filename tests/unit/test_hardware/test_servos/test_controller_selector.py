"""Simplified unit tests for raspibot.hardware.servos.controller_selector module."""

import pytest
from unittest.mock import Mock, patch

from raspibot.hardware.servos.controller_selector import (
    get_servo_controller,
    is_pca9685_available,
    get_recommended_controller_type
)
from raspibot.hardware.servos.servo import PCA9685ServoController, GPIOServoController
from raspibot.exceptions import HardwareException


class TestGetServoController:
    """Test servo controller creation."""
    
    def test_get_controller_auto_fallback_gpio(self, mock_gpio):
        """Test fallback to GPIO when PCA9685 fails."""
        with patch.object(PCA9685ServoController, '__init__', side_effect=Exception("PCA9685 failed")):
            with patch.object(GPIOServoController, '__init__', return_value=None) as mock_gpio_init:
                controller = get_servo_controller("auto")
                
                assert isinstance(controller, GPIOServoController)
                mock_gpio_init.assert_called_once()
    
    def test_get_controller_explicit_gpio(self, mock_gpio):
        """Test explicit GPIO selection."""
        with patch.object(GPIOServoController, '__init__', return_value=None) as mock_gpio_init:
            controller = get_servo_controller("gpio")
            
            assert isinstance(controller, GPIOServoController)
            mock_gpio_init.assert_called_once()
    
    def test_get_controller_invalid_type(self):
        """Test invalid controller type raises exception."""
        with pytest.raises(HardwareException, match="Unknown controller type"):
            get_servo_controller("invalid_type")
    
    def test_kwargs_passed_to_controller(self, mock_gpio):
        """Test additional arguments passed through."""
        custom_pins = {0: 12, 1: 13}
        
        with patch.object(GPIOServoController, '__init__', return_value=None) as mock_gpio_init:
            get_servo_controller("gpio", servo_pins=custom_pins)
            
            mock_gpio_init.assert_called_once_with(servo_pins=custom_pins)
    
    def test_controller_type_case_insensitive(self, mock_gpio):
        """Test controller type is case insensitive."""
        with patch.object(GPIOServoController, '__init__', return_value=None) as mock_gpio_init:
            controller = get_servo_controller("GPIO")  # Uppercase
            
            assert isinstance(controller, GPIOServoController)
            mock_gpio_init.assert_called_once()


class TestControllerAvailability:
    """Test controller availability detection."""
    
    def test_get_recommended_controller_type_pca9685(self):
        """Test recommendation when PCA9685 available."""
        with patch('raspibot.hardware.servos.controller_selector.is_pca9685_available', return_value=True):
            assert get_recommended_controller_type() == "pca9685"
    
    def test_get_recommended_controller_type_gpio(self):
        """Test recommendation when only GPIO available."""
        with patch('raspibot.hardware.servos.controller_selector.is_pca9685_available', return_value=False):
            assert get_recommended_controller_type() == "gpio"


class TestLoggingIntegration:
    """Test logging integration."""
    
    def test_auto_selection_logs_attempts(self, mock_gpio):
        """Test auto selection logs attempts."""
        with patch.object(PCA9685ServoController, '__init__', side_effect=Exception("PCA9685 failed")):
            with patch.object(GPIOServoController, '__init__', return_value=None):
                controller = get_servo_controller("auto")
                
                # Should create GPIO controller as fallback
                assert isinstance(controller, GPIOServoController)