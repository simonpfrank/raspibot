#!/usr/bin/env python3
"""Demo script for Pi AI Camera with people detection."""

import argparse
import time
import sys
import os
import cv2

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.vision.camera_selector import get_camera, CameraType
from raspibot.vision.detection_models import PersonDetection
from raspibot.utils.logging_config import setup_logging


def draw_detections(frame, detections):
    """Draw detection boxes on frame."""
    for i, detection in enumerate(detections):
        x, y, w, h = detection.bbox
        confidence = detection.confidence
        
        # Draw bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw label
        label = f"Person {i+1}: {confidence:.2f}"
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw center point
        center = detection.center
        cv2.circle(frame, center, 5, (255, 0, 0), -1)
    
    return frame


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="Pi AI Camera People Detection Demo")
    parser.add_argument("--camera", choices=["auto", "webcam", "pi_ai"], 
                       default="auto", help="Camera type to use")
    parser.add_argument("--camera-mode", choices=["normal_video", "ai_detection", "opencv_detection"], 
                       default="ai_detection", help="Camera mode to use")
    parser.add_argument("--duration", type=int, default=30, 
                       help="Demo duration in seconds")
    parser.add_argument("--no-display", action="store_true",
                       help="Run without display (headless mode)")
    
    args = parser.parse_args()
    
    print("Pi AI Camera People Detection Demo")
    print("=" * 40)
    print(f"Camera type: {args.camera}")
    print(f"Camera mode: {args.camera_mode}")
    
    # Setup logging
    logger = setup_logging(__name__)
    
    try:
        # Create camera
        print(f"Creating {args.camera} camera...")
        camera = get_camera(args.camera, camera_mode=args.camera_mode)
        print(f"✓ Camera created: {type(camera).__name__}")
        
        # Get camera info
        if hasattr(camera, 'get_model_info'):
            model_info = camera.get_model_info()
            print(f"  Model: {model_info.get('model_path', 'N/A')}")
            print(f"  Task: {model_info.get('task', 'N/A')}")
            print(f"  Confidence threshold: {model_info.get('confidence_threshold', 'N/A')}")
        
        # Get camera mode info
        if hasattr(camera, 'get_camera_mode_info'):
            camera_mode_info = camera.get_camera_mode_info()
            print(f"  Camera mode: {camera_mode_info.get('camera_mode', 'N/A')}")
            print(f"  Detection resolution: {camera_mode_info.get('detection', {}).get('resolution', 'N/A')}")
            print(f"  Detection format: {camera_mode_info.get('detection', {}).get('format', 'N/A')}")
            print(f"  Display resolution: {camera_mode_info.get('display', {}).get('resolution', 'N/A')}")
            print(f"  Memory per frame: {camera_mode_info.get('memory_mb_per_frame', 'N/A')} MB")
        
        # Start camera
        print("Starting camera...")
        if not camera.start():
            print("✗ Failed to start camera")
            return 1
        
        print("✓ Camera started successfully")
        print(f"  Resolution: {camera.get_resolution()}")
        
        # Demo loop
        print(f"\nRunning demo for {args.duration} seconds...")
        print("Press 'q' to quit early")
        
        start_time = time.time()
        frame_count = 0
        detection_count = 0
        
        while time.time() - start_time < args.duration:
            # Get frame (use detection frame for AI detection mode)
            if args.camera_mode == "ai_detection" and hasattr(camera, 'get_detection_frame'):
                frame = camera.get_detection_frame()
            else:
                frame = camera.get_frame()
                
            if frame is None:
                print("✗ Failed to capture frame")
                continue
            
            frame_count += 1
            
            # Get detections if available
            detections = []
            if hasattr(camera, 'get_detections'):
                detections = camera.get_detections()
                if detections:
                    detection_count += len(detections)
                    print(f"  Frame {frame_count}: {len(detections)} people detected")
            
            # Draw detections
            if detections:
                frame = draw_detections(frame, detections)
            
            # Add info overlay
            fps = camera.get_fps()
            elapsed = time.time() - start_time
            info_text = f"FPS: {fps:.1f} | Frame: {frame_count} | People: {len(detections)} | Time: {elapsed:.1f}s"
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Note: Display is handled by Pi's native preview system
            # The frame is automatically shown via show_preview=True
            # No need for OpenCV display functions
            
            # Small delay
            time.sleep(0.01)
        
        # Calculate statistics
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        avg_detections = detection_count / frame_count if frame_count > 0 else 0
        
        print(f"\nDemo completed!")
        print(f"  Total frames: {frame_count}")
        print(f"  Average FPS: {avg_fps:.1f}")
        print(f"  Total detections: {detection_count}")
        print(f"  Average detections per frame: {avg_detections:.2f}")
        
        # Cleanup
        camera.stop()
        # Note: Pi's native preview is automatically cleaned up
        
        print("✓ Demo completed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        return 0
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 