"""Tests for simplified PCA9685 servo controller using Adafruit libraries.

This module tests the simplified servo controller with proper mocking
for safe development and testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from raspibot.exceptions import HardwareException


class TestSimplePCA9685ServoController:
    """Test the simplified PCA9685 servo controller using Adafruit libraries."""

    def test_initialization_success(self):
        """Test PCA9685 controller initialization with Adafruit libraries."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock the PCA9685 instance
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            # Mock I2C bus
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            # Mock servo instances
            mock_pan_servo = Mock()
            mock_tilt_servo = Mock()
            mock_servo_class.side_effect = [mock_pan_servo, mock_tilt_servo]
            
            # Create controller
            controller = SimplePCA9685ServoController(i2c_bus=1, address=0x40)
            
            # Verify initialization
            assert controller.pca == mock_pca_instance
            assert controller.pca.frequency == 50
            assert 0 in controller.servos
            assert 1 in controller.servos
    
    def test_initialization_adafruit_not_available(self):
        """Test PCA9685 controller initialization when Adafruit libraries are not available."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('raspibot.hardware.servo_controller.ADAFRUIT_AVAILABLE', False):
            with pytest.raises(HardwareException, match="Adafruit libraries not available"):
                SimplePCA9685ServoController()
    
    def test_servo_angle_validation(self):
        """Test servo angle validation (0-180 degrees)."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test valid angles
            controller.set_servo_angle(0, 0)    # Should work
            controller.set_servo_angle(0, 90)   # Should work
            controller.set_servo_angle(0, 180)  # Should work
            
            # Test invalid angles
            with pytest.raises(HardwareException, match="Invalid angle"):
                controller.set_servo_angle(0, -10)
            
            with pytest.raises(HardwareException, match="Invalid angle"):
                controller.set_servo_angle(0, 400)

    def test_channel_validation(self):
        """Test servo channel validation."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test valid channels (0 and 1 are created by default)
            controller.set_servo_angle(0, 90)   # Should work
            controller.set_servo_angle(1, 90)   # Should work
            
            # Test invalid channels
            with pytest.raises(HardwareException, match="Invalid channel"):
                controller.set_servo_angle(2, 90)  # Channel 2 doesn't exist

    def test_set_servo_angle(self):
        """Test setting servo angle."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test setting angle
            controller.set_servo_angle(0, 90)
            
            # Verify servo angle was set
            assert mock_servo.angle == 90
            assert controller.current_angles[0] == 90

    def test_get_servo_angle(self):
        """Test getting current servo angle."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Set an angle and verify we can get it back
            controller.set_servo_angle(0, 90)
            angle = controller.get_servo_angle(0)
            assert angle == 90
            
            # Test getting angle for unset channel
            angle = controller.get_servo_angle(1)
            assert angle == 90  # Default angle

    def test_calibration_offset(self):
        """Test servo calibration offset handling."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Set calibration offset
            controller.set_calibration_offset(0, 5.0)  # 5 degree offset
            
            # Verify offset is stored
            offset = controller.get_calibration_offset(0)
            assert offset == 5.0
            
            # Test angle with offset
            controller.set_servo_angle(0, 90)
            
            # Verify angle is set with offset applied
            assert mock_servo.angle == 95  # 90 + 5 offset
            assert controller.current_angles[0] == 90  # Original angle stored

    def test_smooth_movement(self):
        """Test smooth movement between angles."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class, \
             patch('time.sleep') as mock_sleep:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test smooth movement
            controller.smooth_move_to_angle(0, 90, speed=1.0)
            
            # Verify servo angle was set multiple times (smooth movement)
            assert mock_servo.angle == 90
            assert controller.current_angles[0] == 90
            assert mock_sleep.called  # Should have delays between steps

    def test_emergency_stop(self):
        """Test emergency stop functionality."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test emergency stop doesn't crash
            controller.emergency_stop()
            # Emergency stop just maintains current position, no hardware calls

    def test_controller_type(self):
        """Test controller type identification."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test controller type
            assert controller.get_controller_type() == "Simple PCA9685 (Adafruit)"

    def test_available_channels(self):
        """Test available channels list."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test available channels
            channels = controller.get_available_channels()
            assert channels == [0, 1]  # Pan and tilt servos

    def test_shutdown(self):
        """Test controller shutdown."""
        from raspibot.hardware.servo_controller import SimplePCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            controller = SimplePCA9685ServoController()
            
            # Test shutdown doesn't crash
            controller.shutdown()
            # Shutdown just maintains current position, no hardware calls


