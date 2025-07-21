"""Tests for servo interface and factory implementation."""

import pytest
from unittest.mock import Mock, patch

from raspibot.hardware.servo_interface import ServoInterface
from raspibot.hardware.servo_factory import ServoControllerFactory, ServoControllerType
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

    def test_interface_instantiation_fails(self):
        """Test that ServoInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ServoInterface()


class TestServoFactory:
    """Test the servo controller factory."""

    def test_available_controller_types(self):
        """Test getting available controller types."""
        types = ServoControllerFactory.get_available_controller_types()
        assert "pca9685" in types
        assert "gpio" in types
        assert len(types) == 2

    def test_validate_controller_type(self):
        """Test controller type validation."""
        assert ServoControllerFactory.validate_controller_type("pca9685")
        assert ServoControllerFactory.validate_controller_type("gpio")
        assert not ServoControllerFactory.validate_controller_type("invalid")
        assert not ServoControllerFactory.validate_controller_type("")

    def test_create_pca9685_controller(self):
        """Test creating PCA9685 controller."""
        controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
        assert controller.get_controller_type() == "PCA9685"
        assert hasattr(controller, 'set_servo_angle')

    def test_create_gpio_controller(self):
        """Test creating GPIO controller."""
        controller = ServoControllerFactory.create_controller(ServoControllerType.GPIO)
        assert controller.get_controller_type() == "GPIO"
        assert hasattr(controller, 'set_servo_angle')

    def test_create_controller_from_config(self):
        """Test creating controller from string config."""
        controller = ServoControllerFactory.create_controller_from_config("pca9685")
        assert controller.get_controller_type() == "PCA9685"

        controller = ServoControllerFactory.create_controller_from_config("gpio")
        assert controller.get_controller_type() == "GPIO"

    def test_create_controller_invalid_type(self):
        """Test creating controller with invalid type."""
        with pytest.raises(HardwareException):
            ServoControllerFactory.create_controller_from_config("invalid")

    def test_create_controller_from_config_invalid(self):
        """Test creating controller from invalid string config."""
        with pytest.raises(HardwareException):
            ServoControllerFactory.create_controller_from_config("nonexistent")


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