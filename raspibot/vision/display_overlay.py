"""Display overlay utilities for camera frames."""

import cv2
import numpy as np
from typing import Tuple, Optional, List
from .detection_models import PersonDetection


class DisplayOverlay:
    """Utility class for adding overlays to camera frames."""
    
    def __init__(self, font_scale: float = 0.6, thickness: int = 2):
        """
        Initialize display overlay.
        
        Args:
            font_scale: Font scale for text rendering
            thickness: Line thickness for text and boxes
        """
        self.font_scale = font_scale
        self.thickness = thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Colors (BGR format)
        self.colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (0, 0, 255),
            'green': (0, 255, 0),
            'blue': (255, 0, 0),
            'yellow': (0, 255, 255),
            'cyan': (255, 255, 0),
            'magenta': (255, 0, 255)
        }
        
        # Overlay background
        self.overlay_bg_color = (0, 0, 0)  # Black background
        self.overlay_alpha = 0.7  # Semi-transparent
    
    def add_info_overlay(self, 
                        frame: np.ndarray,
                        fps: float,
                        mode: str,
                        detection_type: Optional[str] = None,
                        detections: Optional[List[PersonDetection]] = None) -> np.ndarray:
        """
        Add information overlay to frame.
        
        Args:
            frame: Input frame (BGR format)
            fps: Current FPS
            mode: Processing mode ('Color' or 'Grayscale')
            detection_type: Type of detection ('OpenCV', 'AI Model', etc.)
            detections: List of detections to display
            
        Returns:
            Frame with overlay added
        """
        if frame is None:
            return frame
        
        # Create a copy to avoid modifying original
        overlay_frame = frame.copy()
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Calculate overlay position (top-right corner)
        overlay_width = 200
        overlay_height = 80
        overlay_x = width - overlay_width - 10
        overlay_y = 10
        
        # Create semi-transparent background
        overlay_bg = np.zeros((overlay_height, overlay_width, 3), dtype=np.uint8)
        overlay_bg[:] = self.overlay_bg_color
        
        # Blend overlay background with frame
        roi = overlay_frame[overlay_y:overlay_y + overlay_height, 
                           overlay_x:overlay_x + overlay_width]
        blended = cv2.addWeighted(roi, 1 - self.overlay_alpha, 
                                 overlay_bg, self.overlay_alpha, 0)
        overlay_frame[overlay_y:overlay_y + overlay_height, 
                     overlay_x:overlay_x + overlay_width] = blended
        
        # Add text information
        text_y = overlay_y + 25
        line_height = 20
        
        # FPS
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(overlay_frame, fps_text, 
                   (overlay_x + 10, text_y), 
                   self.font, self.font_scale, self.colors['white'], self.thickness)
        
        # Mode
        mode_text = f"Mode: {mode}"
        cv2.putText(overlay_frame, mode_text, 
                   (overlay_x + 10, text_y + line_height), 
                   self.font, self.font_scale, self.colors['white'], self.thickness)
        
        # Detection type (if specified)
        if detection_type:
            detection_text = f"Detection: {detection_type}"
            cv2.putText(overlay_frame, detection_text, 
                       (overlay_x + 10, text_y + 2 * line_height), 
                       self.font, self.font_scale, self.colors['white'], self.thickness)
        
        # Add detection boxes if provided
        if detections:
            overlay_frame = self.add_detection_boxes(overlay_frame, detections)
        
        return overlay_frame
    
    def add_detection_boxes(self, 
                           frame: np.ndarray, 
                           detections: List[PersonDetection]) -> np.ndarray:
        """
        Add detection bounding boxes to frame.
        
        Args:
            frame: Input frame
            detections: List of PersonDetection objects
            
        Returns:
            Frame with detection boxes added
        """
        if frame is None or not detections:
            return frame
        
        for detection in detections:
            x, y, w, h = detection.bbox
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), 
                         self.colors['green'], self.thickness)
            
            # Add confidence label
            confidence_text = f"{detection.category}: {detection.confidence:.2f}"
            
            # Calculate text position
            text_size = cv2.getTextSize(confidence_text, self.font, 
                                       self.font_scale, self.thickness)[0]
            text_x = x
            text_y = y - 5 if y > text_size[1] + 5 else y + h + text_size[1]
            
            # Draw text background
            cv2.rectangle(frame, 
                         (text_x, text_y - text_size[1] - 5),
                         (text_x + text_size[0], text_y + 5),
                         self.colors['black'], -1)
            
            # Draw text
            cv2.putText(frame, confidence_text, 
                       (text_x, text_y), 
                       self.font, self.font_scale, 
                       self.colors['white'], self.thickness)
        
        return frame
    
    def add_resolution_info(self, 
                           frame: np.ndarray, 
                           resolution: Tuple[int, int]) -> np.ndarray:
        """
        Add resolution information to frame.
        
        Args:
            frame: Input frame
            resolution: Current resolution (width, height)
            
        Returns:
            Frame with resolution info added
        """
        if frame is None:
            return frame
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Resolution text
        resolution_text = f"Resolution: {width}x{height}"
        
        # Position at bottom-left
        text_x = 10
        text_y = height - 10
        
        # Draw text background
        text_size = cv2.getTextSize(resolution_text, self.font, 
                                   self.font_scale, self.thickness)[0]
        cv2.rectangle(frame, 
                     (text_x - 5, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 5, text_y + 5),
                     self.colors['black'], -1)
        
        # Draw text
        cv2.putText(frame, resolution_text, 
                   (text_x, text_y), 
                   self.font, self.font_scale, 
                   self.colors['white'], self.thickness)
        
        return frame
    
    def add_performance_metrics(self, 
                               frame: np.ndarray,
                               fps: float,
                               memory_mb_per_sec: float) -> np.ndarray:
        """
        Add detailed performance metrics to frame.
        
        Args:
            frame: Input frame
            fps: Current FPS
            memory_mb_per_sec: Memory usage in MB/s
            
        Returns:
            Frame with performance metrics added
        """
        if frame is None:
            return frame
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Performance text
        perf_text = f"FPS: {fps:.1f} | Memory: {memory_mb_per_sec:.1f} MB/s"
        
        # Position at bottom-right
        text_size = cv2.getTextSize(perf_text, self.font, 
                                   self.font_scale, self.thickness)[0]
        text_x = width - text_size[0] - 10
        text_y = height - 10
        
        # Draw text background
        cv2.rectangle(frame, 
                     (text_x - 5, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 5, text_y + 5),
                     self.colors['black'], -1)
        
        # Draw text
        cv2.putText(frame, perf_text, 
                   (text_x, text_y), 
                   self.font, self.font_scale, 
                   self.colors['white'], self.thickness)
        
        return frame


def create_display_overlay(font_scale: float = 0.6, thickness: int = 2) -> DisplayOverlay:
    """
    Create a display overlay instance.
    
    Args:
        font_scale: Font scale for text rendering
        thickness: Line thickness for text and boxes
        
    Returns:
        DisplayOverlay instance
    """
    return DisplayOverlay(font_scale=font_scale, thickness=thickness) 