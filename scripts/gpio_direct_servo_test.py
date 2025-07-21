#!/usr/bin/env python3
"""
GPIO Servo Test Script

This script demonstrates basic servo control using RPi.GPIO on GPIO 17.
It provides functions to move the servo to different positions and includes
proper cleanup and error handling.

Usage:
    python gpio_servo_test.py

Requirements:
    - RPi.GPIO library
    - Servo connected to GPIO 17
    - 5V power supply for servo
"""

import RPi.GPIO as GPIO
import time
import sys
from typing import Optional


class ServoController:
    """A simple servo controller using RPi.GPIO PWM."""
    
    def __init__(self, pin: int = 17, frequency: int = 50) -> None:
        """
        Initialize the servo controller.
        
        Args:
            pin: GPIO pin number (default: 17)
            frequency: PWM frequency in Hz (default: 50 for most servos)
        """
        self.pin = pin
        self.frequency = frequency
        self.pwm: Optional[GPIO.PWM] = None
        
        # Servo angle limits (adjust these based on your servo)
        self.min_angle = 0
        self.max_angle = 150
        
        # Duty cycle limits (typical servo values)
        self.min_duty_cycle = 2.5   # 0 degrees
        self.max_duty_cycle = 12.5  # 150 degrees
        
        self._setup_gpio()
    
    def _setup_gpio(self) -> None:
        """Setup GPIO and PWM for servo control."""
        try:
            # Set GPIO mode to BCM numbering
            GPIO.setmode(GPIO.BCM)
            
            # Setup GPIO pin as output
            GPIO.setup(self.pin, GPIO.OUT)
            
            # Initialize PWM
            self.pwm = GPIO.PWM(self.pin, self.frequency)
            self.pwm.start(0)
            
            print(f"Servo controller initialized on GPIO {self.pin}")
            
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            self.cleanup()
            sys.exit(1)
    
    def angle_to_duty_cycle(self, angle: float) -> float:
        """
        Convert angle to duty cycle percentage.
        
        Args:
            angle: Angle in degrees (0-150)
            
        Returns:
            Duty cycle percentage
        """
        # Clamp angle to valid range
        angle = max(self.min_angle, min(self.max_angle, angle))
        
        # Linear interpolation between min and max duty cycles
        duty_cycle = self.min_duty_cycle + (angle / self.max_angle) * (self.max_duty_cycle - self.min_duty_cycle)
        
        return duty_cycle
    
    def move_to_angle(self, angle: float, delay: float = 0.5) -> None:
        """
        Move servo to specified angle.
        
        Args:
            angle: Target angle in degrees (0-150)
            delay: Time to wait after movement in seconds
        """
        if self.pwm is None:
            print("Error: PWM not initialized")
            return
        
        try:
            duty_cycle = self.angle_to_duty_cycle(angle)
            print(f"Moving servo to {angle}° (duty cycle: {duty_cycle:.1f}%)")
            
            self.pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error moving servo: {e}")
    
    def sweep(self, start_angle: float = 0, end_angle: float = 180, 
              step: float = 10, delay: float = 0.1) -> None:
        """
        Sweep servo between two angles.
        
        Args:
            start_angle: Starting angle in degrees
            end_angle: Ending angle in degrees
            step: Angle increment per step
            delay: Delay between steps in seconds
        """
        print(f"Sweeping servo from {start_angle}° to {end_angle}°")
        
        # Forward sweep
        for angle in range(int(start_angle), int(end_angle) + 1, int(step)):
            self.move_to_angle(angle, delay)
        
        # Backward sweep
        for angle in range(int(end_angle), int(start_angle) - 1, -int(step)):
            self.move_to_angle(angle, delay)
    
    def center(self) -> None:
        """Move servo to center position (75 degrees)."""
        print("Moving servo to center position (75°)")
        self.move_to_angle(75)
    
    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            if self.pwm is not None:
                self.pwm.stop()
            GPIO.cleanup()
            print("GPIO cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")


def main() -> None:
    """Main function to demonstrate servo control."""
    print("=== GPIO Servo Test Script ===")
    print("This script will test servo control on GPIO 17")
    print("Make sure your servo is connected to GPIO 17 and powered")
    print()
    
    # Create servo controller
    servo = ServoController(pin=17)
    
    try:
        # Test basic movements
        print("1. Testing basic movements...")
        servo.move_to_angle(0)      # Leftmost position
        time.sleep(1)
        servo.move_to_angle(75)     # Center position
        time.sleep(1)
        servo.move_to_angle(150)    # Rightmost position
        time.sleep(1)
        servo.center()              # Back to center
        time.sleep(1)
        
        # Test sweep movement
        print("\n2. Testing sweep movement...")
        servo.sweep(0, 150, 20, 0.2)
        
        # Test fine control
        print("\n3. Testing fine control...")
        for angle in [37, 75, 112, 75]:
            servo.move_to_angle(angle, 0.5)
        
        print("\n4. Final center position...")
        servo.center()
        
        print("\n=== Test completed successfully! ===")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {e}")
    finally:
        # Always cleanup
        servo.cleanup()


if __name__ == "__main__":
    main()
