#!/usr/bin/env python3
"""
Simple Person Detection

A clean, simple person detection example using HOG detector.
Features:
- Person detection with confidence threshold
- Simple coordinate tracking
- Distance estimation from object size
- Fast moving people ignored
"""

import cv2  # Only for drawing rectangles and text
import numpy as np
import time
import sys
import os
import argparse
from typing import List, Tuple, Optional
from collections import deque



# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from raspibot.hardware.servo_selector import get_servo_controller, ServoControllerType
from raspibot.vision.camera_selector import get_camera, CameraType
from raspibot.vision.person_detector import PersonDetector
from raspibot.vision.detection_result import DetectionResult
from raspibot.vision.display_manager import DisplayManager
from raspibot.utils.logging_config import setup_logging


class PersonDetectionSystem:
    """Simple person detection system."""
    
    def __init__(self, camera_instance=None, camera_mode="ai_detection"):
        """
        Initialize person detection system.
        
        Args:
            camera_instance: Optional existing camera instance to share
            camera_mode: Camera mode to use for detection
        """
        self.logger = setup_logging(__name__)
        
        # Initialize person detector with very low threshold for testing
        self.person_detector = PersonDetector(
            confidence_threshold=0.1,  # Very low threshold for testing
            camera_instance=camera_instance,  # Share existing camera instance
            camera_mode=camera_mode  # Pass camera mode
        )
        
        # Detection history for movement tracking
        self.detection_history = deque(maxlen=3)
        

        
        self.logger.info("Person detection system initialized")
    
    def detect_persons(self, frame: np.ndarray, servo_angles: Tuple[float, float]) -> List[DetectionResult]:
        """
        Perform person detection.
        
        Args:
            frame: Input frame
            servo_angles: Current (pan, tilt) angles
            
        Returns:
            List of detection results
        """
        results = []
        height, width = frame.shape[:2]
        camera_resolution = (width, height)
        
        # Person detection using AI camera
        person_results = self.person_detector.detect_persons(frame)
        
        # Add servo angles and timestamp to results
        for person_result in person_results:
            person_result.servo_angles = servo_angles
            person_result.timestamp = time.time()
            results.append(person_result)
        
        # Update detection history
        self.detection_history.extend(results)
        
        return results
    
    def get_stable_detections(self, min_detections: int = 2) -> List[DetectionResult]:
        """
        Get detections that have been stable (not moving fast).
        
        Args:
            min_detections: Minimum number of detections to consider stable
            
        Returns:
            List of stable detection results
        """
        if len(self.detection_history) < min_detections:
            return []
        
        # Group detections by type and check for stability
        stable_results = []
        recent_detections = list(self.detection_history)[-min_detections:]
        
        # Simple stability check: if we have multiple detections of same type, consider stable
        detection_types = {}
        for detection in recent_detections:
            if detection.object_type not in detection_types:
                detection_types[detection.object_type] = []
            detection_types[detection.object_type].append(detection)
        
        # Return detections that appear multiple times
        for object_type, detections in detection_types.items():
            if len(detections) >= 2:  # At least 2 detections of same type
                # Return the most recent detection of this type
                stable_results.append(detections[-1])
        
        return stable_results
    



