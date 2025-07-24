"""Abstract camera interface for different camera implementations."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class CameraInterface(ABC):
    """Abstract base class for camera implementations."""
    
    @abstractmethod
    def start(self) -> bool:
        """
        Start camera capture.
        
        Returns:
            True if camera started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop camera capture and release resources."""
        pass
    
    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current camera resolution.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        """
        Get current camera FPS.
        
        Returns:
            Current FPS as float
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if camera is available and working.
        
        Returns:
            True if camera is available, False otherwise
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 