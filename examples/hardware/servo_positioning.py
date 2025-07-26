#!/usr/bin/env python3
"""Servo positioning example.

This example demonstrates how to position servos using the project's servo abstraction layer.
It provides interactive servo positioning with proper error handling.
"""

import sys
import os
import time
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.hardware.servo_selector import get_servo_controller, ServoControllerType
from raspibot.config.hardware_config import (
    SERVO_PAN_CHANNEL, SERVO_TILT_CHANNEL,
    SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE, SERVO_PAN_CENTER,
    SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE, SERVO_TILT_CENTER
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Servo Positioning Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python servo_positioning.py                    # Use PCA9685 servo controller
  python servo_positioning.py --servo gpio       # Use GPIO servo controller
  python servo_positioning.py --pan 45 --tilt 300  # Set specific angles
  python servo_positioning.py --interactive      # Interactive mode
        """
    )
    parser.add_argument(
        '--servo', 
        choices=['pca9685', 'gpio'], 
        default='pca9685',
        help='Servo controller type (default: pca9685)'
    )
    parser.add_argument(
        '--pan',
        type=int,
        help=f'Pan angle ({SERVO_PAN_MIN_ANGLE}-{SERVO_PAN_MAX_ANGLE} degrees)'
    )
    parser.add_argument(
        '--tilt',
        type=int,
        help=f'Tilt angle ({SERVO_TILT_MIN_ANGLE}-{SERVO_TILT_MAX_ANGLE} degrees)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    return parser.parse_args()


def interactive_mode(servo_controller):
    """Run interactive servo positioning."""
    print("=== Interactive Servo Positioning ===")
    print("Commands:")
    print(f"  pan <angle>    - Set pan angle ({SERVO_PAN_MIN_ANGLE}-{SERVO_PAN_MAX_ANGLE})")
    print(f"  tilt <angle>   - Set tilt angle ({SERVO_TILT_MIN_ANGLE}-{SERVO_TILT_MAX_ANGLE})")
    print("  center         - Center both servos")
    print("  sweep          - Run sweep pattern")
    print("  quit           - Exit")
    print()
    
    while True:
        try:
            command = input("Enter command: ").strip().lower().split()
            if not command:
                continue
                
            if command[0] == 'quit':
                break
            elif command[0] == 'center':
                print("Centering servos...")
                servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER)
                servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER)
                print("Servos centered")
            elif command[0] == 'sweep':
                print("Running sweep pattern...")
                # Pan sweep
                for angle in range(SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE + 1, 20):
                    servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, angle)
                    time.sleep(0.5)
                servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER)
                time.sleep(1)
                # Tilt sweep
                for angle in range(SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE + 1, 15):
                    servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, angle)
                    time.sleep(0.5)
                servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER)
                print("Sweep completed")
            elif command[0] == 'pan' and len(command) > 1:
                try:
                    angle = int(command[1])
                    if SERVO_PAN_MIN_ANGLE <= angle <= SERVO_PAN_MAX_ANGLE:
                        print(f"Setting pan to {angle}°")
                        servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, angle)
                    else:
                        print(f"Pan angle must be between {SERVO_PAN_MIN_ANGLE} and {SERVO_PAN_MAX_ANGLE} degrees")
                except ValueError:
                    print("Invalid pan angle")
            elif command[0] == 'tilt' and len(command) > 1:
                try:
                    angle = int(command[1])
                    if SERVO_TILT_MIN_ANGLE <= angle <= SERVO_TILT_MAX_ANGLE:
                        print(f"Setting tilt to {angle}°")
                        servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, angle)
                    else:
                        print(f"Tilt angle must be between {SERVO_TILT_MIN_ANGLE} and {SERVO_TILT_MAX_ANGLE} degrees")
                except ValueError:
                    print("Invalid tilt angle")
            else:
                print("Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function for servo positioning."""
    args = parse_arguments()
    
    print("=== Servo Positioning Example ===")
    print(f"Using {args.servo} servo controller")
    
    # Get servo controller
    servo_type = ServoControllerType.GPIO if args.servo == 'gpio' else ServoControllerType.PCA9685
    servo_controller = get_servo_controller(servo_type)
    
    try:
        print("Servo controller initialized successfully")
        
        if args.interactive:
            interactive_mode(servo_controller)
        else:
            # Set specific angles if provided
            if args.pan is not None:
                if SERVO_PAN_MIN_ANGLE <= args.pan <= SERVO_PAN_MAX_ANGLE:
                    print(f"Setting pan to {args.pan}°")
                    servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, args.pan)
                else:
                    print(f"Pan angle must be between {SERVO_PAN_MIN_ANGLE} and {SERVO_PAN_MAX_ANGLE} degrees")
                    return
            
            if args.tilt is not None:
                if SERVO_TILT_MIN_ANGLE <= args.tilt <= SERVO_TILT_MAX_ANGLE:
                    print(f"Setting tilt to {args.tilt}°")
                    servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, args.tilt)
                else:
                    print(f"Tilt angle must be between {SERVO_TILT_MIN_ANGLE} and {SERVO_TILT_MAX_ANGLE} degrees")
                    return
            
            # If no specific angles, center servos
            if args.pan is None and args.tilt is None:
                print("Centering servos...")
                servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER)
                servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER)
                print("Servos centered")
            
            # Wait a moment to see the movement
            time.sleep(2)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        servo_controller.shutdown()
        print("Servo controller shutdown completed")


if __name__ == "__main__":
    main()
