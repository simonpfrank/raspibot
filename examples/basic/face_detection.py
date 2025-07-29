#!/usr/bin/env python3
"""
Test Face Detection with AI Camera

Sets tilt to 270° (horizontal) and pan to 90° (center) and runs face detection
using AI Camera's hardware-accelerated person detection.
"""

import cv2
import time
import sys
import os
import argparse

# Set display for headless operation
os.environ['DISPLAY'] = ':0'
#os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '1'

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from raspibot.hardware.servo_selector import get_servo_controller, ServoControllerType
from raspibot.vision.camera_selector import get_camera, CameraType
from raspibot.vision.face_detector import FaceDetector
from raspibot.vision.display_manager import DisplayManager
from raspibot.utils.logging_config import setup_logging


def main():
    """Main function to test face detection with AI Camera."""
    parser = argparse.ArgumentParser(description="Face Detection Test with AI Camera")
    parser.add_argument("--camera", choices=["auto", "basic", "webcam", "pi_ai"], 
                       default="auto", help="Camera type to use")
    parser.add_argument("--camera-mode", choices=["normal_video", "ai_detection", "opencv_detection"], 
                       default="opencv_detection", help="Camera mode to use")
    args = parser.parse_args()
    
    logger = setup_logging(__name__)
    
    print("=== Face Detection Test with AI Camera ===")
    print(f"Camera type: {args.camera}")
    print(f"Camera mode: {args.camera_mode}")
    print("Press 'q' to quit, 'space' to take screenshot")
    
    # Initialize servo controller
    try:
        controller = get_servo_controller(ServoControllerType.PCA9685)
        logger.info("Servo controller initialized")
        
        # Set servo positions
        print("Setting servo positions...")
        controller.set_servo_angle(0, 90)  # Pan center
        time.sleep(1)
        controller.set_servo_angle(1, 90)  # Tilt horizontal
        time.sleep(1)
        print("Servos positioned: Pan=90°, Tilt=90° (horizontal)")
        
    except Exception as e:
        logger.error(f"Failed to initialize servo controller: {e}")
        return
    
    # Initialize camera
    try:
        # Only pass camera_mode to cameras that support it
        if args.camera in ["pi_ai", "basic"]:
            camera = get_camera(args.camera, camera_mode=args.camera_mode)
        else:
            camera = get_camera(args.camera)
            
        if not camera.start():
            logger.error("Failed to start camera")
            return
        
        # Get camera mode info if available
        try:
            camera_info = camera.get_camera_mode_info()
            print(f"Camera mode info: {camera_info}")
        except AttributeError:
            camera_info = "Not available"
            print("Camera mode info: Not available")
            
        logger.info(f"Camera started: {camera.get_resolution()}")
        print(f"Camera resolution: {camera.get_resolution()}")
        
    except Exception as e:
        logger.error(f"Failed to initialize camera: {e}")
        return
    
    # Initialize face detector with camera instance for AI detection
    try:
        # Pass camera instance to enable AI Camera detection
        detector = FaceDetector(camera_instance=camera, detection_method="ai_camera")
        model_info = detector.get_model_info()
        logger.info(f"Face detector initialized: {model_info}")
        print(f"Face detector: {model_info['model_type']}")
        print(f"Detection method: {model_info['detection_method']}")
        print(f"Confidence threshold: {model_info['confidence_threshold']}")
        
    except Exception as e:
        logger.error(f"Failed to initialize face detector: {e}")
        camera.stop()
        return
    
    # Initialize display manager for automatic environment detection
    display_manager = DisplayManager("Face Detection Test - AI Camera")
    print(f"Display method: {display_manager.display_method}")
    print(f"Display handler: {display_manager.display_handler.__class__.__name__}")
    
    print("\n=== Detection Loop Started ===")
    print("AI Camera provides hardware-accelerated person detection")
    
    frame_count = 0
    try:
        while True:
            # Get frame from camera (use optimal display frame for proper sizing)
            if hasattr(camera, 'get_optimal_display_frame'):
                frame = camera.get_optimal_display_frame()
            elif hasattr(camera, 'get_detection_frame'):
                frame = camera.get_detection_frame()
            else:
                frame = camera.get_frame()
                
            if frame is None:
                continue
            
            # Ensure we have a complete frame
            if frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
                continue
            
            frame_count += 1
            
            # Detect faces with YuNet or get detections from AI camera
            faces = detector.detect_faces(frame)

            # --- NEW: If using AI camera, try to get raw detections and draw them ---
            ai_detections = None
            if hasattr(camera, 'get_detections'):
                try:
                    ai_detections = camera.get_detections()
                except Exception as e:
                    logger.warning(f"Could not get AI camera detections: {e}")

            if ai_detections:
                print(f"[DEBUG] AI camera returned {len(ai_detections)} detections:")
                display_height, display_width = frame.shape[:2]
                print(f"[DEBUG] Display size: {display_width}x{display_height}")
                
                # Use the same scale factors as the AI camera (1920x1080)
                # The AI camera processes at 1920x1080 but we display at 1280x720
                ai_display_width = 1920
                ai_display_height = 1080
                model_input_width = 320
                model_input_height = 320
                
                # Scale from model input (320x320) to AI display (1920x1080)
                scale_x = ai_display_width / model_input_width
                scale_y = ai_display_height / model_input_height
                
                # Then scale from AI display to actual display
                display_scale_x = display_width / ai_display_width
                display_scale_y = display_height / ai_display_height
                
                # Final scale factors
                final_scale_x = scale_x * display_scale_x
                final_scale_y = scale_y * display_scale_y
                
                print(f"[DEBUG] AI display: {ai_display_width}x{ai_display_height}")
                print(f"[DEBUG] Model input: {model_input_width}x{model_input_height}")
                print(f"[DEBUG] AI scale factors: x={scale_x}, y={scale_y}")
                print(f"[DEBUG] Display scale factors: x={display_scale_x}, y={display_scale_y}")
                print(f"[DEBUG] Final scale factors: x={final_scale_x}, y={final_scale_y}")
                
                # Draw multiple test rectangles to confirm drawing works
                cv2.rectangle(frame, (10, 10), (100, 100), (255, 0, 0), 3)  # Blue
                cv2.rectangle(frame, (200, 200), (300, 300), (0, 255, 0), 3)  # Green
                cv2.rectangle(frame, (400, 400), (500, 500), (0, 0, 255), 3)  # Red
                
                for i, det in enumerate(ai_detections):
                    bbox = getattr(det, 'bbox', None) or getattr(det, 'box', None)
                    category = getattr(det, 'category', 'person')
                    conf = getattr(det, 'confidence', getattr(det, 'conf', None))
                    if bbox is not None:
                        print(f"  RAW bbox for detection {i}: {bbox}")
                        # Treat as (x, y, w, h) in model input pixels
                        x, y, w, h = bbox
                        x1 = int(x * final_scale_x)
                        y1 = int(y * final_scale_y)
                        x2 = int((x + w) * final_scale_x)
                        y2 = int((y + h) * final_scale_y)
                        
                        # Ensure minimum size for visibility
                        min_size = 50
                        if (x2 - x1) < min_size:
                            x2 = x1 + min_size
                        if (y2 - y1) < min_size:
                            y2 = y1 + min_size
                        
                        # Ensure coordinates are within frame bounds
                        x1 = max(0, min(x1, display_width - 1))
                        y1 = max(0, min(y1, display_height - 1))
                        x2 = max(x1 + 1, min(x2, display_width))
                        y2 = max(y1 + 1, min(y2, display_height))
                        
                        label = f"{category}"
                        if conf is not None:
                            label += f" ({conf:.2f})"
                        print(f"  Detection {i}: {label} bbox=({x1}, {y1}, {x2}, {y2}) size=({x2-x1}x{y2-y1})")
                        
                        # Draw a very thick, bright rectangle
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 8)  # Bright yellow, very thick
                        
                        # Draw label with background
                        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                        overlay = frame.copy()
                        cv2.rectangle(overlay, (x1, max(0, y1 - th - 4)), (x1 + tw + 4, y1), (255, 255, 255), cv2.FILLED)
                        alpha = 0.4
                        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
                        cv2.putText(frame, label, (x1 + 2, max(0, y1 - 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Draw a large test rectangle to show scaling works
                test_x1 = int(50 * final_scale_x)
                test_y1 = int(50 * final_scale_y)
                test_x2 = int(150 * final_scale_x)
                test_y2 = int(150 * final_scale_y)
                cv2.rectangle(frame, (test_x1, test_y1), (test_x2, test_y2), (255, 255, 0), 5)  # Cyan
                print(f"[DEBUG] Test rectangle: ({test_x1}, {test_y1}) to ({test_x2}, {test_y2})")
            else:
                print("[DEBUG] No AI camera detections returned or not available.")
                # Draw test rectangles even when no detections
                cv2.rectangle(frame, (10, 10), (100, 100), (255, 0, 0), 3)  # Blue
                cv2.rectangle(frame, (200, 200), (300, 300), (0, 255, 0), 3)  # Green

            # Draw face rectangles (as before)
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
                f"AI Camera Face Detector",
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
            
            # Save image only when faces are detected (once per detection)
            if faces and not hasattr(main, 'face_detected_this_session'):
                filename = f"face_detected_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"🎯 Face detected! Screenshot saved: {filename}")
                main.face_detected_this_session = True
            
            # Prepare display data
            display_data = {
                'frame': frame,
                'fps': detector.get_detection_fps(),
                'frame_count': frame_count,
                'show_info': True,
                'camera_info': {
                    'type': camera.__class__.__name__,
                    'resolution': camera.get_resolution(),
                    'display_method': display_manager.display_method
                },
                'detection_info': {
                    'faces_detected': len(faces),
                    'detector_type': 'AI Camera',
                    'confidence_threshold': detector.get_model_info()['confidence_threshold']
                }
            }
            
            # Show frame using display manager
            if not display_manager.show_frame(display_data):
                print("User requested quit")
                break
            
            # Handle key presses
            key = display_manager.get_key()
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
        display_manager.close()
        camera.stop()
        controller.shutdown()
        print("Test completed")


if __name__ == "__main__":
    main() 