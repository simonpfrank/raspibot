#!/usr/bin/env python3
"""
Test Face Detection with YuNet DNN Model

Sets tilt to 270° (horizontal) and pan to 90° (center) and runs face detection
without sweeping to test the camera view and YuNet's angular tolerance.
"""

import cv2
import time
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from raspibot.hardware.servo_factory import ServoControllerFactory, ServoControllerType
from raspibot.vision.camera import Camera
from raspibot.vision.face_detector import FaceDetector
from raspibot.utils.logging_config import setup_logging


def main():
    """Main function to test face detection with YuNet."""
    logger = setup_logging(__name__)
    
    print("=== Face Detection Test with YuNet DNN ===")
    print("Press 'q' to quit, 'space' to take screenshot")
    
    # Initialize servo controller
    try:
        controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
        logger.info("Servo controller initialized")
        
        # Set servo positions
        print("Setting servo positions...")
        controller.set_servo_angle(0, 90)  # Pan center
        time.sleep(1)
        controller.set_servo_angle(1, 270)  # Tilt horizontal
        time.sleep(1)
        print("Servos positioned: Pan=90°, Tilt=270° (horizontal)")
        
    except Exception as e:
        logger.error(f"Failed to initialize servo controller: {e}")
        return
    
    # Initialize camera
    try:
        camera = Camera(device_id=0)
        if not camera.start():
            logger.error("Failed to start camera")
            return
        
        logger.info(f"Camera started: {camera.width}x{camera.height}")
        print(f"Camera resolution: {camera.width}x{camera.height}")
        
    except Exception as e:
        logger.error(f"Failed to initialize camera: {e}")
        return
    
    # Initialize YuNet face detector
    try:
        detector = FaceDetector()
        model_info = detector.get_model_info()
        logger.info(f"Face detector initialized: {model_info}")
        print(f"Face detector: {model_info['model_type']}")
        print(f"Confidence threshold: {model_info['confidence_threshold']}")
        
    except Exception as e:
        logger.error(f"Failed to initialize face detector: {e}")
        camera.stop()
        return
    
    # Create display window
    window_name = "Face Detection Test - YuNet DNN"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    
    print("\n=== Detection Loop Started ===")
    print("YuNet provides better angular tolerance than Haar cascades")
    
    frame_count = 0
    try:
        while True:
            # Get frame from camera
            frame = camera.get_frame()
            if frame is None:
                continue
            
            frame_count += 1
            
            # Detect faces with YuNet
            faces = detector.detect_faces(frame)
            
            # Draw face rectangles
            for i, (x, y, w, h) in enumerate(faces):
                # Draw green rectangle for detected faces
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Calculate and draw center point
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
                
                # Add face info text
                area = w * h
                cv2.putText(frame, f"Face {i+1}: {area}px", 
                           (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Add status information to frame
            status_text = [
                f"YuNet DNN Face Detector",
                f"Faces: {len(faces)}",
                f"Frame: {frame_count}",
                f"FPS: {detector.get_detection_fps():.1f}",
                f"Pan: 90° | Tilt: 270° (horizontal)"
            ]
            
            for i, text in enumerate(status_text):
                y_pos = 30 + i * 25
                cv2.putText(frame, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            
            # Show frame
            cv2.imshow(window_name, frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Quit requested")
                break
            elif key == ord(' '):
                # Save screenshot
                filename = f"face_detection_test_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved: {filename}")
            
            # Log face detections periodically
            if frame_count % 30 == 0 and faces:
                largest_face = detector.get_largest_face(faces)
                if largest_face:
                    center = detector.get_face_center(largest_face)
                    area = detector.get_face_area(largest_face)
                    logger.info(f"Largest face at {center}, area: {area}px")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Error in detection loop: {e}")
    
    finally:
        # Cleanup
        print("\nCleaning up...")
        cv2.destroyAllWindows()
        camera.stop()
        controller.shutdown()
        print("Test completed")


if __name__ == "__main__":
    main() 