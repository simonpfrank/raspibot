"""Simple camera selection for different camera implementations."""

from typing import Union
from enum import Enum

from .camera_interface import CameraInterface
from .camera import Camera
from .basic_camera import BasicCamera
from .pi_ai_camera import PiAICamera
from .usb_camera import USBCam
from ..utils.logging_config import setup_logging


class CameraType(Enum):
    """Available camera types."""
    WEBCAM = "webcam"
    BASIC = "basic"
    PI_AI = "pi_ai"
    USB = "usb"
    AUTO = "auto"


def get_camera(camera_type: Union[CameraType, str] = CameraType.AUTO, **kwargs) -> CameraInterface:
    """
    Create a camera instance based on the specified type.
    
    Args:
        camera_type: Type of camera to create (webcam, pi_ai, or auto)
        **kwargs: Additional arguments passed to camera constructor
        
    Returns:
        CameraInterface instance
        
    Raises:
        ValueError: If camera type is invalid
        ImportError: If Pi AI camera is requested but not available
    """
    logger = setup_logging(__name__)
    
    # Convert string to enum if needed
    if isinstance(camera_type, str):
        try:
            camera_type = CameraType(camera_type.lower())
        except ValueError:
            raise ValueError(f"Invalid camera type: {camera_type}. "
                           f"Valid types: {[t.value for t in CameraType]}")
    
    if camera_type == CameraType.AUTO:
        # Try Pi camera first, then USB camera, then basic webcam
        try:
            logger.info("Attempting to create Pi AI camera...")
            camera = PiAICamera(**kwargs)
            logger.info("Pi AI camera created successfully")
            return camera
        except (ImportError, Exception) as e:
            logger.warning(f"Pi AI camera not available: {e}")
            
            try:
                logger.info("Attempting to create BasicCamera (Pi camera)...")
                camera = BasicCamera(**kwargs)
                logger.info("BasicCamera created successfully")
                return camera
            except (ImportError, Exception) as e:
                logger.warning(f"BasicCamera not available: {e}")
                
                try:
                    logger.info("Attempting to create USB camera...")
                    camera = USBCam(**kwargs)
                    logger.info("USB camera created successfully")
                    return camera
                except Exception as e:
                    logger.warning(f"USB camera not available: {e}")
                    logger.info("Falling back to basic webcam")
                    return Camera(**kwargs)
    
    elif camera_type == CameraType.BASIC:
        return BasicCamera(**kwargs)
    
    elif camera_type == CameraType.PI_AI:
        return PiAICamera(**kwargs)
    
    elif camera_type == CameraType.WEBCAM:
        return Camera(**kwargs)
    
    elif camera_type == CameraType.USB:
        return USBCam(**kwargs)
    
    else:
        raise ValueError(f"Unknown camera type: {camera_type}")


def is_pi_ai_available() -> bool:
    """
    Check if Pi AI camera is available.
    
    Returns:
        True if Pi AI camera can be created, False otherwise
    """
    try:
        # Try to create a Pi AI camera instance
        camera = PiAICamera()
        camera.stop()  # Clean up
        return True
    except Exception:
        return False


def get_available_cameras() -> list[CameraType]:
    """
    Get list of available camera types.
    
    Returns:
        List of available camera types
    """
    available = [CameraType.WEBCAM]  # Basic webcam is always available
    
    # Check for USB camera availability
    try:
        camera = USBCam()
        camera.shutdown()
        available.append(CameraType.USB)
    except Exception:
        pass
    
    # Check for BasicCamera availability (Pi camera)
    try:
        camera = BasicCamera()
        camera.shutdown()
        available.append(CameraType.BASIC)
    except Exception:
        pass
    
    if is_pi_ai_available():
        available.append(CameraType.PI_AI)
    
    return available


def get_recommended_camera() -> CameraType:
    """
    Get the recommended camera type based on availability.
    
    Returns:
        Recommended camera type
    """
    available = get_available_cameras()
    
    # Prefer Pi AI camera for AI operations
    if CameraType.PI_AI in available:
        return CameraType.PI_AI
    
    # Prefer BasicCamera for general use (Pi camera, supports all resolutions)
    if CameraType.BASIC in available:
        return CameraType.BASIC
    
    # Prefer USB camera over basic webcam (better detection and capabilities)
    if CameraType.USB in available:
        return CameraType.USB
    
    # Fall back to basic webcam
    return CameraType.WEBCAM


def get_camera_for_ai() -> CameraInterface:
    """
    Get camera specifically for AI operations.
    
    Returns:
        Camera instance suitable for AI operations
    """
    logger = setup_logging(__name__)
    
    try:
        logger.info("Creating Pi AI camera for AI operations...")
        return PiAICamera()
    except Exception as e:
        logger.warning(f"Pi AI camera not available: {e}")
        logger.info("Using BasicCamera for AI operations...")
        camera = BasicCamera()
        camera.set_resolution(640, 480)  # AI-friendly resolution
        return camera 