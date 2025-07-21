#!/usr/bin/env python3
"""
Optimized Speed Test Script

This script tests the optimized speed settings for GPIO servo control
to demonstrate reduced jitter with better speed ranges.
"""

import time
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.hardware.servo_controller import GPIOServoController


def test_optimized_speeds():
    """Test the optimized speed range (0.7-1.0)."""
    print("=== Testing Optimized Speed Range ===")
    print("Speed range: 0.7 to 1.0 (where 1.0 is smoothest)")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 ---")
        
        # Test speed 0.7 (minimum optimized speed)
        print("Testing speed 0.7 (minimum optimized)")
        controller.smooth_move_to_angle(0, 0, speed=0.7)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 135, speed=0.7)
        time.sleep(1)
        
        # Test speed 0.8 (medium optimized speed)
        print("Testing speed 0.8 (medium optimized)")
        controller.smooth_move_to_angle(0, 270, speed=0.8)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 135, speed=0.8)
        time.sleep(1)
        
        # Test speed 1.0 (fastest and smoothest)
        print("Testing speed 1.0 (fastest and smoothest)")
        controller.smooth_move_to_angle(0, 0, speed=1.0)
        time.sleep(1)
        controller.smooth_move_to_angle(0, 135, speed=1.0)
        time.sleep(1)
        
        controller.shutdown()
        print("✓ Optimized speed test completed")
        
    except Exception as e:
        print(f"✗ Optimized speed test failed: {e}")


def test_direct_vs_smooth():
    """Compare direct movement vs smooth movement."""
    print("\n=== Testing Direct vs Smooth Movement ===")
    print("Comparing jitter between direct and smooth movement")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 ---")
        
        # Test direct movement (potentially jittery)
        print("Testing direct movement (potentially jittery)")
        for angle in [135, 140, 145, 150, 145, 140, 135]:
            controller.set_servo_angle(0, angle)
            time.sleep(0.2)
        
        time.sleep(1)
        
        # Test smooth movement (should be less jittery)
        print("Testing smooth movement (should be less jittery)")
        controller.smooth_move_to_angle(0, 150, speed=1.0)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 135, speed=1.0)
        time.sleep(0.5)
        
        controller.shutdown()
        print("✓ Direct vs smooth comparison completed")
        
    except Exception as e:
        print(f"✗ Direct vs smooth comparison failed: {e}")


def test_smooth_movement_patterns():
    """Test various smooth movement patterns."""
    print("\n=== Testing Smooth Movement Patterns ===")
    print("Testing different movement patterns with smooth movement")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 ---")
        
        # Pattern 1: Wide sweep with speed 1.0
        print("Pattern 1: Wide sweep (speed 1.0)")
        controller.smooth_move_to_angle(0, 0, speed=1.0)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 270, speed=1.0)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 135, speed=1.0)
        time.sleep(1)
        
        # Pattern 2: Medium movements with speed 0.8
        print("Pattern 2: Medium movements (speed 0.8)")
        controller.smooth_move_to_angle(0, 90, speed=0.8)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 180, speed=0.8)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 135, speed=0.8)
        time.sleep(1)
        
        # Pattern 3: Fine movements with speed 0.7
        print("Pattern 3: Fine movements (speed 0.7)")
        controller.smooth_move_to_angle(0, 130, speed=0.7)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 140, speed=0.7)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 135, speed=0.7)
        time.sleep(1)
        
        controller.shutdown()
        print("✓ Smooth movement patterns test completed")
        
    except Exception as e:
        print(f"✗ Smooth movement patterns test failed: {e}")