class TestLegacyPCA9685ServoController:
    """Test the legacy PCA9685 servo controller for backward compatibility."""

    def test_legacy_compatibility(self):
        """Test that legacy PCA9685ServoController still works."""
        from raspibot.hardware.servo_controller import PCA9685ServoController
        
        with patch('adafruit_pca9685.PCA9685') as mock_pca, \
             patch('board.SCL') as mock_scl, \
             patch('board.SDA') as mock_sda, \
             patch('busio.I2C') as mock_i2c_class, \
             patch('adafruit_motor.servo.Servo') as mock_servo_class:
            
            # Mock setup
            mock_pca_instance = Mock()
            mock_pca.return_value = mock_pca_instance
            
            mock_i2c = Mock()
            mock_i2c_class.return_value = mock_i2c
            
            mock_servo = Mock()
            mock_servo_class.return_value = mock_servo
            
            # Test legacy controller still works
            controller = PCA9685ServoController()
            
            # Test basic functionality
            controller.set_servo_angle(0, 90)
            assert controller.get_servo_angle(0) == 90
            assert controller.get_controller_type() == "Simple PCA9685 (Adafruit)"


class TestGPIOServoController:
    """Test the GPIO servo controller."""

    def test_gpio_initialization_success(self):
        """Test GPIO controller initialization with RPi.GPIO available."""
        from raspibot.hardware.servo_controller import GPIOServoController
        
        with patch('RPi.GPIO') as mock_gpio:
            controller = GPIOServoController()
            
            # Verify GPIO was initialized
            assert hasattr(controller, 'gpio')
            assert controller.gpio == mock_gpio

    def test_gpio_initialization_failure(self):
        """Test GPIO controller initialization when RPi.GPIO is not available."""
        from raspibot.hardware.servo_controller import GPIOServoController
        
        with patch('RPi.GPIO', side_effect=ImportError("No module named 'RPi'")):
            controller = GPIOServoController()
            
            # Should still work in simulation mode
            assert not hasattr(controller, 'gpio')
            controller.set_servo_angle(0, 90)  # Should not crash

    def test_gpio_servo_angle_validation(self):
        """Test GPIO servo angle validation."""
        from raspibot.hardware.servo_controller import GPIOServoController
        
        with patch('RPi.GPIO') as mock_gpio:
            controller = GPIOServoController()
            
            # Test valid angles
            controller.set_servo_angle(0, 0)    # Should work
            controller.set_servo_angle(0, 90)   # Should work
            controller.set_servo_angle(0, 180)  # Should work
            
            # Test invalid angles
            with pytest.raises(HardwareException, match="Invalid angle"):
                controller.set_servo_angle(0, -10)
            
            with pytest.raises(HardwareException, match="Invalid angle"):
                controller.set_servo_angle(0, 400)

    def test_gpio_channel_validation(self):
        """Test GPIO servo channel validation."""
        from raspibot.hardware.servo_controller import GPIOServoController
        
        with patch('RPi.GPIO') as mock_gpio:
            controller = GPIOServoController()
            
            # Test valid channels (0 and 1 are default)
            controller.set_servo_angle(0, 90)   # Should work
            controller.set_servo_angle(1, 90)   # Should work
            
            # Test invalid channels
            with pytest.raises(HardwareException, match="Invalid channel"):
                controller.set_servo_angle(2, 90)  # Channel 2 doesn't exist

    def test_gpio_emergency_stop(self):
        """Test GPIO emergency stop functionality."""
        from raspibot.hardware.servo_controller import GPIOServoController
        
        with patch('RPi.GPIO') as mock_gpio:
            controller = GPIOServoController()
            
            # Test emergency stop
            controller.emergency_stop()
            
            # Verify GPIO outputs were set to False
            assert mock_gpio.output.called

    def test_gpio_shutdown(self):
        """Test GPIO controller shutdown."""
        from raspibot.hardware.servo_controller import GPIOServoController
        
        with patch('RPi.GPIO') as mock_gpio:
            controller = GPIOServoController()
            
            # Test shutdown
            controller.shutdown()
            
            # Verify GPIO cleanup was called
            assert mock_gpio.cleanup.called 