#!/usr/bin/env python3
"""
Simple GPIO servo test script.

This script provides a basic test of the GPIO servo controller
to verify it's working correctly.
"""

import time
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.hardware.servo_controller import GPIOServoController
from raspibot.config.hardware_config import GPIO_SERVO_PINS


def main():
    """Simple GPIO servo test."""
    print("=== Simple GPIO Servo Test ===")
    print(f"Configured servo pins: {GPIO_SERVO_PINS}")
    print()
    
    try:
        # Create GPIO controller
        print("Creating GPIO servo controller...")
        controller = GPIOServoController()
        print("✓ GPIO controller created successfully")
        
        # Test each servo
        for channel, pin in GPIO_SERVO_PINS.items():
            print(f"\n--- Testing Servo {channel} on GPIO {pin} ---")
            
            # Move to center (135 degrees)
            print("Moving to center position (135°)")
            controller.set_servo_angle(channel, 135)
            time.sleep(2)
            
            # Move to minimum (0 degrees)
            print("Moving to minimum position (0°)")
            controller.set_servo_angle(channel, 0)
            time.sleep(2)
            
            # Move to maximum (270 degrees)
            print("Moving to maximum position (270°)")
            controller.set_servo_angle(channel, 270)
            time.sleep(2)
            
            # Return to center
            print("Returning to center position (135°)")
            controller.set_servo_angle(channel, 135)
            time.sleep(2)
        
        print("\n✓ All servo tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        try:
            if 'controller' in locals():
                print("\nShutting down controller...")
                controller.shutdown()
                print("✓ Controller shutdown completed")
        except Exception as e:
            print(f"✗ Shutdown error: {e}")


if __name__ == "__main__":
    main() 