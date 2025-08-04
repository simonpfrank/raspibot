#!/usr/bin/env python3
"""Simple webcam picture capture script, using no classes just open cv"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import from raspibot
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from raspibot.vision.camera_selector import get_camera, CameraType


def main():
    """Take a picture with webcam and save it."""
    print("Starting webcam picture capture...")
    
    try:
        # Create webcam instance
        camera = get_camera(CameraType.WEBCAM)
        print("Webcam initialized successfully")
        
        # Start the camera
        camera.start()
        print("Camera started")
        
        # Capture a frame
        print("Capturing image...")
        frame = camera.get_frame()
        
        if frame is not None:
            # Save the image
            import cv2
            filename = "image1.jpg"
            cv2.imwrite(filename, frame)
            print(f"Image saved as {filename}")
        else:
            print("Failed to capture frame")
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean up
        try:
            camera.stop()
            print("Camera stopped")
        except:
            pass


if __name__ == "__main__":
    main() 