#!/usr/bin/env python3
"""
Basic camera capture and display example.

This example demonstrates basic camera operations:
- Initialize camera
- Capture frames
- Display frames in a window
- Save pictures on command
"""

import argparse
import time
import sys
import os
import cv2

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.vision.camera_selector import get_camera, get_available_cameras, get_recommended_camera
from raspibot.utils.logging_config import setup_logging


def main():
    """Main camera capture function."""
    parser = argparse.ArgumentParser(description="Basic camera capture and display")
    parser.add_argument("--camera", choices=["auto", "basic", "webcam", "pi_ai"], 
                       default="auto", help="Camera type to use")
    parser.add_argument("--camera-mode", choices=["normal_video", "ai_detection", "opencv_detection"], 
                       default="normal_video", help="Camera mode to use")
    parser.add_argument("--width", type=int, default=1280, help="Camera width")
    parser.add_argument("--height", type=int, default=720, help="Camera height")
    parser.add_argument("--save-dir", type=str, default="./captures", 
                       help="Directory to save captured images")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(__name__)
    
    print("Basic Camera Capture Example")
    print("=" * 40)
    print(f"Camera type: {args.camera}")
    print(f"Camera mode: {args.camera_mode}")
    print(f"Resolution: {args.width}x{args.height}")
    print()
    
    # Check available cameras
    available = get_available_cameras()
    print(f"Available cameras: {[c.value for c in available]}")
    recommended = get_recommended_camera()
    print(f"Recommended camera: {recommended.value}")
    print()
    
    # Create save directory
    os.makedirs(args.save_dir, exist_ok=True)
    
    # Create camera
    try:
        print("Creating camera...")
        camera = get_camera(args.camera, width=args.width, height=args.height, camera_mode=args.camera_mode)
        
        # Start camera
        print("Starting camera...")
        if not camera.start():
            print("❌ Failed to start camera")
            return 1
        
        print("✓ Camera started successfully")
        print(f"  Resolution: {camera.get_resolution()}")
        print()
        
        # Display instructions
        print("Camera Controls:")
        print("  Press 's' to save current frame")
        print("  Press 'q' to quit")
        print("  Press any other key to capture and display frame")
        print()
        
        frame_count = 0
        saved_count = 0
        
        while True:
            # Get frame from camera
            frame = camera.get_frame()
            if frame is None:
                print("No frame received")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            
            # Display the frame
            cv2.imshow('Camera Feed', frame)
            
            # Wait for key press
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("Quitting...")
                break
            elif key == ord('s'):
                # Save current frame
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"capture_{timestamp}_{saved_count:03d}.jpg"
                filepath = os.path.join(args.save_dir, filename)
                
                cv2.imwrite(filepath, frame)
                saved_count += 1
                print(f"✓ Saved frame to {filepath}")
            
            # Update FPS display every 30 frames
            if frame_count % 30 == 0:
                fps = camera.get_fps()
                print(f"FPS: {fps:.1f}, Frames: {frame_count}, Saved: {saved_count}")
        
        print(f"\nSession summary:")
        print(f"  Total frames processed: {frame_count}")
        print(f"  Images saved: {saved_count}")
        print(f"  Final FPS: {camera.get_fps():.1f}")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Camera error: {e}")
        print(f"❌ Camera error: {e}")
        return 1
    finally:
        # Clean up
        try:
            camera.stop()
            cv2.destroyAllWindows()
            print("✓ Camera stopped and cleaned up")
        except:
            pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 