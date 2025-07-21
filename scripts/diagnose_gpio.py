#!/usr/bin/env python3
"""
GPIO Servo Controller Diagnostic Script

This script helps identify issues with the integrated GPIOServoController
by testing each component step by step.
"""

import sys
import os
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_imports():
    """Test if all required modules can be imported."""
    print("=== Testing Imports ===")
    
    try:
        import RPi.GPIO as GPIO
        print("✓ RPi.GPIO imported successfully")
    except ImportError as e:
        print(f"✗ RPi.GPIO import failed: {e}")
        return False
    
    try:
        from raspibot.exceptions import HardwareException
        print("✓ HardwareException imported successfully")
    except ImportError as e:
        print(f"✗ HardwareException import failed: {e}")
        return False
    
    try:
        from raspibot.utils.logging_config import setup_logging
        print("✓ setup_logging imported successfully")
    except ImportError as e:
        print(f"✗ setup_logging import failed: {e}")
        return False
    
    try:
        from raspibot.config.hardware_config import (
            GPIO_SERVO_MIN_ANGLE,
            GPIO_SERVO_MAX_ANGLE,
            GPIO_SERVO_DEFAULT_ANGLE,
            GPIO_SERVO_FREQUENCY,
            GPIO_SERVO_MIN_PULSE,
            GPIO_SERVO_MAX_PULSE,
            GPIO_SERVO_PINS,
        )
        print("✓ Hardware config imported successfully")
        print(f"  GPIO_SERVO_PINS: {GPIO_SERVO_PINS}")
        print(f"  Angle range: {GPIO_SERVO_MIN_ANGLE}° to {GPIO_SERVO_MAX_ANGLE}°")
        print(f"  Default angle: {GPIO_SERVO_DEFAULT_ANGLE}°")
    except ImportError as e:
        print(f"✗ Hardware config import failed: {e}")
        return False
    
    try:
        from raspibot.hardware.servo_controller import GPIOServoController
        print("✓ GPIOServoController imported successfully")
    except ImportError as e:
        print(f"✗ GPIOServoController import failed: {e}")
        return False
    
    return True


def test_gpio_access():
    """Test basic GPIO access."""
    print("\n=== Testing GPIO Access ===")
    
    try:
        import RPi.GPIO as GPIO
        
        # Test GPIO mode setting
        GPIO.setmode(GPIO.BCM)
        print("✓ GPIO mode set to BCM")
        
        # Test GPIO setup
        GPIO.setup(17, GPIO.OUT)
        print("✓ GPIO pin 17 setup as output")
        
        # Test PWM creation
        pwm = GPIO.PWM(17, 50)
        pwm.start(0)
        print("✓ PWM created and started")
        
        # Cleanup
        pwm.stop()
        GPIO.cleanup()
        print("✓ GPIO cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ GPIO access test failed: {e}")
        traceback.print_exc()
        return False


def test_controller_creation():
    """Test GPIOServoController creation."""
    print("\n=== Testing Controller Creation ===")
    
    try:
        from raspibot.hardware.servo_controller import GPIOServoController
        
        # Test with default configuration
        print("Creating GPIOServoController with default config...")
        controller = GPIOServoController()
        print("✓ GPIOServoController created successfully")
        
        # Test basic functionality
        print("Testing basic servo control...")
        for channel in [0, 1]:  # Test first two channels
            try:
                controller.set_servo_angle(channel, 135)  # Center position
                print(f"✓ Servo {channel} moved to center")
            except Exception as e:
                print(f"✗ Servo {channel} movement failed: {e}")
        
        # Cleanup
        controller.shutdown()
        print("✓ Controller shutdown completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Controller creation test failed: {e}")
        traceback.print_exc()
        return False


def test_custom_config():
    """Test controller with custom configuration."""
    print("\n=== Testing Custom Configuration ===")
    
    try:
        from raspibot.hardware.servo_controller import GPIOServoController
        
        # Test with custom pin mapping
        custom_pins = {0: 17}  # Just one servo on GPIO 17
        print(f"Creating controller with custom pins: {custom_pins}")
        
        controller = GPIOServoController(servo_pins=custom_pins)
        print("✓ Custom controller created successfully")
        
        # Test movement
        controller.set_servo_angle(0, 135)
        print("✓ Custom controller movement successful")
        
        # Cleanup
        controller.shutdown()
        print("✓ Custom controller shutdown completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Custom configuration test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Main diagnostic function."""
    print("=== GPIO Servo Controller Diagnostic ===")
    print("This script will test each component step by step")
    print()
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Check your installation.")
        return
    
    # Test GPIO access
    if not test_gpio_access():
        print("\n❌ GPIO access test failed. Check permissions and hardware.")
        return
    
    # Test controller creation
    if not test_controller_creation():
        print("\n❌ Controller creation test failed. Check configuration.")
        return
    
    # Test custom configuration
    if not test_custom_config():
        print("\n❌ Custom configuration test failed.")
        return
    
    print("\n🎉 All tests passed! GPIOServoController should work correctly.")
    print("\nYou can now run:")
    print("  python3 scripts/test_servo_controllers.py")


if __name__ == "__main__":
    main() 