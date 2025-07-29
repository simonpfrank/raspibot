"""Utility functions for display management."""

import os
import cv2
import subprocess
from typing import Tuple


def get_screen_dimensions() -> Tuple[int, int]:
    """
    Get screen dimensions for window positioning.
    
    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        # Try to get screen dimensions from environment
        if 'DISPLAY' in os.environ:
            # For X11 systems, try to get screen info
            try:
                result = subprocess.run(['xrandr', '--current'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    # Parse xrandr output for primary screen
                    for line in result.stdout.split('\n'):
                        if '*' in line and 'x' in line:
                            # Extract resolution from line like "1920x1080*"
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '*' in part:
                                    res = part.replace('*', '')
                                    width, height = map(int, res.split('x'))
                                    return width, height
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
            
            # Try alternative method for remote desktop
            try:
                result = subprocess.run(['xdpyinfo'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'dimensions:' in line:
                            # Extract dimensions from line like "dimensions: 1920x1080 pixels"
                            parts = line.split(':')[1].strip().split()[0]
                            width, height = map(int, parts.split('x'))
                            return width, height
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
        
        # For remote desktop environments, use more conservative dimensions
        # This helps prevent windows from appearing off-screen
        if os.environ.get('SSH_CONNECTION') or os.path.exists('/tmp/wayvnc/wayvncctl.sock'):
            # Remote desktop - use smaller default dimensions
            return 1024, 768
        
        # Fallback to common resolutions
        common_resolutions = [
            (1920, 1080),  # Full HD
            (1366, 768),   # HD
            (1280, 720),   # HD Ready
            (1024, 768),   # XGA
            (800, 600),    # SVGA
        ]
        
        # Return first common resolution as default
        return common_resolutions[0]
        
    except Exception:
        # Ultimate fallback
        return 1280, 720


def center_window_on_screen(window_name: str, window_width: int, window_height: int) -> None:
    """
    Center a window on the screen.
    
    Args:
        window_name: Name of the window to center
        window_width: Width of the window
        window_height: Height of the window
    """
    try:
        screen_width, screen_height = get_screen_dimensions()
        
        # Calculate center position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Ensure window is within screen bounds
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        # For remote desktop environments, add some offset to ensure visibility
        # This helps with window decorations and taskbars
        x = max(50, x)  # At least 50 pixels from left
        y = max(50, y)  # At least 50 pixels from top
        
        # Move window to center
        cv2.moveWindow(window_name, x, y)
        
        # Log the positioning for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Window '{window_name}' positioned at ({x}, {y}) with size ({window_width}, {window_height})")
        logger.debug(f"Screen dimensions: ({screen_width}, {screen_height})")
        
    except Exception as e:
        # If centering fails, try a fallback position
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to center window: {e}")
        
        # Fallback: position in top-left with offset
        try:
            cv2.moveWindow(window_name, 100, 100)
            logger.info("Window positioned using fallback coordinates (100, 100)")
        except Exception as fallback_error:
            logger.error(f"Failed to position window even with fallback: {fallback_error}") 