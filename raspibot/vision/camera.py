"""Simple camera class for OpenCV webcam capture."""

import cv2
import numpy as np
import time
from typing import Optional, Tuple

from ..config.hardware_config import CAMERA_DEFAULT_WIDTH, CAMERA_DEFAULT_HEIGHT, CAMERA_DEVICE_ID
from ..utils.logging_config import setup_logging
from .camera_interface import CameraInterface


class Camera(CameraInterface):
    """Simple camera class - start with webcam, easy to extend later."""
    
    def __init__(self, device_id: int = CAMERA_DEVICE_ID, 
                 width: int = CAMERA_DEFAULT_WIDTH, 
                 height: int = CAMERA_DEFAULT_HEIGHT):
        """
        Initialize camera with specified parameters.
        
        Args:
            device_id: Camera device ID (default from config)
            width: Camera width in pixels
            height: Camera height in pixels
        """
        self.device_id = device_id
        self.width = width
        self.height = height
        self.cap = None
        self.is_running = False
        self.logger = setup_logging(__name__)
        
        # FPS tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
    
    def start(self) -> bool:
        """
        Start camera capture.
        
        Returns:
            True if camera started successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting camera device {self.device_id} at {self.width}x{self.height}")
            
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera device {self.device_id}")
                self.cap.release()
                self.cap = None
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Verify actual resolution
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width != self.width or actual_height != self.height:
                self.logger.warning(f"Requested {self.width}x{self.height}, got {actual_width}x{actual_height}")
                self.width = actual_width
                self.height = actual_height
            
            self.is_running = True
            self.fps_start_time = time.time()
            self.fps_counter = 0
            
            self.logger.info(f"Camera started successfully at {self.width}x{self.height}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting camera: {e}")
            if self.cap:
                self.cap.release()
                self.cap = None
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        if not self.is_running or self.cap is None:
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret:
                self._update_fps()
                return frame
            else:
                self.logger.warning("Failed to read frame from camera")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current camera resolution.
        
        Returns:
            Tuple of (width, height)
        """
        return (self.width, self.height)
    
    def get_fps(self) -> float:
        """
        Get current FPS.
        
        Returns:
            Current FPS as float
        """
        return self.current_fps
    
    def is_available(self) -> bool:
        """
        Check if camera is available and running.
        
        Returns:
            True if camera is available
        """
        return self.is_running and self.cap is not None and self.cap.isOpened()
    
    def stop(self) -> None:
        """Stop camera capture and release resources."""
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            
            self.is_running = False
            self.logger.info("Camera stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping camera: {e}")
    
    def _update_fps(self) -> None:
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:  # Update FPS every second
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def __enter__(self):
        """Context manager entry."""
        if not self.start():
            raise RuntimeError("Failed to start camera")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 