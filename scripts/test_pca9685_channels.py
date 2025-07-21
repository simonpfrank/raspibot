#!/usr/bin/env python3
"""
PCA9685 Channel Test Script

This script allows testing of PCA9685 servo controller channels one by one.
The user inputs a channel number and the script performs a series of tests:
1. Direct movement to 45°
2. Smooth movement to 180°
3. Smooth movement back to 45°
4. Direct movement to center (90°)

This demonstrates the difference between direct and smooth servo movements.

Usage:
    python test_pca9685_channels.py

Requirements:
    - PCA9685 servo controller connected via I2C
    - Servo connected to the specified channel
    - 5V power supply for servo
"""

import sys
import time
from typing import Optional

# Add the project root to the path to import our modules
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from raspibot.hardware.servo_controller import PCA9685ServoController
    from raspibot.config.hardware_config import (
        PCA9685_ADDRESS,
        SERVO_MIN_ANGLE,
        SERVO_MAX_ANGLE,
        SERVO_DEFAULT_ANGLE
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the scripts/ directory")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)


def get_user_input(prompt: str, min_val: int, max_val: int) -> int:
    """
    Get user input with validation.
    
    Args:
        prompt: Input prompt message
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated integer input
    """
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            else:
                print(f"Please enter a value between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid number")


def test_channel(controller: PCA9685ServoController, channel: int) -> None:
    """
    Test a specific channel with hardcoded angles and smooth movement comparison.
    
    Args:
        controller: PCA9685 servo controller instance
        channel: Channel number to test
    """
    print(f"\n=== Testing Channel {channel} ===")
    
    # Hardcoded test angles
    angle1 = 45
    angle2 = 180
    
    print(f"Channel {channel} angle range: {SERVO_MIN_ANGLE}° to {SERVO_MAX_ANGLE}°")
    print(f"Test angles: {angle1}° and {angle2}°")
    
    try:
        # Test 1: Direct movement to 45°
        print(f"\n1. Direct movement to {angle1}°...")
        controller.set_servo_angle(channel, angle1)
        time.sleep(2)  # Wait for movement to complete
        
        # Test 2: Smooth movement to 180°
        print(f"2. Smooth movement to {angle2}°...")
        controller.smooth_move_to_angle(channel, angle2, speed=0.8)
        time.sleep(1)  # Brief pause
        
        # Test 3: Smooth movement back to 45°
        print(f"3. Smooth movement back to {angle1}°...")
        controller.smooth_move_to_angle(channel, angle1, speed=0.8)
        time.sleep(1)  # Brief pause
        
        # Test 4: Direct movement to center
        print(f"4. Direct movement to center ({SERVO_DEFAULT_ANGLE}°)...")
        controller.set_servo_angle(channel, SERVO_DEFAULT_ANGLE)
        time.sleep(1)
        
        print(f"Channel {channel} test completed successfully!")
        print("Note: Smooth movements should be noticeably less jittery than direct movements.")
        
    except Exception as e:
        print(f"Error testing channel {channel}: {e}")


def main() -> None:
    """Main function to test PCA9685 channels."""
    print("=== PCA9685 Channel Test Script ===")
    print("This script will test PCA9685 servo controller channels")
    print("Each test includes direct and smooth movement comparisons")
    print("Make sure your PCA9685 is connected and servos are powered")
    print()
    
    # Initialize PCA9685 controller
    try:
        controller = PCA9685ServoController()
        print("PCA9685 controller initialized successfully")
        print(f"I2C Address: 0x{PCA9685_ADDRESS:02X}")
        print(f"Angle range: {SERVO_MIN_ANGLE}° to {SERVO_MAX_ANGLE}°")
        print()
        
    except Exception as e:
        print(f"Error initializing PCA9685 controller: {e}")
        print("Please check your I2C connection and PCA9685 setup")
        sys.exit(1)
    
    try:
        while True:
            # Get channel number from user
            channel = get_user_input(
                "Enter channel number (0-15) or -1 to exit: ",
                -1, 15
            )
            
            if channel == -1:
                print("Exiting...")
                break
            
            # Test the specified channel
            test_channel(controller, channel)
        
        print("\n=== All tests completed! ===")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")
    finally:
        # Cleanup
        try:
            controller.shutdown()
            print("PCA9685 controller shutdown completed")
        except Exception as e:
            print(f"Error during shutdown: {e}")


if __name__ == "__main__":
    main() 