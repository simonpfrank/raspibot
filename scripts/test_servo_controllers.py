#!/usr/bin/env python3
"""
Test script for both PCA9685 and GPIO servo controllers.

This script demonstrates the usage of both servo controller types
and allows testing of servo movements with different configurations.
"""

import time
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.hardware.servo_controller import PCA9685ServoController, GPIOServoController
from raspibot.config.hardware_config import (
    GPIO_SERVO_PINS,
    GPIO_SERVO_MIN_ANGLE,
    GPIO_SERVO_MAX_ANGLE,
    GPIO_SERVO_DEFAULT_ANGLE,
    SERVO_CHANNELS,
    SERVO_MIN_ANGLE,
    SERVO_MAX_ANGLE,
    SERVO_DEFAULT_ANGLE,
)


def test_gpio_servo_controller():
    """Test GPIO servo controller with 270-degree range."""
    print("=== Testing GPIO Servo Controller ===")
    print(f"GPIO Servo Pins: {GPIO_SERVO_PINS}")
    print(f"Angle Range: {GPIO_SERVO_MIN_ANGLE}° to {GPIO_SERVO_MAX_ANGLE}°")
    print(f"Default Angle: {GPIO_SERVO_DEFAULT_ANGLE}°")
    print()
    
    # Create GPIO servo controller
    try:
        gpio_controller = GPIOServoController()
        print("✓ GPIO servo controller initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize GPIO servo controller: {e}")
        return False
    
    try:
        # Test basic movements for each servo
        for channel in GPIO_SERVO_PINS:
            pin = GPIO_SERVO_PINS[channel]
            print(f"\n--- Testing Servo {channel} (GPIO {pin}) ---")
            
            # Test minimum angle
            print(f"Moving to minimum angle ({GPIO_SERVO_MIN_ANGLE}°)")
            gpio_controller.set_servo_angle(channel, GPIO_SERVO_MIN_ANGLE)
            time.sleep(1)
            
            # Test center angle
            print(f"Moving to center angle ({GPIO_SERVO_DEFAULT_ANGLE}°)")
            gpio_controller.set_servo_angle(channel, GPIO_SERVO_DEFAULT_ANGLE)
            time.sleep(1)
            
            # Test maximum angle
            print(f"Moving to maximum angle ({GPIO_SERVO_MAX_ANGLE}°)")
            gpio_controller.set_servo_angle(channel, GPIO_SERVO_MAX_ANGLE)
            time.sleep(1)
            
            # Return to center
            print("Returning to center")
            gpio_controller.set_servo_angle(channel, GPIO_SERVO_DEFAULT_ANGLE)
            time.sleep(1)
        
        # Test smooth movement
        print("\n--- Testing Smooth Movement ---")
        for channel in GPIO_SERVO_PINS:
            print(f"Smooth movement test for servo {channel}")
            gpio_controller.smooth_move_to_angle(channel, GPIO_SERVO_MAX_ANGLE, speed=0.5)
            time.sleep(0.5)
            gpio_controller.smooth_move_to_angle(channel, GPIO_SERVO_MIN_ANGLE, speed=0.5)
            time.sleep(0.5)
            gpio_controller.smooth_move_to_angle(channel, GPIO_SERVO_DEFAULT_ANGLE, speed=0.5)
            time.sleep(0.5)
        
        print("\n✓ GPIO servo controller tests completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ GPIO servo controller test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            gpio_controller.shutdown()
            print("✓ GPIO servo controller shutdown completed")
        except Exception as e:
            print(f"✗ GPIO shutdown error: {e}")


def test_pca9685_servo_controller():
    """Test PCA9685 servo controller with 180-degree range."""
    print("\n=== Testing PCA9685 Servo Controller ===")
    print(f"Servo Channels: {SERVO_CHANNELS}")
    print(f"Angle Range: {SERVO_MIN_ANGLE}° to {SERVO_MAX_ANGLE}°")
    print(f"Default Angle: {SERVO_DEFAULT_ANGLE}°")
    print()
    
    # Create PCA9685 servo controller
    try:
        pca9685_controller = PCA9685ServoController()
        print("✓ PCA9685 servo controller initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize PCA9685 servo controller: {e}")
        return False
    
    try:
        # Test basic movements for each servo
        for channel in SERVO_CHANNELS:
            print(f"\n--- Testing Servo {channel} (PCA9685) ---")
            
            # Test minimum angle
            print(f"Moving to minimum angle ({SERVO_MIN_ANGLE}°)")
            pca9685_controller.set_servo_angle(channel, SERVO_MIN_ANGLE)
            time.sleep(1)
            
            # Test center angle
            print(f"Moving to center angle ({SERVO_DEFAULT_ANGLE}°)")
            pca9685_controller.set_servo_angle(channel, SERVO_DEFAULT_ANGLE)
            time.sleep(1)
            
            # Test maximum angle
            print(f"Moving to maximum angle ({SERVO_MAX_ANGLE}°)")
            pca9685_controller.set_servo_angle(channel, SERVO_MAX_ANGLE)
            time.sleep(1)
            
            # Return to center
            print("Returning to center")
            pca9685_controller.set_servo_angle(channel, SERVO_DEFAULT_ANGLE)
            time.sleep(1)
        
        # Test smooth movement
        print("\n--- Testing Smooth Movement ---")
        for channel in SERVO_CHANNELS:
            print(f"Smooth movement test for servo {channel}")
            pca9685_controller.smooth_move_to_angle(channel, SERVO_MAX_ANGLE, speed=0.5)
            time.sleep(0.5)
            pca9685_controller.smooth_move_to_angle(channel, SERVO_MIN_ANGLE, speed=0.5)
            time.sleep(0.5)
            pca9685_controller.smooth_move_to_angle(channel, SERVO_DEFAULT_ANGLE, speed=0.5)
            time.sleep(0.5)
        
        print("\n✓ PCA9685 servo controller tests completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ PCA9685 servo controller test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            pca9685_controller.shutdown()
            print("✓ PCA9685 servo controller shutdown completed")
        except Exception as e:
            print(f"✗ PCA9685 shutdown error: {e}")


def test_calibration():
    """Test servo calibration features."""
    print("\n=== Testing Servo Calibration ===")
    
    # Test GPIO calibration
    try:
        gpio_controller = GPIOServoController()
        
        for channel in GPIO_SERVO_PINS:
            print(f"\n--- Testing GPIO Servo {channel} Calibration ---")
            
            # Set calibration offset
            offset = 5.0
            gpio_controller.set_calibration_offset(channel, offset)
            print(f"Set calibration offset: {offset}°")
            
            # Get calibration offset
            retrieved_offset = gpio_controller.get_calibration_offset(channel)
            print(f"Retrieved calibration offset: {retrieved_offset}°")
            
            # Test movement with offset
            target_angle = GPIO_SERVO_DEFAULT_ANGLE
            gpio_controller.set_servo_angle(channel, target_angle)
            print(f"Set angle to {target_angle}° (with {offset}° offset)")
            time.sleep(1)
        
        gpio_controller.shutdown()
        print("✓ GPIO calibration tests completed")
        
    except Exception as e:
        print(f"✗ GPIO calibration test failed: {e}")
    
    # Test PCA9685 calibration
    try:
        pca9685_controller = PCA9685ServoController()
        
        for channel in SERVO_CHANNELS:
            print(f"\n--- Testing PCA9685 Servo {channel} Calibration ---")
            
            # Set calibration offset
            offset = -2.5
            pca9685_controller.set_calibration_offset(channel, offset)
            print(f"Set calibration offset: {offset}°")
            
            # Get calibration offset
            retrieved_offset = pca9685_controller.get_calibration_offset(channel)
            print(f"Retrieved calibration offset: {retrieved_offset}°")
            
            # Test movement with offset
            target_angle = SERVO_DEFAULT_ANGLE
            pca9685_controller.set_servo_angle(channel, target_angle)
            print(f"Set angle to {target_angle}° (with {offset}° offset)")
            time.sleep(1)
        
        pca9685_controller.shutdown()
        print("✓ PCA9685 calibration tests completed")
        
    except Exception as e:
        print(f"✗ PCA9685 calibration test failed: {e}")


def main():
    """Main test function."""
    print("=== Servo Controller Test Suite ===")
    print("This script tests both PCA9685 and GPIO servo controllers")
    print("Make sure your servos are properly connected and powered")
    print()
    
    # Test GPIO controller
    gpio_success = test_gpio_servo_controller()
    
    # Test PCA9685 controller
    pca9685_success = test_pca9685_servo_controller()
    
    # Test calibration
    test_calibration()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"GPIO Controller: {'✓ PASSED' if gpio_success else '✗ FAILED'}")
    print(f"PCA9685 Controller: {'✓ PASSED' if pca9685_success else '✗ FAILED'}")
    
    if gpio_success and pca9685_success:
        print("\n🎉 All tests passed! Both servo controllers are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check hardware connections and configuration.")
    
    print("\n=== Test completed ===")


if __name__ == "__main__":
    main() 