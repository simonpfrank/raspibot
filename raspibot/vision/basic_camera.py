"""
Basic camera implementation for non-AI operations.

This module provides a BasicCamera class that supports full resolution control
without AI constraints, suitable for high-resolution captures and variable
resolution video recording.
"""

import time
from typing import Tuple, Optional, Dict, Any
import numpy as np

from picamera2 import Picamera2, Preview
from libcamera import Transform, ColorSpace

from .camera_interface import CameraInterface
from ..utils.logging_config import setup_logging


class BasicCamera(CameraInterface):
    """
    Basic camera implementation for non-AI operations.
    
    This camera supports:
    - Full resolution control (not constrained by AI models)
    - Multiple format support (RGB, YUV420, etc.)
    - High resolution captures
    - Variable resolution video recording
    - Grayscale mode for maximum resolution
    """
    
    def __init__(self, camera_num: int = 0, camera_mode: str = "normal_video"):
        """
        Initialize BasicCamera.
        
        Args:
            camera_num: Camera device number (default: 0)
            camera_mode: Camera mode ("normal_video", "opencv_detection")
        """
        self.logger = setup_logging(__name__)
        self.camera_num = camera_num
        self.picam2: Optional[Picamera2] = None
        self.is_running = False
        
        # Camera mode configuration
        self.camera_mode = camera_mode
        if camera_mode == "opencv_detection":
            self.current_resolution = (1280, 720)  # OpenCV detection resolution
            self.current_format = "XBGR8888"
            self.current_mode = "grayscale"  # Will convert to grayscale for detection
        else:
            # Normal video mode
            self.current_resolution = (1280, 720)  # Normal video resolution
            self.current_format = "XBGR8888"
            self.current_mode = "color"
        
        # FPS tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        
        self.logger.info(f"Initializing BasicCamera for device {camera_num} in {camera_mode} mode")
        self._initialize_camera()
    
    def _initialize_camera(self) -> None:
        """Initialize the camera hardware."""
        try:
            self.picam2 = Picamera2(self.camera_num)
            self.logger.info("BasicCamera initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize BasicCamera: {e}")
            raise
    
    def start(self) -> bool:
        """
        Start the camera.
        
        Returns:
            True if camera started successfully, False otherwise
        """
        if self.picam2 is None:
            self.logger.error("Camera not initialized")
            return False
        
        try:
            self.logger.info(f"Starting BasicCamera at {self.current_resolution} in {self.current_mode} mode")
            
            # Create configuration based on current settings
            config = self._create_configuration()
            self.picam2.configure(config)
            self.picam2.start()
            
            self.is_running = True
            self.fps_start_time = time.time()
            self.fps_counter = 0
            
            self.logger.info("BasicCamera started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting BasicCamera: {e}")
            return False
    
    def _create_configuration(self) -> Dict[str, Any]:
        """
        Create picamera2 configuration based on current settings.
        
        Returns:
            Configuration dictionary
        """
        main_config = {
            "size": self.current_resolution,
            "format": self.current_format
        }
        
        # For grayscale mode, we can use higher resolutions
        if self.current_mode == "grayscale":
            # Use a raw format for grayscale to get maximum resolution
            main_config["format"] = "YUV420"  # Y channel will be our grayscale
        
        config = self.picam2.create_preview_configuration(
            main=main_config,
            buffer_count=4  # More buffers for smoother operation
        )
        
        return config
    
    def set_resolution(self, width: int, height: int) -> None:
        """
        Set camera resolution.
        
        Args:
            width: Width in pixels
            height: Height in pixels
        """
        if self.is_running:
            self.logger.warning("Cannot change resolution while camera is running")
            return
        
        # Validate resolution based on mode
        max_width, max_height = self._get_max_resolution()
        
        if width > max_width or height > max_height:
            self.logger.warning(f"Resolution {width}x{height} exceeds maximum {max_width}x{max_height} for {self.current_mode} mode")
            width = min(width, max_width)
            height = min(height, max_height)
        
        self.current_resolution = (width, height)
        self.logger.info(f"Resolution set to {width}x{height}")
    
    def _get_max_resolution(self) -> Tuple[int, int]:
        """
        Get maximum resolution for current mode.
        
        Returns:
            Tuple of (max_width, max_height)
        """
        if self.current_mode == "grayscale":
            # Grayscale mode can support higher resolutions
            return (4056, 3040)  # IMX477 max resolution
        else:
            # Color mode typical limits
            return (2028, 1520)  # Safe color resolution
    
    def set_mode(self, mode: str) -> None:
        """
        Set camera mode.
        
        Args:
            mode: Camera mode ("color" or "grayscale")
        """
        if self.is_running:
            self.logger.warning("Cannot change mode while camera is running")
            return
        
        if mode not in ["color", "grayscale"]:
            self.logger.error(f"Invalid mode: {mode}. Must be 'color' or 'grayscale'")
            return
        
        self.current_mode = mode
        
        # Update format based on mode
        if mode == "grayscale":
            self.current_format = "YUV420"
        else:
            self.current_format = "RGB888"
        
        # Adjust resolution if it exceeds new mode limits
        max_width, max_height = self._get_max_resolution()
        current_width, current_height = self.current_resolution
        
        if current_width > max_width or current_height > max_height:
            new_width = min(current_width, max_width)
            new_height = min(current_height, max_height)
            self.current_resolution = (new_width, new_height)
            self.logger.info(f"Resolution adjusted to {new_width}x{new_height} for {mode} mode")
        
        self.logger.info(f"Camera mode set to {mode}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a frame from the camera in BGR format for display.
        
        Returns:
            Frame as numpy array in BGR format, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame
            frame = self.picam2.capture_array("main")
            
            if frame is not None:
                import cv2
                
                # Convert to BGR format for display based on camera mode
                if self.camera_mode == "opencv_detection":
                    # OpenCV detection mode: convert XBGR8888 to BGR
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    # Normal video mode: convert XBGR8888 to BGR
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                self._update_fps()
                return frame
            else:
                self.logger.warning("Failed to capture frame")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None

    def get_detection_frame(self) -> Optional[np.ndarray]:
        """
        Get a frame in the appropriate format for detection.
        
        Returns:
            Frame in detection format (grayscale for OpenCV), or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame
            frame = self.picam2.capture_array("main")
            
            if frame is not None:
                import cv2
                
                # Convert to detection format based on camera mode
                if self.camera_mode == "opencv_detection":
                    # Convert to grayscale for OpenCV detection
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                    else:
                        frame = frame
                else:
                    # Normal video mode: return BGR for general use
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                self._update_fps()
                return frame
            else:
                self.logger.warning("Failed to capture detection frame")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing detection frame: {e}")
            return None
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current resolution.
        
        Returns:
            Tuple of (width, height)
        """
        return self.current_resolution
    
    def get_mode(self) -> str:
        """
        Get current camera mode.
        
        Returns:
            Current mode ("color" or "grayscale")
        """
        return self.current_mode
    
    def get_fps(self) -> float:
        """
        Get current FPS.
        
        Returns:
            Current FPS as float
        """
        return self.current_fps
    
    def is_available(self) -> bool:
        """
        Check if camera is available.
        
        Returns:
            True if camera is available
        """
        return self.picam2 is not None
    
    def stop(self) -> None:
        """Stop the camera."""
        try:
            if self.picam2 is not None and self.is_running:
                self.picam2.stop()
                self.is_running = False
                self.logger.info("BasicCamera stopped")
        except Exception as e:
            self.logger.error(f"Error stopping BasicCamera: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the camera completely."""
        try:
            self.stop()
            if self.picam2 is not None:
                self.picam2.close()
                self.picam2 = None
                self.logger.info("BasicCamera shutdown")
        except Exception as e:
            self.logger.error(f"Error shutting down BasicCamera: {e}")
    
    def cleanup(self) -> None:
        """Cleanup camera resources."""
        self.shutdown()
    
    def _update_fps(self) -> None:
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:  # Update FPS every second
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    # Additional convenience methods
    
    def capture_image(self, filename: str) -> bool:
        """
        Capture a still image to file.
        
        Args:
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_running or self.picam2 is None:
            self.logger.error("Camera not running")
            return False
        
        try:
            self.picam2.capture_file(filename)
            self.logger.info(f"Image captured to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error capturing image: {e}")
            return False
    
    def get_available_resolutions(self) -> list[Tuple[int, int]]:
        """
        Get list of commonly supported resolutions for current mode.
        
        Returns:
            List of (width, height) tuples
        """
        if self.current_mode == "grayscale":
            return [
                (640, 480),
                (1280, 720),
                (1920, 1080),
                (2028, 1520),
                (3280, 2464),
                (4056, 3040),  # Maximum for IMX477
            ]
        else:
            return [
                (640, 480),
                (800, 600),
                (1024, 768),
                (1280, 720),
                (1640, 1232),
                (1920, 1080),
                (2028, 1520),  # Safe maximum for color
            ]

    def get_camera_mode_info(self) -> Dict[str, Any]:
        """
        Get information about the current camera mode.
        
        Returns:
            Dictionary with camera mode information
        """
        return {
            "camera_mode": self.camera_mode,
            "detection": {
                "resolution": self.current_resolution,
                "format": self.current_format,
                "purpose": "OpenCV face detection" if self.camera_mode == "opencv_detection" else "General video capture"
            },
            "display": {
                "resolution": self.current_resolution,
                "format": "BGR",
                "purpose": "Color display for user interface"
            },
            "memory_mb_per_frame": 3.52 if self.camera_mode == "normal_video" else 0.88  # Grayscale is more efficient
        } 