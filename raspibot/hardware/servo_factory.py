"""Servo controller factory for creating different types of servo controllers.

This module provides a factory pattern for creating servo controllers,
allowing easy switching between different hardware implementations.
"""

from enum import Enum
from typing import Optional, Dict, Any

from raspibot.hardware.servo_interface import ServoInterface
from raspibot.hardware.servo_controller import PCA9685ServoController, GPIOServoController
from raspibot.exceptions import HardwareException


class ServoControllerType(Enum):
    """Enumeration of available servo controller types."""
    PCA9685 = "pca9685"
    GPIO = "gpio"


class ServoControllerFactory:
    """Factory for creating servo controller instances."""
    
    @staticmethod
    def create_controller(
        controller_type: ServoControllerType,
        **kwargs: Any
    ) -> ServoInterface:
        """Create a servo controller of the specified type.
        
        Args:
            controller_type: Type of controller to create
            **kwargs: Additional arguments for controller initialization
            
        Returns:
            Servo controller instance
            
        Raises:
            HardwareException: If controller type is invalid or creation fails
        """
        try:
            if controller_type == ServoControllerType.PCA9685:
                return PCA9685ServoController(**kwargs)
            elif controller_type == ServoControllerType.GPIO:
                return GPIOServoController(**kwargs)
            else:
                raise HardwareException(f"Unknown controller type: {controller_type}")
                
        except Exception as e:
            raise HardwareException(f"Failed to create {controller_type.value} controller: {e}")
    
    @staticmethod
    def create_controller_from_config(
        controller_type_str: str,
        **kwargs: Any
    ) -> ServoInterface:
        """Create a servo controller from string configuration.
        
        Args:
            controller_type_str: Controller type as string ("pca9685" or "gpio")
            **kwargs: Additional arguments for controller initialization
            
        Returns:
            Servo controller instance
            
        Raises:
            HardwareException: If controller type is invalid or creation fails
        """
        try:
            controller_type = ServoControllerType(controller_type_str.lower())
            return ServoControllerFactory.create_controller(controller_type, **kwargs)
        except ValueError:
            raise HardwareException(f"Invalid controller type: {controller_type_str}")
    
    @staticmethod
    def get_available_controller_types() -> list[str]:
        """Get list of available controller types.
        
        Returns:
            List of available controller type strings
        """
        return [controller_type.value for controller_type in ServoControllerType]
    
    @staticmethod
    def validate_controller_type(controller_type_str: str) -> bool:
        """Validate if a controller type string is supported.
        
        Args:
            controller_type_str: Controller type string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ServoControllerType(controller_type_str.lower())
            return True
        except ValueError:
            return False 