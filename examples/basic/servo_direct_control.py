#!/usr/bin/env python3
"""
Direct Servo Control Script

This script provides direct control of servos without using the raspibot abstraction layer.
It uses the underlying PCA9685 or GPIO modules directly for manual calibration.

Usage:
    python servo_direct_control.py            # Prompts for channel and pulse width
    python servo_direct_control.py --gpio     # Use GPIO, prompts for channel and pulse width

Example input:
    0 1.5     # Set pan servo to 1.5ms pulse
    1 2.0     # Set tilt servo to 2.0ms pulse
    0 0.5     # Test very short pulse
    1 2.5     # Test very long pulse
"""

import sys
import argparse
from typing import Optional

# Direct imports (no raspibot)
try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    ADAFRUIT_AVAILABLE = True
except ImportError:
    ADAFRUIT_AVAILABLE = False
    try:
        import smbus2 as smbus
        SMBUS_AVAILABLE = True
    except ImportError:
        SMBUS_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False


class DirectServoController:
    """Direct servo controller using PCA9685 or GPIO."""
    
    def __init__(self, use_gpio: bool = False):
        """
        Initialize direct servo controller.
        
        Args:
            use_gpio: If True, use GPIO control. If False, use PCA9685.
        """
        self.use_gpio = use_gpio
        self.pca9685 = None
        self.bus = None
        self.gpio_initialized = False
        
        # Servo configuration
        self.servo_frequency = 50  # 50Hz for servos
        
        # GPIO pin mapping (channel -> GPIO pin)
        self.gpio_pins = {
            0: 17,  # Pan servo on GPIO 17
            1: 18,  # Tilt servo on GPIO 18
        }
        
        if use_gpio:
            self._init_gpio()
        else:
            self._init_pca9685()
    
    def _init_pca9685(self) -> None:
        """Initialize PCA9685 controller."""
        if ADAFRUIT_AVAILABLE:
            try:
                # Create I2C bus
                i2c = busio.I2C(board.SCL, board.SDA)
                
                # Create PCA9685 instance
                self.pca9685 = PCA9685(i2c, address=0x40)
                
                # Set PWM frequency for servos
                self.pca9685.frequency = self.servo_frequency
                
                print("✓ PCA9685 initialized using Adafruit libraries")
                return
                
            except Exception as e:
                print(f"✗ Failed to initialize PCA9685 with Adafruit: {e}")
        
        if SMBUS_AVAILABLE:
            try:
                # Initialize smbus
                self.bus = smbus.SMBus(1)
                
                # Reset PCA9685
                self._pca9685_reset()
                
                # Set PWM frequency
                self._pca9685_set_frequency(self.servo_frequency)
                
                print("✓ PCA9685 initialized using smbus2")
                return
                
            except Exception as e:
                print(f"✗ Failed to initialize PCA9685 with smbus2: {e}")
        
        print("✗ No PCA9685 libraries available")
        sys.exit(1)
    
    def _init_gpio(self) -> None:
        """Initialize GPIO controller."""
        if not GPIO_AVAILABLE:
            print("✗ RPi.GPIO not available")
            sys.exit(1)
        
        try:
            # Setup GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup servo pins
            for pin in self.gpio_pins.values():
                GPIO.setup(pin, GPIO.OUT)
                pwm = GPIO.PWM(pin, self.servo_frequency)
                pwm.start(0)
            
            self.gpio_initialized = True
            print("✓ GPIO initialized for servo control")
            
        except Exception as e:
            print(f"✗ Failed to initialize GPIO: {e}")
            sys.exit(1)
    
    def _pca9685_reset(self) -> None:
        """Reset PCA9685."""
        if self.bus:
            self.bus.write_byte_data(0x40, 0x00, 0x80)  # Reset
            import time
            time.sleep(0.1)
    
    def _pca9685_set_frequency(self, frequency: int) -> None:
        """Set PCA9685 PWM frequency."""
        if self.bus:
            prescale = int(25000000 / (4096 * frequency)) - 1
            self.bus.write_byte_data(0x40, 0xFE, prescale)
            import time
            time.sleep(0.1)
    

    
    def set_servo_pulse(self, channel: int, pulse_width: float) -> None:
        """
        Set servo to specific pulse width.
        
        Args:
            channel: Servo channel (0=pan, 1=tilt)
            pulse_width: Pulse width in milliseconds
        """
        # Validate channel
        if channel not in [0, 1]:
            print(f"✗ Invalid channel {channel}. Use 0 (pan) or 1 (tilt)")
            return
        
        # Validate pulse width (reasonable range for servos)
        if pulse_width < 0.1 or pulse_width > 3.0:
            print(f"⚠️  Warning: Pulse width {pulse_width}ms is outside typical servo range (0.1-3.0ms)")
        
        print(f"🎯 Setting servo {channel} to {pulse_width}ms pulse")
        
        if self.use_gpio:
            self._set_gpio_servo(channel, pulse_width)
        else:
            self._set_pca9685_servo(channel, pulse_width)
    
    def _set_pca9685_servo(self, channel: int, pulse_width: float) -> None:
        """Set servo pulse width using PCA9685."""
        if self.pca9685:
            # Adafruit method - use duty cycle calculation
            # Convert pulse width to duty cycle
            # At 50Hz, period is 20ms
            duty_cycle = pulse_width / 20.0  # 20ms period at 50Hz
            
            # Convert to 16-bit value (0-65535)
            pwm_value = int(duty_cycle * 65535)
            
            # Clamp to valid range
            pwm_value = max(0, min(65535, pwm_value))
            
            # Set PWM using Adafruit library
            self.pca9685.channels[channel].duty_cycle = pwm_value
            
            print(f"  PCA9685 (Adafruit): Channel {channel}, Pulse {pulse_width:.3f}ms, Duty {duty_cycle:.4f}, PWM {pwm_value}")
            
        elif self.bus:
            # smbus2 method - use proper register addressing
            # Convert pulse width to 12-bit PWM value
            # At 50Hz, period is 20ms
            duty_cycle = pulse_width / 20.0  # 20ms period at 50Hz
            
            # Convert to 12-bit value (0-4095)
            pwm_value = int(duty_cycle * 4095)
            
            # Clamp to valid range
            pwm_value = max(0, min(4095, pwm_value))
            
            # PCA9685 registers
            LED0_ON_L = 0x06
            LED0_ON_H = 0x07
            LED0_OFF_L = 0x08
            LED0_OFF_H = 0x09
            
            # Calculate register addresses for this channel
            on_l = LED0_ON_L + (4 * channel)
            on_h = LED0_ON_H + (4 * channel)
            off_l = LED0_OFF_L + (4 * channel)
            off_h = LED0_OFF_H + (4 * channel)
            
            # Set PWM values (start at 0, end at calculated value)
            self.bus.write_byte_data(0x40, on_l, 0)
            self.bus.write_byte_data(0x40, on_h, 0)
            self.bus.write_byte_data(0x40, off_l, pwm_value & 0xFF)
            self.bus.write_byte_data(0x40, off_h, (pwm_value >> 8) & 0xFF)
            
            print(f"  PCA9685 (smbus2): Channel {channel}, Pulse {pulse_width:.3f}ms, Duty {duty_cycle:.4f}, PWM {pwm_value}")
        else:
            print("✗ PCA9685 not initialized")
    
    def _set_gpio_servo(self, channel: int, pulse_width: float) -> None:
        """Set servo pulse width using GPIO."""
        if not self.gpio_initialized:
            print("✗ GPIO not initialized")
            return
        
        pin = self.gpio_pins[channel]
        
        # Convert pulse width to duty cycle
        duty_cycle = (pulse_width / (1000 / self.servo_frequency)) * 100
        
        # Set PWM
        pwm = GPIO.PWM(pin, self.servo_frequency)
        pwm.ChangeDutyCycle(duty_cycle)
        
        print(f"  GPIO: Pin {pin}, Pulse {pulse_width:.3f}ms, Duty {duty_cycle:.1f}%")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.use_gpio and self.gpio_initialized:
            GPIO.cleanup()
            print("✓ GPIO cleaned up")
        elif self.bus:
            self.bus.close()
            print("✓ I2C bus closed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Direct Servo Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s            # Prompts for channel and pulse width
  %(prog)s --gpio     # Use GPIO, prompts for channel and pulse width
        """
    )
    parser.add_argument("--gpio", action="store_true", help="Use GPIO control instead of PCA9685")
    args = parser.parse_args()

    # Create controller
    try:
        controller = DirectServoController(use_gpio=args.gpio)
    except Exception as e:
        print(f"✗ Failed to initialize controller: {e}")
        return 1

    print("Direct Servo Control - Enter 'q' to quit")
    print("=" * 40)
    print("Your servo calibration:")
    print("  0.4ms = 0°")
    print("  1.45ms = 90°")
    print("  2.47ms = 180°")
    print("  2.7ms = ~200° (max)")
    print()
    print("Typical servo pulse ranges:")
    print("  0.5ms - 1.0ms: Full counter-clockwise")
    print("  1.0ms - 1.5ms: Center position")
    print("  1.5ms - 2.0ms: Full clockwise")
    print("  2.0ms - 2.5ms: Beyond normal range")
    print()

    # Main input loop
    while True:
        try:
            # Prompt for channel and pulse width
            user_input = input("Enter channel and pulse width (e.g. 0 1.5): ").strip()
            
            # Check for quit
            if user_input.lower() == 'q':
                print("👋 Goodbye!")
                break
            
            # Parse input
            try:
                channel_str, pulse_str = user_input.split()
                channel = int(channel_str)
                pulse_width = float(pulse_str)
            except Exception:
                print("✗ Invalid input. Please enter channel and pulse width separated by a space, e.g. '0 1.5'")
                continue

            # Validate channel
            if channel not in [0, 1]:
                print("✗ Invalid channel. Use 0 (pan) or 1 (tilt)")
                continue
            
            # Validate pulse width
            if pulse_width < 0:
                print("✗ Pulse width cannot be negative")
                continue

            # Set servo pulse
            controller.set_servo_pulse(channel, pulse_width)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"✗ Error: {e}")
            continue

    # Cleanup
    controller.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main()) 