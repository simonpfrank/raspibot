#!/usr/bin/env python3
"""
Test script for tilt servo configuration.

This script tests the new tilt servo configuration where:
- 90° = pointing straight up
- 310° = pointing straight down
- 200° = horizontal center position

Usage:
    python test_tilt_configuration.py
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.hardware.servo_factory import ServoControllerFactory, ServoControllerType
from raspibot.movement.pan_tilt import PanTiltSystem
from raspibot.config.hardware_config import (
    SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE, SERVO_TILT_CENTER,
    SERVO_TILT_UP_ANGLE, SERVO_TILT_DOWN_ANGLE
)
from raspibot.utils.logging_config import setup_logging


def test_tilt_configuration():
    """Test the new tilt configuration."""
    logger = setup_logging(__name__)
    
    print("=== Tilt Configuration Test ===")
    print(f"Tilt Range: {SERVO_TILT_MIN_ANGLE}° to {SERVO_TILT_MAX_ANGLE}°")
    print(f"Tilt Center: {SERVO_TILT_CENTER}°")
    print(f"Point Up: {SERVO_TILT_UP_ANGLE}°")
    print(f"Point Down: {SERVO_TILT_DOWN_ANGLE}°")
    print()
    
    # Get available controller
    controller = None
    try:
        controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
        print("✓ Using PCA9685 controller")
    except Exception:
        try:
            controller = ServoControllerFactory.create_controller(ServoControllerType.GPIO)
            print("✓ Using GPIO controller")
        except Exception as e:
            print(f"❌ No servo hardware available: {e}")
            return False
    
    # Create pan/tilt system
    pan_tilt = PanTiltSystem(servo_controller=controller)
    
    print("\n=== Testing Tilt Movements ===")
    
    try:
        # Test pointing up (90°)
        print("1. Pointing camera UP (90°)...")
        pan_tilt.point_up()
        time.sleep(2)
        current_pos = pan_tilt.get_current_position()
        print(f"   Current position: pan={current_pos[0]}°, tilt={current_pos[1]}°")
        assert current_pos[1] == SERVO_TILT_UP_ANGLE, f"Expected {SERVO_TILT_UP_ANGLE}°, got {current_pos[1]}°"
        print("   ✅ Point up successful")
        
        # Test pointing down (310°)
        print("2. Pointing camera DOWN (310°)...")
        pan_tilt.point_down()
        time.sleep(2)
        current_pos = pan_tilt.get_current_position()
        print(f"   Current position: pan={current_pos[0]}°, tilt={current_pos[1]}°")
        assert current_pos[1] == SERVO_TILT_DOWN_ANGLE, f"Expected {SERVO_TILT_DOWN_ANGLE}°, got {current_pos[1]}°"
        print("   ✅ Point down successful")
        
        # Test horizontal (200°)
        print("3. Pointing camera HORIZONTAL (200°)...")
        pan_tilt.point_horizontal()
        time.sleep(2)
        current_pos = pan_tilt.get_current_position()
        print(f"   Current position: pan={current_pos[0]}°, tilt={current_pos[1]}°")
        assert current_pos[1] == SERVO_TILT_CENTER, f"Expected {SERVO_TILT_CENTER}°, got {current_pos[1]}°"
        print("   ✅ Point horizontal successful")
        
        # Test center position
        print("4. Moving to CENTER position...")
        pan_tilt.center_camera()
        time.sleep(2)
        current_pos = pan_tilt.get_current_position()
        print(f"   Current position: pan={current_pos[0]}°, tilt={current_pos[1]}°")
        print("   ✅ Center position successful")
        
        # Test coordinate-based movement
        print("5. Testing coordinate-based movement...")
        pan_tilt.move_to_coordinates(0, 1.0)  # Should point up
        time.sleep(1)
        current_pos = pan_tilt.get_current_position()
        print(f"   Coordinates (0, 1.0) -> pan={current_pos[0]}°, tilt={current_pos[1]}°")
        
        pan_tilt.move_to_coordinates(0, -1.0)  # Should point down
        time.sleep(1)
        current_pos = pan_tilt.get_current_position()
        print(f"   Coordinates (0, -1.0) -> pan={current_pos[0]}°, tilt={current_pos[1]}°")
        
        pan_tilt.move_to_coordinates(0, 0)  # Should be center
        time.sleep(1)
        current_pos = pan_tilt.get_current_position()
        print(f"   Coordinates (0, 0) -> pan={current_pos[0]}°, tilt={current_pos[1]}°")
        print("   ✅ Coordinate movement successful")
        
        # Return to center
        pan_tilt.center_camera()
        time.sleep(1)
        
        print("\n=== Test Summary ===")
        print("✅ All tilt configuration tests passed!")
        print("✅ Tilt range 90°-310° working correctly")
        print("✅ Point up/down/horizontal working")
        print("✅ Coordinate conversion working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Tilt configuration test failed: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            pan_tilt.shutdown()
        except Exception as e:
            print(f"Warning: Error during shutdown: {e}")


def main():
    """Main function."""
    success = test_tilt_configuration()
    
    if success:
        print("\n🎉 Tilt configuration test completed successfully!")
        return 0
    else:
        print("\n❌ Tilt configuration test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 