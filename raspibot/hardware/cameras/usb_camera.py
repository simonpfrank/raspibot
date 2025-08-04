"""
USB Camera implementation with automatic detection and capability discovery.

This module provides a USBCam class that automatically detects available USB webcams
and their capabilities, providing a robust fallback when Pi cameras are not available.
"""

import cv2
import subprocess
import os
import re
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np

from .camera_template import CameraTemplate
from raspibot.utils.logging_config import setup_logging


@dataclass
class WebcamInfo:
    """Information about a detected webcam."""
    device_path: str
    device_number: int
    name: str
    driver: str
    capabilities: List[str]
    supported_resolutions: List[Tuple[int, int]]
    supported_formats: List[str]
    max_fps: float
    is_working: bool


class WebcamDetector:
    """Detect and analyze available webcams."""
    
    def __init__(self):
        self.detected_webcams: List[WebcamInfo] = []
    
    def detect_video_devices(self) -> List[str]:
        """Find all video devices in /dev/video*."""
        video_devices = []
        
        try:
            # Use glob to find video devices
            import glob
            all_video_devices = glob.glob('/dev/video*')
            
            # Filter to only include devices that are likely to be cameras
            # Skip very high device numbers (likely virtual devices)
            for device_path in all_video_devices:
                try:
                    device_number = int(device_path.split('video')[-1])
                    # Only include devices 0-15 (reasonable range for physical cameras)
                    if device_number <= 15:
                        video_devices.append(device_path)
                except ValueError:
                    continue
            
            # If no devices found, try the fallback method
            if not video_devices:
                # Check for specific video device numbers
                for i in range(10):  # Check video0 through video9
                    device_path = f'/dev/video{i}'
                    if os.path.exists(device_path):
                        video_devices.append(device_path)
            
        except Exception as e:
            print(f"Error finding video devices: {e}")
        
        return sorted(video_devices)
    
    def get_device_info(self, device_path: str) -> Dict[str, str]:
        """Get device information using v4l2-ctl."""
        info = {}
        
        try:
            result = subprocess.run(['v4l2-ctl', '--device', device_path, '--info'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
            
        except FileNotFoundError:
            # v4l2-ctl not available, continue without detailed info
            pass
        except Exception as e:
            print(f"Error getting device info for {device_path}: {e}")
        
        return info
    
    def test_opencv_access(self, device_number: int) -> Tuple[bool, List[Tuple[int, int]], float]:
        """Test if OpenCV can access the device and find supported resolutions."""
        supported_resolutions = []
        max_fps = 0.0
        
        try:
            self.stream= cv2.VideoCapture(device_number)
            
            if not self.stream.isOpened():
                return False, [], 0.0
            
            # Set a timeout for frame capture to prevent hanging
            self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test common resolutions (reduced list for faster testing)
            test_resolutions = [
                (640, 480),   # VGA
                (1280, 720),  # 720p
                (1920, 1080), # 1080p
            ]
            
            for width, height in test_resolutions:
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Check if resolution was actually set
                actual_width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                if actual_width == width and actual_height == height:
                    # Try to capture a frame to verify it works (with timeout)
                    ret, frame = self.stream.read()
                    if ret and frame is not None and frame.size > 0:
                        if (actual_width, actual_height) not in supported_resolutions:
                            supported_resolutions.append((actual_width, actual_height))
            
            # Get maximum FPS (usually at lowest resolution)
            if supported_resolutions:
                min_res = min(supported_resolutions, key=lambda x: x[0] * x[1])
                self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, min_res[0])
                self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, min_res[1])
                max_fps = self.stream.get(cv2.CAP_PROP_FPS)
            
            self.stream.release()
            return True, supported_resolutions, max_fps
            
        except Exception as e:
            print(f"Error testing OpenCV access for device {device_number}: {e}")
            return False, [], 0.0
    
    def find_best_webcam(self) -> Optional[WebcamInfo]:
        """Find the best available webcam."""
        video_devices = self.detect_video_devices()
        
        for device_path in video_devices:
            try:
                device_number = int(device_path.split('video')[-1])
                
                # Test OpenCV access first (fastest check)
                is_working, resolutions, max_fps = self.test_opencv_access(device_number)
                
                if is_working:
                    # Get device information
                    device_info = self.get_device_info(device_path)
                    device_name = device_info.get('Driver name', 'Unknown')
                    driver = device_info.get('Bus info', 'Unknown')
                    
                    webcam_info = WebcamInfo(
                        device_path=device_path,
                        device_number=device_number,
                        name=device_name,
                        driver=driver,
                        capabilities=[],  # Not needed for basic functionality
                        supported_resolutions=resolutions,
                        supported_formats=[],  # Not needed for basic functionality
                        max_fps=max_fps,
                        is_working=is_working
                    )
                    
                    return webcam_info
                
            except Exception as e:
                continue
        
        return None


