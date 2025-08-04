#!/usr/bin/env python3
"""Interactive servo control example.

This example provides both preset movement patterns and individual servo control.
It allows you to choose between preset patterns or control individual servos by
channel/pin and angle with smooth or direct movement options.
"""

import sys
import os
import time
import argparse

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.hardware.servos.servo_selector import get_servo_controller, ServoControllerType
from raspibot.settings.config import (
    SERVO_PAN_CHANNEL, SERVO_TILT_CHANNEL,
    SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE, SERVO_PAN_CENTER,
    SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE, SERVO_TILT_CENTER
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Interactive Servo Control Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python servo_control.py                    # Use PCA9685 servo controller
  python servo_control.py --servo gpio       # Use GPIO servo controller
  python servo_control.py --pattern sweep    # Run sweep pattern and exit
        """
    )
    parser.add_argument(
        '--servo', 
        choices=['pca9685', 'gpio'], 
        default='pca9685',
        help='Servo controller type (default: pca9685)'
    )
    parser.add_argument(
        '--pattern',
        choices=['sweep', 'center', 'wave', 'test'],
        help='Run specific pattern and exit (no interactive mode)'
    )
    return parser.parse_args()


def run_sweep_pattern(servo_controller):
    """Run a sweep pattern."""
    print("Running sweep pattern...")
    
    # Sweep pan servo
    print("Sweeping pan servo...")
    for angle in range(SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE + 1, 10):
        servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, angle)
        time.sleep(0.5)
    
    # Return to center
    servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER)
    time.sleep(1)
    
    # Sweep tilt servo
    print("Sweeping tilt servo...")
    for angle in range(SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE + 1, 10):
        servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, angle)
        time.sleep(0.5)
    
    # Return to center
    servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER)
    print("Sweep pattern completed")


def run_wave_pattern(servo_controller):
    """Run a wave pattern."""
    print("Running wave pattern...")
    
    # Wave pattern - small movements around center
    for i in range(5):
        # Pan wave
        servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER - 20)
        time.sleep(0.3)
        servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER + 20)
        time.sleep(0.3)
        servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER)
        time.sleep(0.3)
        
        # Tilt wave
        servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER - 15)
        time.sleep(0.3)
        servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER + 15)
        time.sleep(0.3)
        servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER)
        time.sleep(0.3)
    
    print("Wave pattern completed")


def run_test_pattern(servo_controller):
    """Run a test pattern with user interaction."""
    print("Running test pattern...")
    print("Press Enter to move to next position, 'q' to quit")
    
    test_positions = [
        (SERVO_PAN_CHANNEL, SERVO_PAN_CENTER, "Center"),
        (SERVO_PAN_CHANNEL, SERVO_PAN_MIN_ANGLE, "Left"),
        (SERVO_PAN_CHANNEL, SERVO_PAN_MAX_ANGLE, "Right"),
        (SERVO_TILT_CHANNEL, SERVO_TILT_MIN_ANGLE, "Up"),
        (SERVO_TILT_CHANNEL, SERVO_TILT_MAX_ANGLE, "Down"),
        (SERVO_PAN_CHANNEL, SERVO_PAN_CENTER, "Center"),
        (SERVO_TILT_CHANNEL, SERVO_TILT_CENTER, "Center")
    ]
    
    for channel, angle, description in test_positions:
        print(f"Moving to {description} (Channel {channel}: {angle}°)")
        servo_controller.set_servo_angle(channel, angle)
        
        user_input = input("Press Enter to continue, 'q' to quit: ").strip().lower()
        if user_input == 'q':
            break
    
    print("Test pattern completed")


def center_servos(servo_controller):
    """Center all servos."""
    print("Centering servos...")
    servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER)
    servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER)
    print("Servos centered")


def individual_servo_control(servo_controller):
    """Interactive individual servo control."""
    print("\n=== Individual Servo Control ===")
    print("Format: <channel> <angle> [smooth]")
    print("Examples:")
    print("  0 90        - Move channel 0 to 90° (direct)")
    print("  1 200 smooth - Move channel 1 to 200° (smooth)")
    print("  q           - Quit individual control")
    print("  back        - Return to main menu")
    print("Note: Servos will stay in their final positions")
    print()
    
    available_channels = servo_controller.get_available_channels()
    print(f"Available channels: {available_channels}")
    
    while True:
        try:
            command = input("Servo control> ").strip().lower()
            
            if command == 'q':
                return 'quit'
            elif command == 'back':
                return 'back'
            elif not command:
                continue
            
            # Parse command
            parts = command.split()
            if len(parts) < 2:
                print("Usage: <channel> <angle> [smooth]")
                continue
            
            try:
                channel = int(parts[0])
                angle = float(parts[1])
                smooth = len(parts) > 2 and parts[2] == 'smooth'
            except ValueError:
                print("Invalid channel or angle")
                continue
            
            # Validate channel
            if channel not in available_channels:
                print(f"Channel {channel} not available. Available: {available_channels}")
                continue
            
            # Validate angle based on channel
            if channel == SERVO_PAN_CHANNEL:
                min_angle, max_angle = SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE
            elif channel == SERVO_TILT_CHANNEL:
                min_angle, max_angle = SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE
            else:
                min_angle, max_angle = 0, 270  # Default range for other channels
            
            if not min_angle <= angle <= max_angle:
                print(f"Angle {angle}° out of range for channel {channel} ({min_angle}°-{max_angle}°)")
                continue
            
            # Move servo
            if smooth:
                print(f"Moving channel {channel} smoothly to {angle}°...")
                servo_controller.smooth_move_to_angle(channel, angle, speed=0.8)
            else:
                print(f"Moving channel {channel} to {angle}°...")
                servo_controller.set_servo_angle(channel, angle)
            
            # Show current angle
            current_angle = servo_controller.get_servo_angle(channel)
            print(f"Channel {channel} now at {current_angle}°")
            
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            return 'back'
        except Exception as e:
            print(f"Error: {e}")


def show_main_menu():
    """Show the main menu."""
    print("\n=== Servo Control Menu ===")
    print("1. Sweep Pattern")
    print("2. Wave Pattern") 
    print("3. Test Pattern")
    print("4. Center Servos")
    print("5. Individual Servo Control")
    print("6. Quit")
    print()


def main():
    """Main function for interactive servo control."""
    args = parse_arguments()
    
    print("=== Interactive Servo Control Example ===")
    print(f"Using {args.servo} servo controller")
    print("Note: Servos will maintain their positions when you quit")
    
    # Get servo controller
    servo_type = ServoControllerType.GPIO if args.servo == 'gpio' else ServoControllerType.PCA9685
    servo_controller = get_servo_controller(servo_type)
    
    try:
        print("Servo controller initialized successfully")
        
        # If specific pattern requested, run it and exit
        if args.pattern:
            if args.pattern == 'sweep':
                run_sweep_pattern(servo_controller)
            elif args.pattern == 'wave':
                run_wave_pattern(servo_controller)
            elif args.pattern == 'test':
                run_test_pattern(servo_controller)
            elif args.pattern == 'center':
                center_servos(servo_controller)
            return
        
        # Interactive mode
        while True:
            show_main_menu()
            
            try:
                choice = input("Enter choice (1-6): ").strip()
                
                if choice == '1':
                    run_sweep_pattern(servo_controller)
                elif choice == '2':
                    run_wave_pattern(servo_controller)
                elif choice == '3':
                    run_test_pattern(servo_controller)
                elif choice == '4':
                    center_servos(servo_controller)
                elif choice == '5':
                    result = individual_servo_control(servo_controller)
                    if result == 'quit':
                        break
                elif choice == '6':
                    break
                else:
                    print("Invalid choice. Please enter 1-6.")
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Don't shutdown - leave servos in their current positions
        print("Servo controller left in current state")


if __name__ == "__main__":
    main() 