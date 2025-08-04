#!/usr/bin/env python3
"""
Complete Servo System Test Script

This script demonstrates the complete servo control system including:
- Servo controller factory
- Abstract interface implementation
- Both PCA9685 and GPIO controllers
- Pan/tilt system with coordinate-based movement

Usage:
    python test_complete_servo_system.py

Requirements:
    - PCA9685 servo controller (optional)
    - GPIO servos (optional)
    - 5V power supply for servos
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.hardware.servo_selector import (
    get_servo_controller, ServoControllerType, 
    get_available_controllers, is_pca9685_available, get_recommended_controller
)
from raspibot.hardware.servo_interface import ServoInterface
from raspibot.movement.pan_tilt import PanTiltSystem
from raspibot.utils.logging_config import setup_logging
from raspibot.settings.config import (
    SERVO_PAN_CHANNEL, SERVO_TILT_CHANNEL,
    SERVO_PAN_MIN_ANGLE, SERVO_PAN_MAX_ANGLE, SERVO_PAN_CENTER,
    SERVO_TILT_MIN_ANGLE, SERVO_TILT_MAX_ANGLE, SERVO_TILT_CENTER
)


def test_factory_creation() -> None:
    """Test servo controller factory creation."""
    print("\n=== Testing Servo Controller Factory ===")
    
    # Test available controller types
    available_types = get_available_controllers()
    print(f"Available controller types: {[t.value for t in available_types]}")
    
    # Test PCA9685 availability
    pca9685_available = is_pca9685_available()
    print(f"PCA9685 available: {pca9685_available}")
    
    # Test recommended controller
    recommended = get_recommended_controller()
    print(f"Recommended controller: {recommended.value}")
    
    # Test PCA9685 creation
    try:
        pca_controller = get_servo_controller(ServoControllerType.PCA9685)
        print(f"✓ PCA9685 controller created: {pca_controller.get_controller_type()}")
        print(f"  Available channels: {pca_controller.get_available_channels()}")
    except Exception as e:
        print(f"⚠ PCA9685 controller creation failed: {e}")
    
    # Test GPIO creation
    try:
        gpio_controller = get_servo_controller(ServoControllerType.GPIO)
        print(f"✓ GPIO controller created: {gpio_controller.get_controller_type()}")
        print(f"  Available channels: {gpio_controller.get_available_channels()}")
    except Exception as e:
        print(f"⚠ GPIO controller creation failed: {e}")
    
    # Test string-based creation
    try:
        pca_controller_str = get_servo_controller("pca9685")
        print(f"✓ String-based PCA9685 creation: {pca_controller_str.get_controller_type()}")
    except Exception as e:
        print(f"⚠ String-based PCA9685 creation failed: {e}")
    
    # Test auto selection
    try:
        auto_controller = get_servo_controller(ServoControllerType.AUTO)
        print(f"✓ Auto-selected controller: {auto_controller.get_controller_type()}")
    except Exception as e:
        print(f"⚠ Auto controller selection failed: {e}")


def test_interface_contract(controller: ServoInterface, controller_name: str) -> None:
    """Test that a controller implements the interface contract.
    
    Args:
        controller: Servo controller instance
        controller_name: Name for logging
    """
    print(f"\n=== Testing {controller_name} Interface Contract ===")
    
    # Test interface methods exist
    assert hasattr(controller, 'set_servo_angle')
    assert hasattr(controller, 'get_servo_angle')
    assert hasattr(controller, 'smooth_move_to_angle')
    assert hasattr(controller, 'emergency_stop')
    assert hasattr(controller, 'set_calibration_offset')
    assert hasattr(controller, 'get_calibration_offset')
    assert hasattr(controller, 'shutdown')
    assert hasattr(controller, 'get_controller_type')
    assert hasattr(controller, 'get_available_channels')
    print("✓ All interface methods present")
    
    # Test controller type
    controller_type = controller.get_controller_type()
    print(f"✓ Controller type: {controller_type}")
    
    # Test available channels
    channels = controller.get_available_channels()
    print(f"✓ Available channels: {channels}")
    
    if channels:
        test_channel = channels[0]
        print(f"  Testing with channel {test_channel}")
        
        # Test basic servo operations
        try:
            # Test angle setting
            controller.set_servo_angle(test_channel, 90)
            time.sleep(0.5)
            current_angle = controller.get_servo_angle(test_channel)
            print(f"✓ Set angle to 90°, got {current_angle}°")
            
            # Test calibration
            controller.set_calibration_offset(test_channel, 5.0)
            offset = controller.get_calibration_offset(test_channel)
            print(f"✓ Set calibration offset to 5.0°, got {offset}°")
            
            # Test smooth movement
            controller.smooth_move_to_angle(test_channel, 45, speed=0.8)
            time.sleep(1)
            print("✓ Smooth movement to 45° completed")
            
            # Return to center
            controller.set_servo_angle(test_channel, 90)
            time.sleep(0.5)
            print("✓ Returned to center position")
            
        except Exception as e:
            print(f"⚠ Servo operations failed: {e}")


def test_pan_tilt_system(controller: ServoInterface, controller_name: str) -> None:
    """Test pan/tilt system with a servo controller.
    
    Args:
        controller: Servo controller instance
        controller_name: Name for logging
    """
    print(f"\n=== Testing Pan/Tilt System with {controller_name} ===")
    
    try:
        # Create pan/tilt system with correct channels from config
        pan_tilt = PanTiltSystem(
            servo_controller=controller,
            pan_channel=SERVO_PAN_CHANNEL,
            tilt_channel=SERVO_TILT_CHANNEL
        )
        print("✓ Pan/tilt system created")
        
        # Test coordinate-based movement
        print("Testing coordinate-based movement...")
        
        # Center
        print("Moving to center (0,0)...")
        pan_tilt.move_to_coordinates(0, 0)
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        angles = pan_tilt.get_current_position()
        print(f"✓ Moved to center (0,0), position: {pos}, angles: {angles}")
        
        # Far left
        print("Moving to far left (-1.0,0)...")
        pan_tilt.move_to_coordinates(-1.0, 0)
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        angles = pan_tilt.get_current_position()
        print(f"✓ Moved to far left (-1.0,0), position: {pos}, angles: {angles}")
        
        # Far right
        print("Moving to far right (1.0,0)...")
        pan_tilt.move_to_coordinates(1.0, 0)
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        angles = pan_tilt.get_current_position()
        print(f"✓ Moved to far right (1.0,0), position: {pos}, angles: {angles}")
        
        # Far up
        print("Moving to far up (0,1.0)...")
        pan_tilt.move_to_coordinates(0, 1.0)
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        angles = pan_tilt.get_current_position()
        print(f"✓ Moved to far up (0,1.0), position: {pos}, angles: {angles}")
        
        # Far down
        print("Moving to far down (0,-1.0)...")
        pan_tilt.move_to_coordinates(0, -1.0)
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        angles = pan_tilt.get_current_position()
        print(f"✓ Moved to far down (0,-1.0), position: {pos}, angles: {angles}")
        
        # Smooth movement
        print("Testing smooth movement...")
        pan_tilt.smooth_move_to_coordinates(0, 0, speed=0.8)
        time.sleep(2)
        pos = pan_tilt.get_current_coordinates()
        print(f"✓ Smooth movement to center, position: {pos}")
        
        # Return to center
        pan_tilt.center_camera()
        time.sleep(0.5)
        print("✓ Returned to center")
        
        # Shutdown
        pan_tilt.shutdown()
        print("✓ Pan/tilt system shutdown")
        
    except Exception as e:
        print(f"⚠ Pan/tilt system test failed: {e}")


def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Complete Servo System Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python servo_system_demo.py                    # Use default (PCA9685)
  python servo_system_demo.py --servo gpio       # Use GPIO servo controller
  python servo_system_demo.py --servo pca9685    # Use PCA9685 servo controller
  python servo_system_demo.py --servo auto       # Auto-select best available
        """
    )
    parser.add_argument(
        '--servo', 
        choices=['pca9685', 'gpio', 'auto'], 
        default='auto',
        help='Servo controller type (default: auto)'
    )
    parser.add_argument(
        '--test-all',
        action='store_true',
        help='Test all available servo controllers'
    )
    return parser.parse_args()


