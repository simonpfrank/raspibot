#!/usr/bin/env python3
"""
Interactive Servo Range Calibration

Allows you to test servo positions by entering angles directly.
You can judge the positions yourself and note the important angles.

Usage: python servo_movement_range.py
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.hardware.servo_selector import get_servo_controller, ServoControllerType
from raspibot.utils.logging_config import setup_logging


def main():
    """Interactive servo calibration with direct angle input."""
    logger = setup_logging(__name__)
    
    print("=== Interactive Servo Range Calibration ===")
    print("Enter angles to test servo positions")
    print("Enter 'q' to quit")
    print("Enter 'info' for current servo info")
    print()
    
    # Initialize servo controller
    try:
        controller = get_servo_controller(ServoControllerType.PCA9685)
        logger.info("PCA9685 servo controller initialized")
        print("✅ PCA9685 servo controller initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize servo controller: {e}")
        print(f"❌ Failed to initialize servo controller: {e}")
        return 1
    
    print("\nServo Channels:")
    print("  Channel 0: Pan servo (left/right)")
    print("  Channel 1: Tilt servo (up/down)")
    print()
    
    # Choose servo to test
    while True:
        try:
            servo_input = input("Which servo to test? (0=pan, 1=tilt, q=quit): ").strip().lower()
            
            if servo_input == 'q':
                break
            
            if servo_input in ['0', '1']:
                channel = int(servo_input)
                servo_name = "Pan" if channel == 0 else "Tilt"
                
                print(f"\n=== Testing {servo_name} Servo (Channel {channel}) ===")
                print("Enter angles (0-359) to test positions")
                print("Useful commands:")
                print("  0-359: Test specific angle")
                print("  'sweep': Quick 0-359 sweep for reference")
                print("  'center': Go to 180° (center)")
                print("  'info': Show current position")
                print("  'back': Return to servo selection")
                print("  'q': Quit")
                print()
                
                # Test this servo
                test_servo(controller, channel, servo_name, logger)
                
            else:
                print("Please enter 0, 1, or q")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    # Cleanup
    try:
        print("\nReturning servos to safe positions...")
        controller.set_servo_angle(0, 90)   # Pan center
        controller.set_servo_angle(1, 200)  # Tilt safe position
        time.sleep(1)
        controller.shutdown()
        print("✅ Cleanup completed")
        
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")
    
    print("Calibration session completed")
    return 0


def test_servo(controller, channel, servo_name, logger):
    """Test a specific servo with angle input."""
    current_angle = controller.get_servo_angle(channel)
    
    while True:
        try:
            user_input = input(f"\n{servo_name} angle (current: {current_angle}°): ").strip().lower()
            
            if user_input == 'q':
                return
            elif user_input == 'back':
                return
            elif user_input == 'center':
                angle = 180
            elif user_input == 'sweep':
                print("Performing 0-359° sweep...")
                for angle in range(0, 360, 30):
                    print(f"  Setting {angle}°...")
                    controller.set_servo_angle(channel, angle)
                    time.sleep(0.5)
                continue
            elif user_input == 'info':
                current_angle = controller.get_servo_angle(channel)
                print(f"Current {servo_name} position: {current_angle}°")
                continue
            else:
                try:
                    angle = float(user_input)
                    if not 0 <= angle <= 359:
                        print("Angle must be between 0 and 359")
                        continue
                except ValueError:
                    print("Please enter a valid angle (0-359), 'sweep', 'center', 'info', 'back', or 'q'")
                    continue
            
            # Move servo to the angle
            print(f"Moving {servo_name} to {angle}°...")
            controller.set_servo_angle(channel, angle)
            current_angle = angle
            
            # Give feedback prompt
            print(f"Servo is now at {angle}°")
            print("Note important positions like:")
            print("  - Minimum movement position")
            print("  - Maximum movement position") 
            print("  - Horizontal/center position")
            
        except KeyboardInterrupt:
            print("\nReturning to servo selection...")
            return
        except Exception as e:
            logger.error(f"Error testing servo: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    sys.exit(main()) 