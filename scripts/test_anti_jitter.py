#!/usr/bin/env python3
"""
Anti-Jitter GPIO Servo Test Script

This script tests the anti-jitter improvements for GPIO servo control,
demonstrating smoother movement and reduced jitter.
"""

import time
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.hardware.servo_controller import GPIOServoController
from raspibot.config.hardware_config import (
    GPIO_SERVO_DEADBAND,
    GPIO_SERVO_MIN_STEP_SIZE,
    GPIO_SERVO_MAX_STEP_SIZE,
    GPIO_SERVO_STEP_DELAY,
)


def test_deadband():
    """Test deadband functionality to prevent jitter."""
    print("=== Testing Deadband Functionality ===")
    print(f"Deadband setting: {GPIO_SERVO_DEADBAND}°")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 Deadband ---")
        
        # Move to center
        print("Moving to center position (135°)")
        controller.set_servo_angle(0, 135)
        time.sleep(1)
        
        # Try small movements that should be ignored
        small_movements = [135.5, 134.8, 135.2, 134.9, 135.1]
        for angle in small_movements:
            print(f"Attempting small movement to {angle}° (should be ignored)")
            controller.set_servo_angle(0, angle)
            time.sleep(0.5)
        
        # Try larger movement that should work
        print("Attempting larger movement to 140° (should work)")
        controller.set_servo_angle(0, 140)
        time.sleep(1)
        
        # Return to center
        controller.set_servo_angle(0, 135)
        time.sleep(1)
        
        controller.shutdown()
        print("✓ Deadband test completed")
        
    except Exception as e:
        print(f"✗ Deadband test failed: {e}")


def test_smooth_movement():
    """Test smooth movement with different speeds."""
    print("\n=== Testing Smooth Movement ===")
    print(f"Step size range: {GPIO_SERVO_MIN_STEP_SIZE}° to {GPIO_SERVO_MAX_STEP_SIZE}°")
    print(f"Step delay: {GPIO_SERVO_STEP_DELAY}s")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 Smooth Movement ---")
        
        # Test slow movement
        print("Testing slow movement (speed=0.3)")
        controller.smooth_move_to_angle(0, 0, speed=0.3)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 135, speed=0.3)
        time.sleep(1)
        
        # Test medium movement
        print("Testing medium movement (speed=0.6)")
        controller.smooth_move_to_angle(0, 270, speed=0.6)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 135, speed=0.6)
        time.sleep(1)
        
        # Test fast movement
        print("Testing fast movement (speed=1.0)")
        controller.smooth_move_to_angle(0, 0, speed=1.0)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 135, speed=1.0)
        time.sleep(1)
        
        controller.shutdown()
        print("✓ Smooth movement test completed")
        
    except Exception as e:
        print(f"✗ Smooth movement test failed: {e}")


def test_precision_movement():
    """Test precision movement and duty cycle rounding."""
    print("\n=== Testing Precision Movement ===")
    print("Testing small incremental movements")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 Precision ---")
        
        # Start at center
        controller.set_servo_angle(0, 135)
        time.sleep(1)
        
        # Test small incremental movements
        test_angles = [135, 136, 137, 138, 139, 140, 139, 138, 137, 136, 135]
        
        for angle in test_angles:
            print(f"Moving to {angle}°")
            controller.set_servo_angle(0, angle)
            time.sleep(0.5)
        
        # Test smooth movement with small steps
        print("Testing smooth movement with small steps")
        controller.smooth_move_to_angle(0, 145, speed=0.5)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 125, speed=0.5)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 135, speed=0.5)
        time.sleep(1)
        
        controller.shutdown()
        print("✓ Precision movement test completed")
        
    except Exception as e:
        print(f"✗ Precision movement test failed: {e}")


def test_jitter_comparison():
    """Compare jitter between direct and smooth movement."""
    print("\n=== Testing Jitter Comparison ===")
    print("Comparing direct movement vs smooth movement")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 Jitter Comparison ---")
        
        # Test direct movement (potentially jittery)
        print("Testing direct movement (potentially jittery)")
        for angle in [135, 140, 145, 150, 145, 140, 135]:
            controller.set_servo_angle(0, angle)
            time.sleep(0.3)
        
        time.sleep(1)
        
        # Test smooth movement (should be less jittery)
        print("Testing smooth movement (should be less jittery)")
        controller.smooth_move_to_angle(0, 150, speed=0.8)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 135, speed=0.8)
        time.sleep(0.5)
        
        controller.shutdown()
        print("✓ Jitter comparison test completed")
        
    except Exception as e:
        print(f"✗ Jitter comparison test failed: {e}")


def main():
    """Main test function."""
    print("=== Anti-Jitter GPIO Servo Test Suite ===")
    print("This script tests the anti-jitter improvements for GPIO servo control")
    print("Testing only GPIO 17 (servo attached)")
    print("Make sure your servo is properly connected and powered")
    print()
    
    # Run all tests
    test_deadband()
    test_smooth_movement()
    test_precision_movement()
    test_jitter_comparison()
    
    print("\n=== Test Summary ===")
    print("🎉 All anti-jitter tests completed!")
    print()
    print("Key improvements tested:")
    print("• Deadband filtering to prevent small jitter movements")
    print("• Smooth movement with configurable step sizes")
    print("• Precision duty cycle rounding")
    print("• Stabilization delays")
    print()
    print("If you notice reduced jitter, the improvements are working!")
    print("If jitter persists, consider:")
    print("• Increasing GPIO_SERVO_DEADBAND in hardware_config.py")
    print("• Reducing GPIO_SERVO_STEP_DELAY for smoother movement")
    print("• Using the PCA9685 controller for hardware PWM")


if __name__ == "__main__":
    main() 