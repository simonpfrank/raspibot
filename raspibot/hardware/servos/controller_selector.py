"""Simple servo controller selection without enums or complex patterns."""

import logging
from typing import Union, Any

from .servo import PCA9685ServoController, GPIOServoController
from raspibot.exceptions import HardwareException


def get_servo_controller(controller_type: str = "auto", **kwargs: Any) -> Union[PCA9685ServoController, GPIOServoController]:
    """Create a servo controller of the specified type.
    
    Args:
        controller_type: "pca9685", "gpio", or "auto" for automatic selection
        **kwargs: Additional arguments for controller initialization
        
    Returns:
        Servo controller instance
        
    Raises:
        HardwareException: If controller creation fails
    """
    logger = logging.getLogger(__name__)
    controller_type = controller_type.lower()
    
    if controller_type == "auto":
        try:
            logger.info("Attempting PCA9685 controller...")
            controller = PCA9685ServoController(**kwargs)
            logger.info("PCA9685 controller created successfully")
            return controller
        except Exception as e:
            logger.warning(f"PCA9685 not available: {e}")
            logger.info("Falling back to GPIO controller")
            return GPIOServoController(**kwargs)
    
    elif controller_type == "pca9685":
        return PCA9685ServoController(**kwargs)
    
    elif controller_type == "gpio":
        return GPIOServoController(**kwargs)
    
    else:
        raise HardwareException(f"Unknown controller type: {controller_type}. Use 'pca9685', 'gpio', or 'auto'")


def is_pca9685_available() -> bool:
    """Check if PCA9685 controller is available."""
    try:
        controller = PCA9685ServoController()
        controller.shutdown()
        return True
    except Exception:
        return False


def get_recommended_controller_type() -> str:
    """Get recommended controller type."""
    return "pca9685" if is_pca9685_available() else "gpio"