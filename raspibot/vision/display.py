"""Visual display for camera feed with face detection boxes."""

import cv2
import numpy as np
import os
from typing import List, Tuple, Optional

from ..utils.logging_config import setup_logging


class Display:
    """Simple display for camera feed with face detection boxes."""
    
    def __init__(self, window_name: str = "Face Tracking Robot", 
                 font_scale: float = 1.0, 
                 font_thickness: int = 2,
                 headless: bool = None):
        """
        Initialize display window.
        
        Args:
            window_name: Name of the display window
            font_scale: Scale factor for text
            font_thickness: Thickness of text lines
            headless: Force headless mode. If None, auto-detect from environment
        """
        self.window_name = window_name
        self.font_scale = font_scale
        self.font_thickness = font_thickness
        self.logger = setup_logging(__name__)
        
        # Auto-detect headless environment
        if headless is None:
            self.headless = self._is_headless_environment()
        else:
            self.headless = headless
        
        # Colors (BGR format)
        self.face_color = (0, 255, 0)      # Green for face boxes
        self.center_color = (0, 255, 0)    # Green for face centers
        self.text_color = (0, 255, 0)      # Green for text
        self.stable_color = (0, 255, 0)    # Green for stable faces
        self.unstable_color = (0, 0, 255)  # Red for unstable faces
        
        # Create window only if not headless
        if not self.headless:
            try:
                cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
                self.logger.info(f"Display window '{self.window_name}' created")
            except Exception as e:
                self.logger.warning(f"Failed to create display window: {e}")
                self.headless = True
        else:
            self.logger.info("Running in headless mode - no display window created")
    
    def _is_headless_environment(self) -> bool:
        """Detect if running in a headless environment."""
        # Check for Raspberry Pi Connect / WayVNC environment
        if os.path.exists('/tmp/wayvnc/wayvncctl.sock'):
            # WayVNC is running, check if we can access X11
            if os.path.exists('/tmp/.X11-unix/X0'):
                # X11 server is available, try to set DISPLAY if not set
                if 'DISPLAY' not in os.environ:
                    os.environ['DISPLAY'] = ':0'
                return False
        
        # Check for common headless indicators
        headless_indicators = [
            'DISPLAY' not in os.environ,
            os.environ.get('DISPLAY', '') == '',
            os.environ.get('XDG_SESSION_TYPE', '') == 'tty',
            os.environ.get('TERM', '') == 'linux',
            'SSH_CONNECTION' in os.environ and 'DISPLAY' not in os.environ,
        ]
        
        # Check if we can actually create a window
        try:
            cv2.namedWindow("test", cv2.WINDOW_AUTOSIZE)
            cv2.destroyWindow("test")
            return False
        except Exception:
            return True
    
    def show_frame(self, frame: np.ndarray, 
                   faces: List[Tuple[int, int, int, int]] = None,
                   stable_faces: List[Tuple[int, int, int, int]] = None,
                   camera_fps: float = 0.0,
                   detection_fps: float = 0.0,
                   servo_position: Optional[Tuple[float, float]] = None,
                   search_status: Optional[dict] = None) -> bool:
        """
        Show frame with face detection boxes and status information.
        
        Args:
            frame: Input frame to display
            faces: List of all detected faces as (x, y, w, h) tuples
            stable_faces: List of stable faces as (x, y, w, h) tuples
            camera_fps: Current camera FPS
            detection_fps: Current detection FPS
            servo_position: Current servo position as (pan, tilt) coordinates
            search_status: Search pattern status information
            
        Returns:
            False if user pressed 'q' to quit, True otherwise
        """
        if frame is None:
            return True
        
        try:
            # Create a copy for drawing
            display_frame = frame.copy()
            
            # Draw all detected faces (unstable in red)
            if faces:
                for face in faces:
                    if stable_faces and face in stable_faces:
                        continue  # Will be drawn as stable
                    self._draw_face_rectangle(display_frame, face, self.unstable_color, "UNSTABLE")
            
            # Draw stable faces (green)
            if stable_faces:
                for face in stable_faces:
                    self._draw_face_rectangle(display_frame, face, self.stable_color, "TRACKING")
            
            # Draw status information
            self._draw_status_info(display_frame, faces, stable_faces, camera_fps, detection_fps, servo_position, search_status)
            
            # Show the frame only if not headless
            if not self.headless:
                cv2.imshow(self.window_name, display_frame)
                # Check for quit key
                key = cv2.waitKey(1) & 0xFF
                return key != ord('q')
            else:
                # In headless mode, just log the status
                total_faces = len(faces) if faces else 0
                stable_count = len(stable_faces) if stable_faces else 0
                search_active = search_status.get('active', False) if search_status else False
                self.logger.debug(f"Headless display: {total_faces} faces ({stable_count} stable), "
                                f"Camera: {camera_fps:.1f} FPS, Detection: {detection_fps:.1f} FPS, "
                                f"Search: {'ACTIVE' if search_active else 'inactive'}")
                return True
            
        except Exception as e:
            self.logger.error(f"Error displaying frame: {e}")
            return False
    
    def close(self) -> None:
        """Close display window and cleanup."""
        if not self.headless:
            try:
                cv2.destroyWindow(self.window_name)
                self.logger.info(f"Display window '{self.window_name}' closed")
            except Exception as e:
                self.logger.error(f"Error closing display: {e}")
        else:
            self.logger.debug("Headless display closed")
    
    def _draw_face_rectangle(self, frame: np.ndarray, face: Tuple[int, int, int, int], 
                           color: Tuple[int, int, int], label: str) -> None:
        """
        Draw face rectangle with center point and label.
        
        Args:
            frame: Frame to draw on
            face: Face rectangle as (x, y, w, h)
            color: Color for drawing (BGR)
            label: Label text for the face
        """
        x, y, w, h = face
        
        # Draw rectangle
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        
        # Draw center point
        center_x, center_y = x + w // 2, y + h // 2
        cv2.circle(frame, (center_x, center_y), 5, color, -1)
        
        # Draw label
        label_y = y - 10 if y > 30 else y + h + 20
        cv2.putText(frame, label, (x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, color, 1, cv2.LINE_AA)
        
        # Draw size info
        size_text = f"{w}x{h}"
        size_y = label_y + 20 if label_y < y else label_y - 20
        cv2.putText(frame, size_text, (x, size_y), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.4, color, 1, cv2.LINE_AA)
    
    def _draw_status_info(self, frame: np.ndarray, 
                         faces: List[Tuple[int, int, int, int]] = None,
                         stable_faces: List[Tuple[int, int, int, int]] = None,
                         camera_fps: float = 0.0,
                         detection_fps: float = 0.0,
                         servo_position: Optional[Tuple[float, float]] = None,
                         search_status: Optional[dict] = None) -> None:
        """
        Draw status information on the frame.
        
        Args:
            frame: Frame to draw on
            faces: List of all detected faces
            stable_faces: List of stable faces
            camera_fps: Camera FPS
            detection_fps: Detection FPS
            servo_position: Servo position
            search_status: Search pattern status
        """
        # Status text lines
        status_lines = []
        
        # Face counts
        total_faces = len(faces) if faces else 0
        stable_count = len(stable_faces) if stable_faces else 0
        unstable_count = total_faces - stable_count
        
        status_lines.append(f"Faces: {total_faces} (Stable: {stable_count}, Unstable: {unstable_count})")
        
        # FPS information
        status_lines.append(f"Camera FPS: {camera_fps:.1f}")
        status_lines.append(f"Detection FPS: {detection_fps:.1f}")
        
        # Servo position
        if servo_position:
            pan, tilt = servo_position
            status_lines.append(f"Servo: Pan {pan:.2f}, Tilt {tilt:.2f}")
        
        # Search status
        if search_status:
            search_active = search_status.get('active', False)
            status_lines.append(f"Search: {'ACTIVE' if search_active else 'inactive'}")
        
        # Instructions
        status_lines.append("")
        status_lines.append("Press 'q' to quit")
        
        # Draw status lines
        y_offset = 30
        for line in status_lines:
            if line:  # Skip empty lines
                cv2.putText(frame, line, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                           self.font_scale * 0.6, self.text_color, 1, cv2.LINE_AA)
            y_offset += 25
    
    def show_error_message(self, message: str) -> None:
        """
        Show error message in a simple window.
        
        Args:
            message: Error message to display
        """
        try:
            # Create a black frame for error message
            error_frame = np.zeros((200, 600, 3), dtype=np.uint8)
            
            # Split message into lines
            lines = message.split('\n')
            y_offset = 50
            
            for line in lines:
                cv2.putText(error_frame, line, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 0, 255), 2, cv2.LINE_AA)  # Red text
                y_offset += 30
            
            cv2.putText(error_frame, "Press any key to close", (10, y_offset + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            cv2.imshow(self.window_name, error_frame)
            cv2.waitKey(0)
            
        except Exception as e:
            self.logger.error(f"Error showing error message: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 