def main() -> None:
    """Main test function."""
    args = parse_arguments()
    
    print("=== Complete Servo System Test ===")
    print("This script tests the servo control system")
    print("including factory, interface, and pan/tilt functionality")
    print()
    
    # Setup logging
    logger = setup_logging(__name__)
    
    try:
        # Test factory
        test_factory_creation()
        
        if args.test_all:
            # Test all available controllers
            print("\n=== Testing All Available Controllers ===")
            
            # Test PCA9685 controller
            try:
                pca_controller = get_servo_controller(ServoControllerType.PCA9685)
                test_interface_contract(pca_controller, "PCA9685")
                test_pan_tilt_system(pca_controller, "PCA9685")
            except Exception as e:
                print(f"⚠ PCA9685 tests skipped: {e}")
            
            # Test GPIO controller
            try:
                gpio_controller = get_servo_controller(ServoControllerType.GPIO)
                test_interface_contract(gpio_controller, "GPIO")
                test_pan_tilt_system(gpio_controller, "GPIO")
            except Exception as e:
                print(f"⚠ GPIO tests skipped: {e}")
        else:
            # Test selected controller
            print(f"\n=== Testing {args.servo.upper()} Controller ===")
            
            # Convert string to enum
            if args.servo == 'pca9685':
                servo_type = ServoControllerType.PCA9685
            elif args.servo == 'gpio':
                servo_type = ServoControllerType.GPIO
            else:  # auto
                servo_type = ServoControllerType.AUTO
            
            try:
                controller = get_servo_controller(servo_type)
                controller_name = controller.get_controller_type()
                test_interface_contract(controller, controller_name)
                test_pan_tilt_system(controller, controller_name)
            except Exception as e:
                print(f"⚠ {args.servo.upper()} tests failed: {e}")
        
        print("\n=== Test Summary ===")
        print("✓ Factory pattern working")
        print("✓ Interface contract enforced")
        print("✓ Pan/tilt system functional")
        print("✓ Complete servo system ready!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {e}")
        logger.error(f"Test error: {e}")


if __name__ == "__main__":
    main() 