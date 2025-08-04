"""Display handlers for different display environments.

This module contains the presentation layer implementations for each
supported display mode in the headless architecture.
"""

import cv2
import numpy as np
import os
import time
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod

from .display_utils import center_window_on_screen, get_screen_dimensions
from ..utils.logging_config import setup_logging


class BaseDisplayHandler(ABC):
    """Base class for display handlers."""
    
    def __init__(self, window_name: str = "Raspibot Camera"):
        """
        Initialize base display handler.
        
        Args:
            window_name: Name of the display window
        """
        self.window_name = window_name
        self.logger = setup_logging(__name__)
        self.display_name = "Base Display"
        self.is_initialized = False
        
    @abstractmethod
    def setup_window(self) -> bool:
        """Set up display window. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def show_frame(self, display_data: Dict[str, Any]) -> bool:
        """Show frame. Must be implemented by subclasses."""
        pass
    
    def show_info(self, info: Dict[str, Any]) -> None:
        """Show information (default implementation)."""
        self.logger.info(f"Display info: {info}")
    
    def show_help(self) -> None:
        """Show help information (default implementation)."""
        help_text = (
            "Camera Controls:\n"
            "  Press 'q' to quit\n"
            "  Press 's' to save screenshot\n"
            "  Press 'i' to show/hide info overlay\n"
            "  Press 'h' to show this help"
        )
        self.logger.info(f"Help: {help_text}")
    
    def get_key(self) -> int:
        """Get key press (default implementation returns -1)."""
        return -1
    
    def close(self) -> None:
        """Close display (default implementation)."""
        self.logger.debug(f"Closing {self.display_name} display")


class ConnectedDisplayHandler(BaseDisplayHandler):
    """Display handler for connected screen with direct OpenCV windows."""
    
    def __init__(self, window_name: str = "Raspibot Camera"):
        super().__init__(window_name)
        self.display_name = "Connected Screen"
        self.show_info_overlay = True
        
    def setup_window(self) -> bool:
        """Set up window for connected screen."""
        try:
            # Create window
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            
            # Get screen dimensions
            screen_width, screen_height = get_screen_dimensions()
            
            # Calculate optimal window size (80% of screen, maintain aspect ratio)
            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)
            
            # Default to 1280x720 if no frame size available
            frame_width, frame_height = 1280, 720
            
            # Calculate window size maintaining aspect ratio
            aspect_ratio = frame_width / frame_height
            if max_width / aspect_ratio <= max_height:
                window_width = max_width
                window_height = int(max_width / aspect_ratio)
            else:
                window_height = max_height
                window_width = int(max_height * aspect_ratio)
            
            # Resize window
            cv2.resizeWindow(self.window_name, window_width, window_height)
            
            # Center window on screen
            center_window_on_screen(self.window_name, window_width, window_height)
            
            self.is_initialized = True
            self.logger.info(f"Connected screen display window '{self.window_name}' created")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create connected screen window: {e}")
            return False
    
    def show_frame(self, display_data: Dict[str, Any]) -> bool:
        """Show frame on connected screen."""
        if not self.is_initialized:
            if not self.setup_window():
                return True  # Continue without display
        
        frame = display_data.get('frame')
        if frame is None:
            return True
        
        try:
            # Create display frame
            display_frame = frame.copy()
            
            # Add info overlay if requested
            if display_data.get('show_info', True):
                self._add_info_overlay(display_frame, display_data)
            
            # Show frame
            cv2.imshow(self.window_name, display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                return False
            elif key == ord('i'):
                # Toggle info overlay
                self.show_info_overlay = not self.show_info_overlay
                self.logger.info(f"Info overlay: {'ON' if self.show_info_overlay else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error showing frame: {e}")
            return True
    
    def _add_info_overlay(self, frame: np.ndarray, display_data: Dict[str, Any]) -> None:
        """Add information overlay to frame."""
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Info text
        info_lines = []
        
        # Camera info
        camera_info = display_data.get('camera_info', {})
        info_lines.append(f"Camera: {camera_info.get('type', 'Unknown')}")
        info_lines.append(f"Resolution: {camera_info.get('resolution', 'Unknown')}")
        
        # Performance info
        fps = display_data.get('fps', 0)
        frame_count = display_data.get('frame_count', 0)
        info_lines.append(f"FPS: {fps:.1f}")
        info_lines.append(f"Frames: {frame_count}")
        
        # Display mode
        info_lines.append(f"Display: {self.display_name}")
        
        # Controls
        info_lines.append("")
        info_lines.append("Press 'q' to quit, 'i' to toggle info, 'h' for help")
        
        # Draw info overlay
        y_offset = 30
        for line in info_lines:
            if line:  # Skip empty lines
                # Draw text with black outline for better visibility
                cv2.putText(frame, line, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 0, 0), 2, cv2.LINE_AA)  # Black outline
                cv2.putText(frame, line, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 255, 0), 1, cv2.LINE_AA)  # Green text
            y_offset += 25
    
    def get_key(self) -> int:
        """Get key press from OpenCV window."""
        return cv2.waitKey(1) & 0xFF
    
    def close(self) -> None:
        """Close OpenCV window."""
        if self.is_initialized:
            try:
                cv2.destroyWindow(self.window_name)
                self.logger.info(f"Connected screen window '{self.window_name}' closed")
            except Exception as e:
                self.logger.error(f"Error closing window: {e}")
        super().close()


class RaspberryConnectDisplayHandler(BaseDisplayHandler):
    """Display handler for Raspberry Pi Connect (WayVNC) environment."""
    
    def __init__(self, window_name: str = "Raspibot Camera"):
        super().__init__(window_name)
        self.display_name = "Raspberry Pi Connect"
        self.show_info_overlay = True
        
    def setup_window(self) -> bool:
        """Set up window for Raspberry Pi Connect."""
        try:
            # Create window optimized for remote viewing
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            
            # Get screen dimensions
            screen_width, screen_height = get_screen_dimensions()
            
            # Use camera configuration from hardware config
            from raspibot.settings.config import PI_AI_CAMERA_CONFIG
            
            # Get display resolution from config - use it directly for window size
            display_config = PI_AI_CAMERA_CONFIG["camera_modes"]["normal_video"]["display"]
            window_width, window_height = display_config["resolution"]
            
            # Use the full config resolution - no scaling down
            # This ensures the window matches the camera's actual output resolution
            
            # Resize window
            cv2.resizeWindow(self.window_name, window_width, window_height)
            
            # Add a small delay to ensure window is created before moving
            import time
            time.sleep(0.1)
            
            # Position window at fixed coordinates to avoid centering issues
            # Y position accounts for Raspberry Pi menu bar (typically 24-32 pixels)
            cv2.moveWindow(self.window_name, 10, 35)
            
            self.is_initialized = True
            self.logger.info(f"Raspberry Pi Connect display window '{self.window_name}' created with size ({window_width}, {window_height})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Raspberry Pi Connect window: {e}")
            return False
    
    def show_frame(self, display_data: Dict[str, Any]) -> bool:
        """Show frame on Raspberry Pi Connect."""
        if not self.is_initialized:
            if not self.setup_window():
                return True  # Continue without display
        
        frame = display_data.get('frame')
        if frame is None:
            return True
        
        try:
            # Create display frame
            display_frame = frame.copy()
            
            # Add info overlay if requested
            if display_data.get('show_info', True):
                self._add_info_overlay(display_frame, display_data)
            
            # Show frame
            cv2.imshow(self.window_name, display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                return False
            elif key == ord('i'):
                # Toggle info overlay
                self.show_info_overlay = not self.show_info_overlay
                self.logger.info(f"Info overlay: {'ON' if self.show_info_overlay else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error showing frame: {e}")
            return True
    
    def _add_info_overlay(self, frame: np.ndarray, display_data: Dict[str, Any]) -> None:
        """Add information overlay to frame (optimized for remote viewing)."""
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Info text (simplified for remote viewing)
        info_lines = []
        
        # Essential info only
        fps = display_data.get('fps', 0)
        frame_count = display_data.get('frame_count', 0)
        info_lines.append(f"FPS: {fps:.1f} | Frames: {frame_count}")
        info_lines.append(f"Display: {self.display_name}")
        info_lines.append("Press 'q' to quit, 'i' to toggle info")
        
        # Draw info overlay with larger text for remote viewing
        y_offset = 30
        for line in info_lines:
            if line:
                # Draw text with black outline for better visibility
                cv2.putText(frame, line, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 0, 0), 3, cv2.LINE_AA)  # Black outline
                cv2.putText(frame, line, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2, cv2.LINE_AA)  # Green text
            y_offset += 30
    
    def get_key(self) -> int:
        """Get key press from OpenCV window."""
        return cv2.waitKey(1) & 0xFF
    
    def close(self) -> None:
        """Close OpenCV window."""
        if self.is_initialized:
            try:
                cv2.destroyWindow(self.window_name)
                self.logger.info(f"Raspberry Pi Connect window '{self.window_name}' closed")
            except Exception as e:
                self.logger.error(f"Error closing window: {e}")
        super().close()


class HeadlessDisplayHandler(BaseDisplayHandler):
    """Display handler for headless environments (logging only)."""
    
    def __init__(self, window_name: str = "Raspibot Camera"):
        super().__init__(window_name)
        self.display_name = "Headless Mode"
        self.last_log_time = 0
        self.log_interval = 5.0  # Log every 5 seconds
        
    def setup_window(self) -> bool:
        """Set up headless display (no-op)."""
        self.is_initialized = True
        self.logger.info("Headless display initialized - no visual output")
        return True
    
    def show_frame(self, display_data: Dict[str, Any]) -> bool:
        """Show frame in headless mode (logging only)."""
        current_time = time.time()
        
        # Log status periodically to avoid spam
        if current_time - self.last_log_time >= self.log_interval:
            fps = display_data.get('fps', 0)
            frame_count = display_data.get('frame_count', 0)
            camera_info = display_data.get('camera_info', {})
            
            self.logger.info(
                f"Headless display: FPS={fps:.1f}, "
                f"Frames={frame_count}, "
                f"Camera={camera_info.get('type', 'Unknown')}"
            )
            self.last_log_time = current_time
        
        return True
    
    def show_info(self, info: Dict[str, Any]) -> None:
        """Show information in headless mode."""
        self.logger.info(f"Headless display info: {info}")
    
    def show_help(self) -> None:
        """Show help in headless mode."""
        help_text = (
            "Headless Mode Controls:\n"
            "  Press Ctrl+C to quit\n"
            "  Check logs for status information\n"
            "  No visual output available"
        )
        self.logger.info(f"Headless help: {help_text}")
    
    def get_key(self) -> int:
        """Get key press in headless mode (always returns -1)."""
        return -1
    
    def close(self) -> None:
        """Close headless display."""
        self.logger.info("Headless display closed")
        super().close() 