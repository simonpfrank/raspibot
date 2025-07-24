"""Camera factory for selecting between different camera implementations."""

from typing import Optional, Union
from enum import Enum

from .camera_interface import CameraInterface
from .camera import Camera
from .pi_ai_camera import PiAICamera
from ..utils.logging_config import setup_logging


class CameraType(Enum):
    """Available camera types."""
    WEBCAM = "webcam"
    PI_AI = "pi_ai"
    AUTO = "auto"


class CameraFactory:
    """Factory for creating camera instances."""
    
    @staticmethod
    def create_camera(camera_type: Union[CameraType, str] = CameraType.AUTO,
                     **kwargs) -> CameraInterface:
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
            # Try Pi AI camera first, fall back to webcam
            try:
                logger.info("Attempting to create Pi AI camera...")
                camera = PiAICamera(**kwargs)
                logger.info("Pi AI camera created successfully")
                return camera
            except (ImportError, Exception) as e:
                logger.warning(f"Pi AI camera not available: {e}")
                logger.info("Falling back to webcam")
                return Camera(**kwargs)
        
        elif camera_type == CameraType.PI_AI:
            return PiAICamera(**kwargs)
        
        elif camera_type == CameraType.WEBCAM:
            return Camera(**kwargs)
        
        else:
            raise ValueError(f"Unknown camera type: {camera_type}")
    
    @staticmethod
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
    
    @staticmethod
    def get_available_cameras() -> list[CameraType]:
        """
        Get list of available camera types.
        
        Returns:
            List of available camera types
        """
        available = [CameraType.WEBCAM]  # Webcam is always available
        
        if CameraFactory.is_pi_ai_available():
            available.append(CameraType.PI_AI)
        
        return available
    
    @staticmethod
    def get_recommended_camera() -> CameraType:
        """
        Get the recommended camera type based on availability.
        
        Returns:
            Recommended camera type
        """
        if CameraFactory.is_pi_ai_available():
            return CameraType.PI_AI
        else:
            return CameraType.WEBCAM 