def test_direct_angle_inputs():
    """Test direct angle inputs for quick positioning."""
    print("\n=== Testing Direct Angle Inputs ===")
    print("Testing direct servo positioning for quick movements")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 ---")
        
        # Test 1: Quick positioning to key angles
        print("Test 1: Quick positioning to key angles")
        angles = [0, 45, 90, 135, 180, 225, 270]
        for angle in angles:
            print(f"Moving to {angle}°")
            controller.set_servo_angle(0, angle)
            time.sleep(0.5)
        
        time.sleep(1)
        
        # Test 2: Fine adjustments
        print("Test 2: Fine adjustments")
        fine_angles = [135, 140, 145, 150, 145, 140, 135]
        for angle in fine_angles:
            print(f"Fine adjustment to {angle}°")
            controller.set_servo_angle(0, angle)
            time.sleep(0.3)
        
        time.sleep(1)
        
        # Test 3: Return to center
        print("Test 3: Return to center")
        controller.set_servo_angle(0, 135)
        time.sleep(1)
        
        controller.shutdown()
        print("✓ Direct angle inputs test completed")
        
    except Exception as e:
        print(f"✗ Direct angle inputs test failed: {e}")


def test_mixed_approaches():
    """Test mixed approaches - combining direct and smooth movement."""
    print("\n=== Testing Mixed Approaches ===")
    print("Testing combination of direct and smooth movement")
    print()
    
    try:
        # Create controller with only GPIO 17
        controller = GPIOServoController(servo_pins={0: 17})
        
        print("--- Testing Servo 0 on GPIO 17 ---")
        
        # Scenario 1: Quick positioning then fine adjustment
        print("Scenario 1: Quick positioning then fine adjustment")
        controller.set_servo_angle(0, 0)  # Quick to start
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 135, speed=1.0)  # Smooth to center
        time.sleep(1)
        
        # Scenario 2: Smooth to position, then direct fine tune
        print("Scenario 2: Smooth to position, then direct fine tune")
        controller.smooth_move_to_angle(0, 180, speed=0.8)  # Smooth to position
        time.sleep(0.5)
        controller.set_servo_angle(0, 185)  # Direct fine adjustment
        time.sleep(0.5)
        controller.set_servo_angle(0, 180)  # Direct back
        time.sleep(1)
        
        # Scenario 3: Multiple smooth movements
        print("Scenario 3: Multiple smooth movements")
        controller.smooth_move_to_angle(0, 90, speed=1.0)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 270, speed=0.8)
        time.sleep(0.5)
        controller.smooth_move_to_angle(0, 135, speed=1.0)
        time.sleep(1)
        
        controller.shutdown()
        print("✓ Mixed approaches test completed")
        
    except Exception as e:
        print(f"✗ Mixed approaches test failed: {e}")


def main():
    """Main test function."""
    print("=== Optimized Speed Test Suite ===")
    print("This script tests the optimized speed settings for GPIO servo control")
    print("Testing only GPIO 17 (servo attached)")
    print("Make sure your servo is properly connected and powered")
    print()
    
    # Run all tests
    test_optimized_speeds()
    test_direct_vs_smooth()
    test_smooth_movement_patterns()
    test_direct_angle_inputs()
    test_mixed_approaches()
    
    print("\n=== Test Summary ===")
    print("🎉 All optimized speed tests completed!")
    print()
    print("Key optimizations made:")
    print("• Speed range changed from 0.1-1.0 to 0.7-1.0")
    print("• Step delay reduced from 0.02s to 0.01s")
    print("• Step sizes increased for smoother movement")
    print("• Stabilization delay reduced from 0.1s to 0.05s")
    print("• Duty cycle precision reduced to minimize PWM jitter")
    print()
    print("Speed recommendations:")
    print("• Speed 1.0: Best for quick positioning (least jitter)")
    print("• Speed 0.8: Good for medium movements")
    print("• Speed 0.7: Suitable for fine positioning")
    print("• Avoid speeds below 0.7 (causes more jitter)")
    print()
    print("Movement approaches:")
    print("• Direct movement: Quick positioning with set_servo_angle()")
    print("• Smooth movement: Anti-jitter movement with smooth_move_to_angle()")
    print("• Mixed approach: Combine both for optimal performance")
    print()
    print("If jitter persists, consider using the PCA9685 controller for hardware PWM")


if __name__ == "__main__":
    main() 