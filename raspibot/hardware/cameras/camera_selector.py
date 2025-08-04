"""Simple camera selection for different camera implementations."""

from typing import Union
from enum import Enum

from .camera_template import CameraTemplate
from .usb_camera import USBCamera
from .pi_camera import PiCamera
from .pi_ai_camera import PiAICamera
from raspibot.utils.logging_config import setup_logging


class CameraType(Enum):
    """Available camera types."""
    WEBCAM = "usb"
    PI = "pi"
    PI_AI = "pi_ai"
    USB = "usb"
    AUTO = "auto"

logger = setup_logging(__name__)

def get_camera(camera_type: Union[CameraType, str] = CameraType.AUTO, **kwargs) -> CameraTemplate:
    """
    Create a camera instance based on the specified type.
    
    Args:
        camera_type: Type of camera to create (webcam, pi_ai, or auto)
        **kwargs: Additional arguments passed to camera constructor
        
    Returns:
        CameraTemplate instance
        
    Raises:
        ValueError: If camera type is invalid
        ImportError: If Pi AI camera is requested but not available
    """

    
    # Convert string to enum if needed
    if isinstance(camera_type, str):
        try:
            camera_type = CameraType(camera_type.lower())
        except ValueError:
            raise ValueError(f"Invalid camera type: {camera_type}. "
                           f"Valid types: {[t.value for t in CameraType]}")
    
    if camera_type == CameraType.AUTO:
        logger.info("Choosing best available camera type")
        camera_type = get_best_available_camera()
    
    if camera_type == CameraType.PI:
        logger.info("Creating PiCamera")
        return PiCamera(**kwargs)
    
    elif camera_type == CameraType.PI_AI:
        logger.info("Creating PiAICamera")
        return PiAICamera(**kwargs)

    elif camera_type == CameraType.USB:
        logger.info("Creating USBCamera")
        return USBCamera(**kwargs)
    
    else:
        raise ValueError(f"Unknown camera type: {camera_type}")



def get_available_cameras() -> list[CameraType]:
    """
    Get list of available camera types.
    
    Returns:
        List of available camera types
    """
    logger.info("Checking for available cameras")
    available = []  
    
    # Check for USB camera availability
    try:
        camera = USBCamera()
        camera.shutdown()
        available.append(CameraType.USB)
    except Exception:
        pass
    
    # Check for PiCamera availability (Pi camera)
    try:
        camera = PiCamera()
        camera.shutdown()
        available.append(CameraType.PI)
    except Exception:
        pass
    
    try:
        camera = PiAICamera()
        camera.shutdown()
        available.append(CameraType.PI_AI)
    except Exception:
        pass
    
    return available


def get_best_available_camera() -> CameraType:
    """
    Get the recommended camera type based on availability.
    
    Returns:
        Recommended camera type
    """
    available = get_available_cameras()
    
    # Prefer Pi AI camera for AI operations
    if CameraType.PI_AI in available:
        return CameraType.PI_AI
    
    # Prefer PiCamera for general use (Pi camera, supports all resolutions)
    elif CameraType.PI in available:
        return CameraType.PI
    
    # Prefer USB camera over basic webcam (better detection and capabilities)
    elif CameraType.USB in available:
        return CameraType.USB
    
    else:
        raise ValueError("No camera available")

