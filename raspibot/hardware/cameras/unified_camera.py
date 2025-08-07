"""
Unified camera interface using Picamera2 for all camera types.
Eliminates template classes and complex detection logic.
"""

from enum import Enum
from typing import Union, Optional

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from raspibot.utils.logging_config import setup_logging


class CameraType(Enum):
    """Available camera types."""
    PI = "pi"
    PI_AI = "pi_ai"
    USB = "usb"
    AUTO = "auto"


def get_available_cameras() -> list[dict]:
    """Get list of available cameras using Picamera2."""
    if not PICAMERA2_AVAILABLE:
        return []
    
    return Picamera2.global_camera_info()


def identify_camera_type(camera_info: dict) -> CameraType:
    """Identify camera type from Picamera2 camera info."""
    model = camera_info.get('Model', '').lower()
    camera_id = camera_info.get('Id', '').lower()
    
    if 'imx500' in model:
        return CameraType.PI_AI
    elif 'uvc' in model or 'usb' in camera_id or any(vid in camera_id for vid in ['046d', '0bda', '1bcf']):
        return CameraType.USB
    else:
        return CameraType.PI  # Default Pi camera


def get_camera_by_type(camera_type: CameraType, **kwargs):
    """Get camera instance by type using existing implementations."""
    logger = setup_logging(__name__)
    
    if camera_type == CameraType.PI_AI:
        from .pi_ai_camera import PiAICamera
        return PiAICamera(**kwargs)
    elif camera_type == CameraType.PI:
        from .pi_camera import PiCamera
        return PiCamera(**kwargs)
    elif camera_type == CameraType.USB:
        from .usb_camera import USBCamera
        return USBCamera(**kwargs)
    else:
        raise ValueError(f"Unknown camera type: {camera_type}")


def create_camera(camera_type: Union[CameraType, str] = CameraType.AUTO, **kwargs):
    """
    Create a camera instance - simplified factory function.
    
    Args:
        camera_type: Type of camera to create or "auto" for best available
        **kwargs: Arguments passed to camera constructor
        
    Returns:
        Camera instance (no template inheritance)
        
    Raises:
        RuntimeError: If no cameras available or specified type not found
    """
    logger = setup_logging(__name__)
    
    # Convert string to enum
    if isinstance(camera_type, str):
        try:
            camera_type = CameraType(camera_type.lower())
        except ValueError:
            raise ValueError(f"Invalid camera type: {camera_type}")
    
    if camera_type == CameraType.AUTO:
        logger.info("Auto-selecting best available camera")
        
        # Get available cameras
        available = get_available_cameras()
        if not available:
            raise RuntimeError("No cameras detected")
        
        # Try cameras in priority order: PI_AI -> PI -> USB
        priority_order = [CameraType.PI_AI, CameraType.PI, CameraType.USB]
        
        for cam_info in available:
            detected_type = identify_camera_type(cam_info)
            if detected_type in priority_order:
                logger.info(f"Auto-selected {detected_type.value} camera: {cam_info.get('Model', 'Unknown')}")
                # Pass camera number to constructor with appropriate parameter name
                camera_num = cam_info['Num']
                if detected_type == CameraType.PI_AI:
                    return get_camera_by_type(detected_type, camera_device_id=camera_num, **kwargs)
                else:
                    return get_camera_by_type(detected_type, camera_num=camera_num, **kwargs)
        
        raise RuntimeError("No suitable cameras found")
    
    else:
        # Create specific camera type
        logger.info(f"Creating {camera_type.value} camera")
        return get_camera_by_type(camera_type, **kwargs)


def list_cameras() -> None:
    """List all available cameras with their types."""
    logger = setup_logging(__name__)
    
    try:
        cameras = get_available_cameras()
        if not cameras:
            logger.info("No cameras detected")
            return
        
        logger.info("Available cameras:")
        for i, info in enumerate(cameras):
            cam_type = identify_camera_type(info)
            model = info.get('Model', 'Unknown')
            logger.info(f"  {i}: {cam_type.value} - {model}")
            
    except Exception as e:
        logger.error(f"Error listing cameras: {type(e).__name__}: {e}")


# For backward compatibility, export the main functions
__all__ = ['create_camera', 'CameraType', 'get_available_cameras', 'list_cameras']