"""Servo controller selector for creating different types of servo controllers.

This module provides functions for creating servo controllers,
allowing easy switching between different hardware implementations.
"""

from enum import Enum
from typing import Union, Any, List

from raspibot.hardware.servo_interface import ServoInterface
from raspibot.hardware.servo_controller import PCA9685ServoController, GPIOServoController
from raspibot.exceptions import HardwareException
from raspibot.utils.logging_config import setup_logging


class ServoControllerType(Enum):
    """Enumeration of available servo controller types."""
    PCA9685 = "pca9685"
    GPIO = "gpio"
    AUTO = "auto"


def get_servo_controller(
    controller_type: Union[ServoControllerType, str] = ServoControllerType.AUTO,
    **kwargs: Any
) -> ServoInterface:
    """Create a servo controller of the specified type.
    
    Args:
        controller_type: Type of controller to create or "auto" for automatic selection
        **kwargs: Additional arguments for controller initialization
        
    Returns:
        Servo controller instance
        
    Raises:
        HardwareException: If controller type is invalid or creation fails
    """
    logger = setup_logging(__name__)
    
    # Convert string to enum if needed
    if isinstance(controller_type, str):
        try:
            controller_type = ServoControllerType(controller_type.lower())
        except ValueError:
            raise HardwareException(f"Invalid controller type: {controller_type}. "
                                  f"Valid types: {[t.value for t in ServoControllerType]}")
    
    if controller_type == ServoControllerType.AUTO:
        # Try PCA9685 first, fall back to GPIO
        try:
            logger.info("Attempting to create PCA9685 servo controller...")
            controller = PCA9685ServoController(**kwargs)
            logger.info("PCA9685 servo controller created successfully")
            return controller
        except Exception as e:
            logger.warning(f"PCA9685 controller not available: {e}")
            logger.info("Falling back to GPIO servo controller")
            return GPIOServoController(**kwargs)
    
    elif controller_type == ServoControllerType.PCA9685:
        return PCA9685ServoController(**kwargs)
    
    elif controller_type == ServoControllerType.GPIO:
        return GPIOServoController(**kwargs)
    
    else:
        raise HardwareException(f"Unknown controller type: {controller_type}")


def is_pca9685_available() -> bool:
    """Check if PCA9685 servo controller is available.
    
    Returns:
        True if PCA9685 is available, False otherwise
    """
    try:
        # Try to create a PCA9685 controller without raising exceptions
        PCA9685ServoController()
        return True
    except Exception:
        return False


def get_available_controllers() -> List[ServoControllerType]:
    """Get list of available servo controller types.
    
    Returns:
        List of available controller types
    """
    available = []
    
    # Check PCA9685
    if is_pca9685_available():
        available.append(ServoControllerType.PCA9685)
    
    # GPIO is always available on Pi
    available.append(ServoControllerType.GPIO)
    
    return available


def get_recommended_controller() -> ServoControllerType:
    """Get recommended servo controller type based on availability.
    
    Returns:
        Recommended controller type
    """
    if is_pca9685_available():
        return ServoControllerType.PCA9685
    else:
        return ServoControllerType.GPIO
 