"""Display manager for camera output with automatic environment detection.

This module implements a headless architecture that separates display logic
from presentation, automatically detecting the best display method for the
current environment.
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from .display_handlers import (
    ConnectedDisplayHandler,
    RaspberryConnectDisplayHandler,
    HeadlessDisplayHandler
)
from ..utils.logging_config import setup_logging


class DisplayManager:
    """Manages display logic without dictating presentation.
    
    This class implements the headless component pattern, separating display
    logic from presentation. It automatically detects the best display method
    for the current environment and provides a unified interface.
    """
    
    SUPPORTED_MODES = {
        'connected_screen': 'Connected Screen',
        'raspberry_connect': 'Raspberry Pi Connect', 
        'headless': 'Headless Mode'
    }
    
    def __init__(self, auto_detect: bool = True, mode: Optional[str] = None):
        """
        Initialize display manager.
        
        Args:
            auto_detect: Whether to automatically detect display method
            mode: Force specific display mode (overrides auto_detect)
        """
        self.logger = setup_logging(__name__)
        self.auto_detect = auto_detect
        
        # Display handlers for each mode
        self.display_handlers = {
            'connected_screen': ConnectedDisplayHandler,
            'raspberry_connect': RaspberryConnectDisplayHandler,
            'headless': HeadlessDisplayHandler,
        }
        
        # Determine display method
        if mode:
            if mode not in self.SUPPORTED_MODES:
                raise ValueError(f"Unsupported display mode: {mode}. "
                               f"Supported modes: {list(self.SUPPORTED_MODES.keys())}")
            self.display_method = mode
        elif auto_detect:
            self.display_method = self._detect_display_method()
        else:
            # Default to headless if not auto-detecting
            self.display_method = 'headless'
        
        self.logger.info(f"Display manager initialized with mode: {self.display_method}")
        
        # Create display handler
        self.display_handler = self._create_display_handler()
    
    def _detect_display_method(self) -> str:
        """
        Auto-detect the best display method for current environment.
        
        Detection priority:
        1. Connected Screen - Can create OpenCV windows
        2. Raspberry Pi Connect - WayVNC socket present
        3. Headless - Everything else
        
        Returns:
            Display method string
        """
        self.logger.debug("Detecting display environment...")
        
        # 1. Check for Raspberry Pi Connect (WayVNC) first
        if os.path.exists('/tmp/wayvnc/wayvncctl.sock') and os.path.exists('/tmp/.X11-unix/X0'):
            # Set DISPLAY for WayVNC environment
            if 'DISPLAY' not in os.environ:
                os.environ['DISPLAY'] = ':0'
            # Test if we can create a window now
            try:
                cv2.namedWindow("test", cv2.WINDOW_AUTOSIZE)
                cv2.destroyWindow("test")
                self.logger.debug("Raspberry Pi Connect detected - using raspberry_connect mode")
                return "raspberry_connect"
            except Exception as e:
                self.logger.debug(f"WayVNC detected but window creation failed: {e}")
        
        # 2. Check for SSH X11 forwarding
        if os.environ.get('SSH_CONNECTION') and os.path.exists('/tmp/.X11-unix/X0'):
            if 'DISPLAY' not in os.environ:
                os.environ['DISPLAY'] = ':0'
            try:
                cv2.namedWindow("test", cv2.WINDOW_AUTOSIZE)
                cv2.destroyWindow("test")
                self.logger.debug("SSH X11 forwarding detected - using raspberry_connect mode")
                return "raspberry_connect"
            except Exception as e:
                self.logger.debug(f"SSH X11 forwarding detected but window creation failed: {e}")
        
        # 3. Check for physical display (can create OpenCV windows)
        if os.environ.get('DISPLAY'):
            try:
                cv2.namedWindow("test", cv2.WINDOW_AUTOSIZE)
                cv2.destroyWindow("test")
                self.logger.debug("Physical display detected - using connected_screen mode")
                return "connected_screen"
            except Exception as e:
                self.logger.debug(f"Physical display not available: {e}")
        
        # 3. Fallback to headless
        self.logger.debug("No display environment detected - using headless mode")
        return "headless"
    
    def _create_display_handler(self):
        """Create the appropriate display handler for the detected method."""
        handler_class = self.display_handlers.get(self.display_method)
        if not handler_class:
            raise ValueError(f"No handler found for display method: {self.display_method}")
        
        return handler_class()
    
    def get_display_method(self) -> str:
        """Get the current display method."""
        return self.display_method
    
    def get_display_handler(self):
        """Get the current display handler."""
        return self.display_handler
    
    def show_frame(self, display_data: Dict[str, Any]) -> bool:
        """
        Show frame using the appropriate display handler.
        
        Args:
            display_data: Dictionary containing frame and metadata
            
        Returns:
            True if should continue, False if user requested quit
        """
        return self.display_handler.show_frame(display_data)
    
    def show_info(self, info: Dict[str, Any]) -> None:
        """
        Show information using the appropriate display handler.
        
        Args:
            info: Information to display
        """
        self.display_handler.show_info(info)
    
    def show_help(self) -> None:
        """Show help information."""
        self.display_handler.show_help()
    
    def get_key(self) -> int:
        """Get key press from display handler."""
        return self.display_handler.get_key()
    
    def close(self) -> None:
        """Close display and cleanup."""
        self.display_handler.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def get_unsupported_environment_message() -> str:
    """Get user-friendly message for unsupported environments."""
    return (
        "⚠️  Display Environment Not Supported\n"
        "This environment is not currently supported by raspibot.\n"
        f"Supported modes: {', '.join(DisplayManager.SUPPORTED_MODES.values())}\n\n"
        "To add support for this environment, see docs/camera_display_modes.md\n\n"
        "Falling back to headless mode for continued operation."
    ) 