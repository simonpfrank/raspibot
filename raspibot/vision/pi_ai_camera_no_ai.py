"""Pi AI Camera implementation without AI functionality (camera only)."""

import time
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from functools import lru_cache

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from .camera_template import CameraTemplate
from ..config.config import PI_AI_CAMERA_CONFIG
from ..utils.logging_config import setup_logging


class PiAICameraNoAI(CameraTemplate):
    """Pi AI Camera implementation without AI functionality (camera only)."""
    
    def __init__(self, 
                 display_resolution: Optional[Tuple[int, int]] = None,
                 framerate: Optional[int] = None):
        """
        Initialize Pi AI Camera without AI functionality.
        
        Args:
            display_resolution: Display resolution (width, height). If None, uses 1280x720.
            framerate: Camera framerate. If None, uses 30 FPS.
        """
        if not PICAMERA2_AVAILABLE:
            raise ImportError("picamera2 not available. Pi AI camera requires picamera2 library.")
        
        self.logger = setup_logging(__name__)
        
        # Camera configuration - no AI model
        self.display_resolution = display_resolution or (1280, 720)
        self.framerate = framerate or 30
        self.target_resolution = self.display_resolution  # For backward compatibility
        
        # Camera state
        self.picam2 = None
        self.is_running = False
        self.last_metadata = None
        
        # Performance tracking
        self.fps_start_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0.0
        
        # Initialize hardware (without AI)
        self._initialize_hardware()
    
    def _initialize_hardware(self) -> None:
        """Initialize camera hardware without AI functionality."""
        try:
            # Initialize Picamera2 directly (no IMX500)
            self.picam2 = Picamera2()
            
            self.logger.info("Pi AI Camera (no AI) hardware initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Pi AI Camera (no AI) hardware: {e}")
            raise
    
    def start(self) -> bool:
        """
        Start camera capture.
        
        Returns:
            True if camera started successfully, False otherwise
        """
        try:
            if self.picam2 is None:
                self.logger.error("Pi AI Camera (no AI) not initialized")
                return False
            
            self.logger.info("Starting Pi AI Camera (no AI) capture")
            
            # Create preview configuration with display resolution
            config = self.picam2.create_preview_configuration(
                main={"size": self.display_resolution},
                controls={"FrameRate": self.framerate}, 
                buffer_count=12
            )
            
            # Log the actual configuration being applied
            self.logger.info(f"Camera config main size: {config['main']['size']}")
            self.logger.info(f"Display resolution: {self.display_resolution}")
            self.logger.info(f"Framerate: {self.framerate}")
            
            # Start camera (no firmware loading needed)
            self.picam2.start(config, show_preview=True)
            
            # Log actual camera configuration after start
            try:
                actual_config = self.picam2.camera_configuration()
                self.logger.info(f"Actual camera size after start: {actual_config['main']['size']}")
            except Exception as e:
                self.logger.warning(f"Could not get actual camera config: {e}")
            
            self.is_running = True
            self.fps_start_time = time.time()
            self.fps_counter = 0
            
            self.logger.info("Pi AI Camera (no AI) started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting Pi AI Camera (no AI): {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame and metadata
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            
            if frame is not None:
                self._update_fps()
                return frame
            else:
                self.logger.warning("Failed to capture frame from Pi AI Camera (no AI)")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def get_frame_grayscale(self) -> Optional[np.ndarray]:
        """
        Get a single grayscale frame from the camera.
        
        Returns:
            Grayscale frame as numpy array, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame and metadata
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            
            if frame is not None:
                self._update_fps()
                
                # Convert to grayscale
                import cv2
                if len(frame.shape) == 3:
                    # Convert BGRA to grayscale (Pi AI camera outputs BGRA)
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                    return gray_frame
                else:
                    return frame
            else:
                self.logger.warning("Failed to capture grayscale frame from Pi AI Camera (no AI)")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing grayscale frame: {e}")
            return None
    
    def get_detections(self) -> List:
        """
        Get detections (not available in no-AI mode).
        
        Returns:
            Empty list (no AI functionality)
        """
        self.logger.warning("AI detection not available in no-AI mode")
        return []
    
    def set_resolution(self, width: int, height: int) -> None:
        """
        Set camera resolution.
        
        Args:
            width: Frame width
            height: Frame height
        """
        if self.is_running:
            self.logger.warning("Cannot change resolution while camera is running")
            return
        
        self.display_resolution = (width, height)
        self.target_resolution = self.display_resolution
        self.logger.info(f"Resolution set to {width}x{height}")
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current camera resolution.
        
        Returns:
            Current resolution as (width, height)
        """
        if self.picam2 is None:
            return self.display_resolution
        
        try:
            config = self.picam2.camera_configuration()
            return config['main']['size']
        except Exception as e:
            self.logger.warning(f"Could not get camera resolution: {e}")
            return self.display_resolution
    
    def get_fps(self) -> float:
        """
        Get current FPS.
        
        Returns:
            Current FPS
        """
        return self.current_fps
    
    def is_available(self) -> bool:
        """
        Check if camera is available.
        
        Returns:
            True if camera is available
        """
        return self.picam2 is not None and self.is_running
    
    def stop(self) -> None:
        """Stop camera capture."""
        if self.picam2 is not None:
            try:
                self.picam2.stop()
                self.logger.info("Pi AI Camera (no AI) stopped")
            except Exception as e:
                self.logger.error(f"Error stopping camera: {e}")
            finally:
                self.is_running = False
                self.picam2 = None
    
    def shutdown(self) -> None:
        """Shutdown camera (alias for stop)."""
        self.stop()
    
    def _update_fps(self) -> None:
        """Update FPS calculation."""
        self.fps_counter += 1
        current_time = time.time()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information (not available in no-AI mode).
        
        Returns:
            Empty dict (no AI functionality)
        """
        return {"mode": "no_ai", "description": "Pi AI Camera running without AI functionality"}
    
    def get_optimal_detection_frame(self) -> Optional[np.ndarray]:
        """
        Get optimal frame for detection (not available in no-AI mode).
        
        Returns:
            Regular frame (no AI optimization)
        """
        return self.get_frame()
    
    def get_optimal_display_frame(self) -> Optional[np.ndarray]:
        """
        Get optimal frame for display.
        
        Returns:
            Frame optimized for display
        """
        return self.get_frame() 