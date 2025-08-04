#!/usr/bin/env python3
"""Search pattern demo script.

This script demonstrates the systematic raster scan search pattern
for face detection when no faces are detected.
"""

import sys
import os
import argparse
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.core.face_tracking_robot import FaceTrackingRobot
from raspibot.vision.search_pattern import SearchDirection


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Search Pattern Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search_pattern_demo.py                    # Use default settings
  python search_pattern_demo.py --servo gpio       # Use GPIO servo controller
  python search_pattern_demo.py --direction up     # Start search from bottom
  python search_pattern_demo.py --interval 15      # Search every 15 seconds

Controls:
  Press 'q' in the camera window to quit
  Ctrl+C to force quit

Features:
  - Systematic raster scan search pattern
  - Slow, smooth movements for thorough coverage
  - Automatic search when no faces detected
  - Visual feedback showing search progress
  - Configurable search parameters
        """
    )
    
    parser.add_argument(
        '--servo', 
        choices=['pca9685', 'gpio'], 
        default='pca9685',
        help='Servo controller type (default: pca9685)'
    )
    
    parser.add_argument(
        '--camera', 
        type=int, 
        default=0,
        help='Camera device ID (default: 0)'
    )
    
    parser.add_argument(
        '--direction',
        choices=['down', 'up'],
        default='down',
        help='Search direction: start from top (down) or bottom (up) (default: down)'
    )
    
    parser.add_argument(
        '--interval',
        type=float,
        default=30.0,
        help='Search interval in seconds when no faces detected (default: 30)'
    )
    
    parser.add_argument(
        '--pan-steps',
        type=int,
        default=8,
        help='Number of pan steps per tilt level (default: 8)'
    )
    
    parser.add_argument(
        '--tilt-steps',
        type=int,
        default=6,
        help='Number of tilt levels to scan (default: 6)'
    )
    
    parser.add_argument(
        '--speed',
        type=float,
        default=0.3,
        help='Movement speed for search (0.1-1.0, default: 0.3)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Run the search pattern demo."""
    args = parse_arguments()
    
    print("=" * 60)
    print("Search Pattern Demo")
    print("=" * 60)
    print(f"Servo Controller: {args.servo}")
    print(f"Camera Device: {args.camera}")
    print(f"Search Direction: {args.direction}")
    print(f"Search Interval: {args.interval} seconds")
    print(f"Pan Steps: {args.pan_steps}")
    print(f"Tilt Steps: {args.tilt_steps}")
    print(f"Movement Speed: {args.speed}")
    print("Press 'q' in the camera window to quit")
    print("Ctrl+C to force quit")
    print("-" * 60)
    
    # Create and start robot
    try:
        print("Initializing robot...")
        robot = FaceTrackingRobot(servo_type=args.servo, camera_device=args.camera)
        
        # Configure search parameters
        print("Configuring search pattern...")
        robot.set_search_interval(args.interval)
        
        # Get search pattern and configure it
        search_pattern = robot.face_tracker.search_pattern
        if search_pattern:
            direction = SearchDirection.UP_FIRST if args.direction == 'up' else SearchDirection.DOWN_FIRST
            search_pattern.set_search_parameters(
                pan_steps=args.pan_steps,
                tilt_steps=args.tilt_steps,
                movement_speed=args.speed,
                direction=direction
            )
            print(f"Search pattern configured: {args.pan_steps}x{args.tilt_steps} grid")
        
        print("Starting face tracking with search pattern...")
        print("🤖 Robot is ready! Look for the camera window.")
        print("🔍 Search pattern will activate when no faces are detected.")
        print()
        
        # Start the robot (this will block until quit)
        robot.start()
        
        print("Search pattern demo completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check camera connection and permissions")
        print("2. Verify servo controller is connected")
        print("3. Ensure OpenCV is installed: pip install opencv-python")
        print("4. Check servo configuration in hardware_config.py")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 