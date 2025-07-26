    #!/usr/bin/env python3
"""Simple camera capture example.

This example demonstrates basic camera initialization and frame capture.
It's designed for beginners to understand how to work with cameras in the project.
"""

import sys
import os
import cv2
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.vision.camera_selector import get_camera, CameraType


def main():
    """Main function demonstrating basic camera operations."""
    print("=== Simple Camera Capture Example ===")
    print("Press 'q' to quit, 's' to save screenshot")
    
    # Get the best available camera
    camera = get_camera()
    print(f"Using camera: {camera.__class__.__name__}")
    
    try:
        # Initialize camera
        camera.initialize()
        print("Camera initialized successfully")
        
        # Capture and display frames
        frame_count = 0
        start_time = time.time()
        
        while True:
            # Capture frame
            frame = camera.capture_frame()
            if frame is None:
                print("Failed to capture frame")
                continue
            
            frame_count += 1
            
            # Calculate FPS
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            
            # Add FPS text to frame
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow("Camera Capture", frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save screenshot
                filename = f"screenshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved: {filename}")
        
        print(f"Captured {frame_count} frames in {elapsed_time:.1f} seconds")
        print(f"Average FPS: {fps:.1f}")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        camera.cleanup()
        cv2.destroyAllWindows()
        print("Camera cleanup completed")


if __name__ == "__main__":
    main() 