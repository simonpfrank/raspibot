"""Simple camera template for different camera implementations, avoiding
the abstract base classes."""

from typing import Optional, Tuple
import numpy as np


class CameraTemplate:
    """Simple base class for camera implementations.
    
    This provides a common interface without the complexity of abstract base classes.
    Subclasses should implement all methods or they will raise NotImplementedError.
    """
    
    def start(self) -> bool:
        """
        Start camera capture.
        
        Returns:
            True if camera started successfully, False otherwise
        """
        raise NotImplementedError("Subclass must implement start()")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        raise NotImplementedError("Subclass must implement get_frame()")
    
    def shutdown(self) -> None:
        """Stop camera capture and release resources."""
        raise NotImplementedError("Subclass must implement stop()")
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current camera resolution.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        raise NotImplementedError("Subclass must implement get_resolution()")
    
    def get_fps(self) -> float:
        """
        Get current camera FPS.
        
        Returns:
            Current FPS as float
        """
        raise NotImplementedError("Subclass must implement get_fps()")
    
    def is_available(self) -> bool:
        """
        Check if camera is available and working.
        
        Returns:
            True if camera is available, False otherwise
        """
        raise NotImplementedError("Subclass must implement is_available()")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown() 