class USBCamera(CameraTemplate):
    """
    USB Camera implementation with automatic detection and capability discovery.
    
    This class automatically finds the best available USB webcam and configures
    it with optimal settings based on discovered capabilities.
    """
    
    def __init__(self, device_id: Optional[int] = None, 
                 width: Optional[int] = None, 
                 height: Optional[int] = None):
        """
        Initialize USB camera with automatic detection.
        
        Args:
            device_id: Specific device ID to use (if None, auto-detect)
            width: Target width (if None, use best available)
            height: Target height (if None, use best available)
        """
        self.logger = setup_logging(__name__)
        self.device_id = device_id
        self.target_width = width
        self.target_height = height
        
        self.stream = None
        self.is_running = False
        self.webcam_info: Optional[WebcamInfo] = None
        
        # Current settings
        self.current_width = 640
        self.current_height = 480
        self.current_fps = 0.0
        
        # FPS tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        self.logger.info("Initializing USB Camera with automatic detection")
        self._detect_and_configure()
    
    def _detect_and_configure(self) -> None:
        """Detect available webcams and configure the best one."""
        detector = WebcamDetector()
        
        if self.device_id is not None:
            # Use specified device
            self.logger.info(f"Using specified device {self.device_id}")
            is_working, resolutions, max_fps = detector.test_opencv_access(self.device_id)
            
            if is_working:
                device_info = detector.get_device_info(f'/dev/video{self.device_id}')
                self.webcam_info = WebcamInfo(
                    device_path=f'/dev/video{self.device_id}',
                    device_number=self.device_id,
                    name=device_info.get('Driver name', 'Unknown'),
                    driver=device_info.get('Bus info', 'Unknown'),
                    capabilities=[],
                    supported_resolutions=resolutions,
                    supported_formats=[],
                    max_fps=max_fps,
                    is_working=True
                )
            else:
                raise RuntimeError(f"Specified device {self.device_id} is not working")
        else:
            # Auto-detect best webcam
            self.logger.info("Auto-detecting best available webcam...")
            self.webcam_info = detector.find_best_webcam()
            
            if self.webcam_info is None:
                raise RuntimeError("No working USB webcams found")
        
        self.logger.info(f"Found webcam: {self.webcam_info.name} on {self.webcam_info.device_path}")
        self.logger.info(f"Supported resolutions: {len(self.webcam_info.supported_resolutions)}")
        
        # Set optimal resolution
        self._set_optimal_resolution()
    
    def _set_optimal_resolution(self) -> None:
        """Set the optimal resolution based on target and available options."""
        if not self.webcam_info or not self.webcam_info.supported_resolutions:
            return
        
        if self.target_width and self.target_height:
            # Use specified resolution if supported
            target_res = (self.target_width, self.target_height)
            if target_res in self.webcam_info.supported_resolutions:
                self.current_width, self.current_height = target_res
                self.logger.info(f"Using specified resolution: {self.current_width}x{self.current_height}")
                return
        
        # Find best available resolution
        if self.target_width and self.target_height:
            # Find closest to target
            target_pixels = self.target_width * self.target_height
            best_res = min(self.webcam_info.supported_resolutions, 
                          key=lambda x: abs(x[0] * x[1] - target_pixels))
        else:
            # Use highest resolution
            best_res = max(self.webcam_info.supported_resolutions, 
                          key=lambda x: x[0] * x[1])
        
        self.current_width, self.current_height = best_res
        self.logger.info(f"Using optimal resolution: {self.current_width}x{self.current_height}")
    
    def start(self) -> bool:
        """Start the USB camera."""
        if self.webcam_info is None:
            self.logger.error("No webcam detected")
            return False
        
        try:
            self.logger.info(f"Starting USB camera device {self.webcam_info.device_number}")
            
            self.stream = cv2.VideoCapture(self.webcam_info.device_number)
            if not self.stream.isOpened():
                self.logger.error(f"Failed to open camera device {self.webcam_info.device_number}")
                return False
            
            # Set resolution
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.current_width)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.current_height)
            
            # Verify actual resolution
            actual_width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width != self.current_width or actual_height != self.current_height:
                self.logger.warning(f"Requested {self.current_width}x{self.current_height}, "
                                  f"got {actual_width}x{actual_height}")
                self.current_width = actual_width
                self.current_height = actual_height
            
            self.is_running = True
            self.fps_start_time = time.time()
            self.fps_counter = 0
            
            self.logger.info(f"USB camera started successfully at {self.current_width}x{self.current_height}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting USB camera: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get a frame from the camera."""
        if not self.is_running or self.stream is None:
            return None
        
        try:
            ret, frame = self.stream.read()
            if ret:
                self._update_fps()
                return frame
            else:
                self.logger.warning("Failed to read frame from camera")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def get_frame_grayscale(self) -> Optional[np.ndarray]:
        """Get a grayscale frame from the camera."""
        if not self.is_running or self.stream is None:
            return None
        
        try:
            ret, frame = self.stream.read()
            if ret:
                self._update_fps()
                
                # Convert to grayscale
                import cv2
                if len(frame.shape) == 3:
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    # Already grayscale
                    gray_frame = frame
                
                return gray_frame
            else:
                self.logger.warning("Failed to read grayscale frame from camera")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing grayscale frame: {e}")
            return None
    
    def set_resolution(self, width: int, height: int) -> None:
        """Set camera resolution."""
        if self.is_running:
            self.logger.warning("Cannot change resolution while camera is running")
            return
        
        self.target_width = width
        self.target_height = height
        self._set_optimal_resolution()
        self.logger.info(f"Resolution set to {self.current_width}x{self.current_height}")
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get current camera resolution."""
        return (self.current_width, self.current_height)
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.current_fps
    
    def is_available(self) -> bool:
        """Check if camera is available."""
        return self.is_running and self.stream is not None and self.stream.isOpened()
    
    def shutdown(self) -> None:
        """Stop camera capture."""
        try:
            if self.stream is not None:
                self.stream.release()
                self.stream = None
            
            self.is_running = False
            self.logger.info("USB camera stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping USB camera: {e}")
    
    
    
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
    
    def get_webcam_info(self) -> Optional[WebcamInfo]:
        """Get information about the detected webcam."""
        return self.webcam_info
    
    def get_supported_resolutions(self) -> List[Tuple[int, int]]:
        """Get list of supported resolutions."""
        if self.webcam_info:
            return self.webcam_info.supported_resolutions
        return []
    
    def __enter__(self):
        """Context manager entry."""
        if not self.start():
            raise RuntimeError("Failed to start USB camera")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 