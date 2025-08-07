"""
Simplified USB Camera using Picamera2 instead of complex OpenCV detection.
"""

import time
from typing import Optional, Tuple
import numpy as np

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from raspibot.utils.logging_config import setup_logging


class USBCamera:
    """Simplified USB Camera using Picamera2 for unified interface."""
    
    def __init__(self, camera_num: Optional[int] = None, width: int = 1280, height: int = 720):
        """
        Initialize USB camera using Picamera2.
        
        Args:
            camera_num: Specific camera number (if None, find first USB camera)
            width: Target width
            height: Target height
        """
        if not PICAMERA2_AVAILABLE:
            raise ImportError("picamera2 not available")
        
        self.logger = setup_logging(__name__)
        self.camera_num = camera_num
        self.target_width = width
        self.target_height = height
        
        self.camera: Optional[Picamera2] = None
        self.is_running = False
        self.current_fps = 0.0
        
        # FPS tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        self.logger.info("Initializing USB Camera with Picamera2")
        self._find_usb_camera()
    
    def _find_usb_camera(self) -> None:
        """Find USB camera using Picamera2.global_camera_info()."""
        camera_info = Picamera2.global_camera_info()
        
        usb_cameras = []
        for i, info in enumerate(camera_info):
            # USB cameras typically have UVC in model name or USB in ID
            model = info.get('Model', '').lower()
            camera_id = info.get('Id', '').lower()
            
            # Check for USB camera indicators
            if ('uvc' in model or 'usb' in camera_id or 
                any(vid in camera_id for vid in ['046d', '0bda', '1bcf', '0ac8'])):
                usb_cameras.append((i, info))
        
        if not usb_cameras:
            raise RuntimeError("No USB cameras found via Picamera2")
        
        # Use specified camera number or first USB camera found
        if self.camera_num is not None:
            # Verify specified camera exists and is USB
            for num, info in usb_cameras:
                if num == self.camera_num:
                    self.camera_num = num
                    self.logger.info(f"Using specified USB camera {num}: {info.get('Model', 'Unknown')}")
                    return
            raise RuntimeError(f"Camera {self.camera_num} is not a USB camera")
        else:
            # Use first USB camera found
            self.camera_num, camera_info = usb_cameras[0]
            self.logger.info(f"Auto-selected USB camera {self.camera_num}: {camera_info.get('Model', 'Unknown')}")
    
    def start(self) -> bool:
        """Start the USB camera."""
        try:
            self.logger.info(f"Starting USB camera {self.camera_num} with Picamera2")
            
            self.camera = Picamera2(self.camera_num)
            
            # Configure for RGB output (convert to BGR later for OpenCV compatibility)
            config = self.camera.create_preview_configuration(
                main={"size": (self.target_width, self.target_height), "format": "RGB888"},
                buffer_count=4
            )
            self.camera.configure(config)
            self.camera.start()
            
            self.is_running = True
            self.fps_start_time = time.time()
            self.fps_counter = 0
            
            self.logger.info(f"USB camera started at {self.target_width}x{self.target_height}")
            return True
            
        except Exception as e:
            self.logger.error(f"USBCamera.start failed: {type(e).__name__}: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get a frame from the camera."""
        if not self.is_running or self.camera is None:
            return None
        
        try:
            # Capture RGB frame and convert to BGR for OpenCV compatibility
            frame = self.camera.capture_array("main")
            if frame is not None:
                import cv2
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                self._update_fps()
                return frame_bgr
            else:
                self.logger.warning("Failed to capture frame")
                return None
                
        except Exception as e:
            self.logger.error(f"USBCamera.get_frame failed: {type(e).__name__}: {e}")
            return None
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get current camera resolution."""
        return (self.target_width, self.target_height)
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.current_fps
    
    def is_available(self) -> bool:
        """Check if camera is available."""
        return self.is_running and self.camera is not None
    
    def shutdown(self) -> None:
        """Stop camera capture and release resources."""
        try:
            if self.camera is not None:
                if self.is_running:
                    self.camera.stop()
                self.camera.close()
                self.camera = None
            
            self.is_running = False
            self.logger.info("USB camera stopped")
            
        except Exception as e:
            self.logger.error(f"USBCamera.shutdown failed: {type(e).__name__}: {e}")
    
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
            raise RuntimeError("Failed to start USB camera")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()