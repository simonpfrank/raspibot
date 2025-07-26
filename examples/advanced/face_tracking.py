#!/usr/bin/env python3
"""Simple face tracking demo script."""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.core.face_tracking_robot import FaceTrackingRobot


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Face Tracking Robot Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python face_tracking_demo.py                    # Use PCA9685 servo controller
  python face_tracking_demo.py --servo gpio       # Use GPIO servo controller
  python face_tracking_demo.py --camera 1         # Use camera device 1
  python face_tracking_demo.py --servo gpio --camera 1  # GPIO servos with camera 1

Controls:
  Press 'q' in the camera window to quit
  Ctrl+C to force quit

Features:
  - Real-time face detection with OpenCV
  - Automatic servo tracking of stable faces
  - Visual display with face detection boxes
  - Sleep mode after 5 minutes of no faces (with dramatic movement)
  - Wake up when faces detected
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
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Run the face tracking demo."""
    args = parse_arguments()
    
    print("=" * 50)
    print("Face Tracking Robot Demo")
    print("=" * 50)
    print(f"Servo Controller: {args.servo}")
    print(f"Camera Device: {args.camera}")
    print("Press 'q' in the camera window to quit")
    print("Ctrl+C to force quit")
    print("-" * 50)
    
    # Create and start robot
    try:
        print("Initializing robot...")
        robot = FaceTrackingRobot(servo_type=args.servo, camera_device=args.camera)
        
        print("Starting face tracking...")
        print("🤖 Robot is ready! Look for the camera window.")
        print()
        
        # Start the robot (this will block until quit)
        robot.start()
        
        print("Face tracking demo completed successfully!")
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
        print("4. Try different camera device: --camera 1")
        print("5. Try different servo controller: --servo gpio")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 