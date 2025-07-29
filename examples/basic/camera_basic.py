#!/usr/bin/env python3
"""Basic camera capture with automatic display detection.

This example demonstrates the simplest way to use the camera with automatic
display method detection. It works in any environment (headless, with display,
remote desktop, etc.) without manual configuration.
"""

import sys
import os
import time
import cv2
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.vision.camera_selector import get_camera, CameraType
from raspibot.vision.display_manager import DisplayManager


def main():
    """Main function demonstrating basic camera operations."""
    print("=== Basic Camera Capture ===")
    print("This example automatically detects and uses the best display method")
    print("for your current environment (headless, display, remote, etc.)")
    print()
    
    # Initialize display manager with auto-detection
    print("🔍 Detecting display environment...")
    display_manager = DisplayManager(auto_detect=True)
    display_method = display_manager.get_display_method()
    print(f"✓ Using display method: {display_method}")
    
    # Get display handler
    display = display_manager.get_display_handler()
    print(f"✓ Display handler: {display.__class__.__name__}")
    
    # Get the best available camera
    print("\n📹 Initializing camera...")
    camera = get_camera()
    print(f"✓ Using camera: {camera.__class__.__name__}")
    
    try:
        # Initialize camera
        if not camera.start():
            print("❌ Failed to start camera")
            return 1
        
        print("✓ Camera started successfully")
        print(f"  Resolution: {camera.get_resolution()}")
        print(f"  FPS: {camera.get_fps():.1f}")
        print()
        
        # Display camera info
        display.show_info({
            'camera_type': camera.__class__.__name__,
            'resolution': camera.get_resolution(),
            'fps': camera.get_fps(),
            'display_method': display_method
        })
        
        # Capture and display frames
        frame_count = 0
        start_time = time.time()
        
        print("Camera Controls:")
        print("  Press 'q' to quit")
        print("  Press 's' to save screenshot")
        print("  Press 'i' to show/hide info overlay")
        print("  Press 'h' to show display help")
        print()
        
        show_info = True
        
        while True:
            # Capture frame
            frame = camera.get_frame()
            if frame is None:
                print("⚠️  Failed to capture frame")
                continue
            
            frame_count += 1
            
            # Calculate FPS
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            
            # Prepare display data
            display_data = {
                'frame': frame,
                'fps': fps,
                'frame_count': frame_count,
                'show_info': show_info,
                'camera_info': {
                    'type': camera.__class__.__name__,
                    'resolution': camera.get_resolution(),
                    'display_method': display_method
                }
            }
            
            # Display frame
            if not display.show_frame(display_data):
                print("User requested quit")
                break
            
            # Handle key presses (if supported by display method)
            key = display.get_key()
            if key == ord('q'):
                print("User requested quit")
                break
            elif key == ord('s'):
                # Save screenshot
                filename = f"screenshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Screenshot saved: {filename}")
            elif key == ord('i'):
                show_info = not show_info
                print(f"ℹ️  Info overlay: {'ON' if show_info else 'OFF'}")
            elif key == ord('h'):
                display.show_help()
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  Frames captured: {frame_count}")
        print(f"  Total time: {elapsed_time:.1f} seconds")
        print(f"  Average FPS: {fps:.1f}")
        print(f"  Display method: {display_method}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        camera.stop()
        display.close()
        print("✓ Cleanup completed")


if __name__ == "__main__":
    main() 