#!/usr/bin/env python3
"""Advanced camera capture with manual display control.

This example demonstrates advanced camera features with manual display
mode selection and configuration options.
"""

import sys
import os
import time
import cv2
import numpy as np
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.hardware.cameras.camera_selector import get_camera, CameraType
from raspibot.vision.display_manager import DisplayManager


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Advanced camera capture example")
    
    parser.add_argument(
        '--camera', '-c',
        type=str,
        default='auto',
        choices=['auto', 'pi_ai', 'basic', 'webcam'],
        help='Camera type to use (default: auto)'
    )
    
    parser.add_argument(
        '--display-mode', '-d',
        type=str,
        default='auto',
        choices=['auto', 'connected_screen', 'raspberry_connect', 'headless'],
        help='Display mode to use (default: auto)'
    )
    
    parser.add_argument(
        '--resolution', '-r',
        type=str,
        default='1280x720',
        help='Camera resolution (default: 1280x720)'
    )
    
    parser.add_argument(
        '--fps', '-f',
        type=int,
        default=30,
        help='Target FPS (default: 30)'
    )
    
    parser.add_argument(
        '--duration', '-t',
        type=int,
        default=0,
        help='Recording duration in seconds (0 = unlimited, default: 0)'
    )
    
    parser.add_argument(
        '--save-frames', '-s',
        action='store_true',
        help='Save frames to disk'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='captured_frames',
        help='Output directory for saved frames (default: captured_frames)'
    )
    
    return parser.parse_args()


def setup_output_directory(output_dir: str) -> str:
    """Set up output directory for saved frames."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created output directory: {output_dir}")
    return output_dir


def save_frame(frame: np.ndarray, output_dir: str, frame_count: int) -> str:
    """Save frame to disk."""
    filename = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
    cv2.imwrite(filename, frame)
    return filename


def main():
    """Main function demonstrating advanced camera operations."""
    args = parse_arguments()
    
    print("=== Advanced Camera Capture ===")
    print("This example demonstrates advanced camera features with manual control")
    print()
    
    # Parse resolution
    try:
        width, height = map(int, args.resolution.split('x'))
        resolution = (width, height)
    except ValueError:
        print(f"❌ Invalid resolution format: {args.resolution}")
        print("  Use format: WIDTHxHEIGHT (e.g., 1280x720)")
        return 1
    
    # Initialize display manager
    print("🔍 Setting up display...")
    if args.display_mode == 'auto':
        display_manager = DisplayManager(auto_detect=True)
    else:
        display_manager = DisplayManager(auto_detect=False, mode=args.display_mode)
    
    display_method = display_manager.get_display_method()
    print(f"✓ Using display method: {display_method}")
    
    # Get display handler
    display = display_manager.get_display_handler()
    print(f"✓ Display handler: {display.__class__.__name__}")
    
    # Set up output directory if saving frames
    output_dir = None
    if args.save_frames:
        output_dir = setup_output_directory(args.output_dir)
    
    # Get camera
    print(f"\n📹 Initializing camera ({args.camera})...")
    if args.camera == 'auto':
        camera = get_camera()
    else:
        camera = get_camera(args.camera)
    
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
            'display_method': display_method,
            'target_fps': args.fps,
            'duration': args.duration if args.duration > 0 else 'unlimited',
            'save_frames': args.save_frames
        })
        
        # Capture and display frames
        frame_count = 0
        start_time = time.time()
        last_fps_time = start_time
        
        print("Advanced Camera Controls:")
        print("  Press 'q' to quit")
        print("  Press 's' to save current frame")
        print("  Press 'i' to show/hide info overlay")
        print("  Press 'h' to show display help")
        print("  Press 'p' to pause/resume")
        print()
        
        show_info = True
        paused = False
        
        while True:
            # Check duration limit
            if args.duration > 0 and time.time() - start_time >= args.duration:
                print(f"⏰ Recording duration ({args.duration}s) reached")
                break
            
            # Handle pause
            if paused:
                time.sleep(0.1)
                continue
            
            # Capture frame
            frame = camera.get_frame()
            if frame is None:
                print("⚠️  Failed to capture frame")
                continue
            
            frame_count += 1
            
            # Calculate FPS
            current_time = time.time()
            elapsed_time = current_time - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            
            # Save frame if requested
            if args.save_frames:
                filename = save_frame(frame, output_dir, frame_count)
                if frame_count % 30 == 0:  # Log every 30 frames
                    print(f"💾 Saved frame: {filename}")
            
            # Prepare display data
            display_data = {
                'frame': frame,
                'fps': fps,
                'frame_count': frame_count,
                'show_info': show_info,
                'camera_info': {
                    'type': camera.__class__.__name__,
                    'resolution': camera.get_resolution(),
                    'display_method': display_method,
                    'target_fps': args.fps,
                    'duration': args.duration if args.duration > 0 else 'unlimited',
                    'save_frames': args.save_frames,
                    'paused': paused
                }
            }
            
            # Display frame
            if not display.show_frame(display_data):
                print("User requested quit")
                break
            
            # Handle key presses
            key = display.get_key()
            if key == ord('q'):
                print("User requested quit")
                break
            elif key == ord('s'):
                # Save current frame
                filename = f"manual_screenshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Manual screenshot saved: {filename}")
            elif key == ord('i'):
                show_info = not show_info
                print(f"ℹ️  Info overlay: {'ON' if show_info else 'OFF'}")
            elif key == ord('h'):
                display.show_help()
            elif key == ord('p'):
                paused = not paused
                print(f"⏸️  {'Paused' if paused else 'Resumed'}")
            
            # FPS limiting
            if args.fps > 0:
                target_frame_time = 1.0 / args.fps
                actual_frame_time = current_time - last_fps_time
                if actual_frame_time < target_frame_time:
                    time.sleep(target_frame_time - actual_frame_time)
                last_fps_time = time.time()
        
        # Summary
        print(f"\n📊 Advanced Capture Summary:")
        print(f"  Frames captured: {frame_count}")
        print(f"  Total time: {elapsed_time:.1f} seconds")
        print(f"  Average FPS: {fps:.1f}")
        print(f"  Target FPS: {args.fps}")
        print(f"  Display method: {display_method}")
        if args.save_frames:
            print(f"  Frames saved to: {output_dir}")
        
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