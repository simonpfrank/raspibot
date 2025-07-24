#!/usr/bin/env python3
"""
Quick script to return servos to safe positions.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.hardware.servo_factory import ServoControllerFactory, ServoControllerType


def main():
    """Return servos to safe positions."""
    print("Returning servos to safe positions...")
    
    try:
        # Initialize servo controller
        controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
        
        # Return to safe positions
        print("Setting pan servo to 90° (center)...")
        controller.set_servo_angle(0, 90)  # Pan center
        time.sleep(0.5)
        
        print("Setting tilt servo to 200° (safe position)...")
        controller.set_servo_angle(1, 200)  # Tilt safe position
        time.sleep(0.5)
        
        # Shutdown
        controller.shutdown()
        print("✅ Servos returned to safe positions")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 