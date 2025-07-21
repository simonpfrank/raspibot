#!/usr/bin/env python3
"""Simple script to move servo 1 to 90 degrees."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.hardware.servo_factory import ServoControllerFactory, ServoControllerType

def main():
    """Move servo 1 to 90 degrees."""
    print("Moving servo 1 to 90 degrees...")
    
    # Create controller (will auto-detect available hardware)
    controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
    
    # Move servo 0 (channel 0) to 90 degrees
    controller.set_servo_angle(1, 315
    )
    
    print("Done!")

if __name__ == "__main__":
    main() 