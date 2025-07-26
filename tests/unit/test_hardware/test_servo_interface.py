"""Tests for servo interface and factory implementation."""

import pytest
from unittest.mock import Mock, patch

from raspibot.hardware.servo_interface import ServoInterface
from raspibot.hardware.servo_selector import (
    get_servo_controller, ServoControllerType, 
    get_available_controllers, is_pca9685_available
)
from raspibot.exceptions import HardwareException


class TestServoInterface:
    """Test the abstract servo interface."""

    def test_interface_contract(self):
        """Test that interface defines all required methods."""
        # Check that all abstract methods are defined
        assert hasattr(ServoInterface, 'set_servo_angle')
        assert hasattr(ServoInterface, 'get_servo_angle')
        assert hasattr(ServoInterface, 'smooth_move_to_angle')
        assert hasattr(ServoInterface, 'emergency_stop')
        assert hasattr(ServoInterface, 'set_calibration_offset')
        assert hasattr(ServoInterface, 'get_calibration_offset')
        assert hasattr(ServoInterface, 'shutdown')
        assert hasattr(ServoInterface, 'get_controller_type')
        assert hasattr(ServoInterface, 'get_available_channels')

    def test_interface_instantiation_raises_not_implemented(self):
        """Test that ServoInterface raises NotImplementedError when methods are called."""
        interface = ServoInterface()
        
        with pytest.raises(NotImplementedError):
            interface.set_servo_angle(0, 90)
        
        with pytest.raises(NotImplementedError):
            interface.get_servo_angle(0)
        
        with pytest.raises(NotImplementedError):
            interface.smooth_move_to_angle(0, 90)
        
        with pytest.raises(NotImplementedError):
            interface.emergency_stop()


class TestServoSelector:
    """Test the servo controller selector functions."""

    def test_available_controller_types(self):
        """Test getting available controller types."""
        types = get_available_controllers()
        assert len(types) >= 1  # At least GPIO should be available
        assert ServoControllerType.GPIO in types

    def test_pca9685_availability_check(self):
        """Test PCA9685 availability check."""
        available = is_pca9685_available()
        assert isinstance(available, bool)  # Should return bool, True or False

    def test_create_pca9685_controller(self):
        """Test creating PCA9685 controller."""
        controller = get_servo_controller(ServoControllerType.PCA9685)
        assert controller.get_controller_type() == "PCA9685"
        assert hasattr(controller, 'set_servo_angle')

    def test_create_gpio_controller(self):
        """Test creating GPIO controller."""
        controller = get_servo_controller(ServoControllerType.GPIO)
        assert controller.get_controller_type() == "GPIO"
        assert hasattr(controller, 'set_servo_angle')

    def test_create_controller_from_string(self):
        """Test creating controller from string config."""
        controller = get_servo_controller("pca9685")
        assert controller.get_controller_type() == "PCA9685"

        controller = get_servo_controller("gpio")
        assert controller.get_controller_type() == "GPIO"

    def test_auto_controller_selection(self):
        """Test auto controller selection."""
        controller = get_servo_controller(ServoControllerType.AUTO)
        assert controller.get_controller_type() in ["PCA9685", "GPIO"]

    def test_create_controller_invalid_type(self):
        """Test creating controller with invalid type."""
        with pytest.raises(HardwareException):
            get_servo_controller("invalid")

    def test_create_controller_invalid_enum(self):
        """Test creating controller with invalid enum."""
        with pytest.raises(HardwareException):
            get_servo_controller("nonexistent")


class TestServoControllerImplementation:
    """Test that controllers properly implement the interface."""

    def test_pca9685_implements_interface(self):
        """Test that PCA9685 controller implements ServoInterface."""
        from raspibot.hardware.servo_controller import PCA9685ServoController
        
        # Check inheritance
        assert issubclass(PCA9685ServoController, ServoInterface)
        
        # Test interface methods
        controller = PCA9685ServoController(i2c_bus=999)  # Simulation mode
        assert controller.get_controller_type() == "PCA9685"
        assert isinstance(controller.get_available_channels(), list)

    def test_gpio_implements_interface(self):
        """Test that GPIO controller implements ServoInterface."""
        from raspibot.hardware.servo_controller import GPIOServoController
        
        # Check inheritance
        assert issubclass(GPIOServoController, ServoInterface)
        
        # Test interface methods
        controller = GPIOServoController()
        assert controller.get_controller_type() == "GPIO"
        assert isinstance(controller.get_available_channels(), list)

    def test_interface_methods_work(self):
        """Test that interface methods work on both controllers."""
        from raspibot.hardware.servo_controller import PCA9685ServoController, GPIOServoController
        
        # Test PCA9685
        pca_controller = PCA9685ServoController(i2c_bus=999)
        pca_controller.set_servo_angle(0, 90)
        assert pca_controller.get_servo_angle(0) == 90
        pca_controller.set_calibration_offset(0, 5.0)
        assert pca_controller.get_calibration_offset(0) == 5.0
        
        # Test GPIO
        gpio_controller = GPIOServoController()
        gpio_controller.set_servo_angle(0, 90)
        assert gpio_controller.get_servo_angle(0) == 90
        gpio_controller.set_calibration_offset(0, 5.0)
        assert gpio_controller.get_calibration_offset(0) == 5.0 