def main():
    """Main function for person detection."""
    parser = argparse.ArgumentParser(description="Simple Person Detection")
    parser.add_argument("--camera", choices=["auto", "basic", "webcam", "pi_ai"], 
                       default="auto", help="Camera type to use")
    parser.add_argument("--camera-mode", choices=["normal_video", "ai_detection"], 
                       default="ai_detection", help="Camera mode to use (ai_detection for AI processing)")

    args = parser.parse_args()
    
    logger = setup_logging(__name__)
    
    print("=== Simple Person Detection (AI Camera Only) ===")
    print(f"Camera type: {args.camera}")
    print(f"Camera mode: {args.camera_mode}")

    print("Press 'q' to quit, 'space' to take screenshot")
    
    # Initialize servo controller
    try:
        controller = get_servo_controller(ServoControllerType.PCA9685)
        logger.info("Servo controller initialized")
        
        # Set initial servo positions
        print("Setting initial servo positions...")
        controller.set_servo_angle(0, 90)  # Pan center
        time.sleep(1)
        controller.set_servo_angle(1, 80)  # Tilt at 80 degrees
        time.sleep(1)
        print("Servos positioned: Pan=90°, Tilt=80°")
        
    except Exception as e:
        logger.error(f"Failed to initialize servo controller: {e}")
        return
    
    # Initialize person detection system (it will create the camera instance)
    try:
        detector = PersonDetectionSystem(camera_instance=None, camera_mode=args.camera_mode)  # Let PersonDetector create its own camera
        logger.info("Person detection system initialized")
        
        # Get the camera instance from the detector
        camera = detector.person_detector.camera
        if camera is None:
            logger.error("Failed to get camera instance from person detector")
            return
            
        logger.info(f"Camera started: {camera.get_resolution()}")
        print(f"Camera resolution: {camera.get_resolution()}")
        
    except Exception as e:
        logger.error(f"Failed to initialize person detection system: {e}")
        return
    
    # Initialize display manager
    display_manager = DisplayManager("Simple Person Detection")
    print(f"Display method: {display_manager.display_method}")
    
    print("\n=== Detection Loop Started ===")
    print("Person detection with AI camera (NO OPENCV)")
    print("Note: AI model may need people to be clearly visible in the camera view")
    print("If no detections, try moving closer to the camera or adjusting lighting")
    
    frame_count = 0
    
    try:
        while True:
            # Get frame for detection and display
            if hasattr(camera, 'get_optimal_display_frame'):
                frame = camera.get_optimal_display_frame()
            elif hasattr(camera, 'get_detection_frame'):
                frame = camera.get_detection_frame()
            else:
                frame = camera.get_frame()
                
            if frame is None:
                continue
            
            if frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
                continue
            
            frame_count += 1
            
            # Get current servo angles
            current_pan = controller.get_servo_angle(0)
            current_tilt = controller.get_servo_angle(1)
            servo_angles = (current_pan, current_tilt)
            
            # Perform person detection using AI camera
            detections = detector.detect_persons(frame, servo_angles)
            
            # Debug: Print detection info
            if detections:
                print(f"Detected {len(detections)} persons:")
                for i, det in enumerate(detections):
                    print(f"  {i+1}. Person: {det.bbox}, conf:{det.confidence:.2f}, area:{det.area}")
            else:
                # Debug: Print when no detections
                if frame_count % 30 == 0:  # Print every 30 frames to avoid spam
                    print(f"Frame {frame_count}: No persons detected")
            
            # Get stable detections
            stable_detections = detector.get_stable_detections(min_detections=2)
            
            # Draw detection results
            for detection in detections:
                x, y, w, h = detection.bbox
                color = (255, 0, 0)  # Red for persons
                thickness = 1
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
                
                # Add detection info
                info_text = f"Person: {detection.area}px"
                cv2.putText(frame, info_text, (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                # Mark stable detections
                if detection in stable_detections:
                    cv2.circle(frame, detection.center, 8, (0, 255, 255), 2)
            
            # Add status information
            status_text = [
                f"Person Detection",
                f"Persons: {len(detections)}",
                f"Stable: {len(stable_detections)}",
                f"Frame: {frame_count}",
                f"Pan: {current_pan:.1f}° | Tilt: {current_tilt:.1f}°"
            ]
            
            for i, text in enumerate(status_text):
                y_pos = 30 + i * 25
                cv2.putText(frame, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            

            
            # Prepare display data
            display_data = {
                'frame': frame,
                'fps': detector.person_detector.get_detection_fps(),
                'frame_count': frame_count,
                'show_info': True,
                'camera_info': {
                    'type': camera.__class__.__name__,
                    'resolution': camera.get_resolution(),
                    'display_method': display_manager.display_method
                },
                'detection_info': {
                    'persons_detected': len(detections),
                    'stable_detections': len(stable_detections),
                    'detector_type': 'AI Camera Person Detector (NO OPENCV)'
                }
            }
            
            # Show frame
            if not display_manager.show_frame(display_data):
                print("User requested quit")
                break
            
            # Handle key presses
            key = display_manager.get_key()
            if key == ord('q'):
                print("Quit requested")
                break
            elif key == ord(' '):
                filename = f"person_detection_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved: {filename}")
            
            # Log detections periodically
            if frame_count % 60 == 0 and stable_detections:
                logger.info(f"Stable detections: {len(stable_detections)}")
                for detection in stable_detections:
                    logger.info(f"  {detection}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Error in detection loop: {e}")
    
    finally:
        # Cleanup
        print("\nCleaning up...")
        display_manager.close()
        camera.stop()
        controller.shutdown()
        print("Person detection test completed")


if __name__ == "__main__":
    main() 