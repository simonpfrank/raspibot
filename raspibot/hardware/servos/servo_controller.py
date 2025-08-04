#!/usr/bin/env python3
"""Simple servo controller using Adafruit libraries.

This module provides a clean interface for controlling servos using
Adafruit's battle-tested libraries with minimal wrapper code.
"""

import time
import logging
from typing import Dict, Optional, Final
from abc import ABC, abstractmethod

# Hardware configuration
from raspibot.settings.config import (
    I2C_BUS,
    PCA9685_ADDRESS,
    SERVO_PAN_0_PULSE,
    SERVO_PAN_90_PULSE,
    SERVO_PAN_180_PULSE,
    SERVO_TILT_0_PULSE,
    SERVO_TILT_90_PULSE,
    SERVO_TILT_180_PULSE,
    SERVO_MIN_ANGLE,
    SERVO_MAX_ANGLE,
    SERVO_DEFAULT_ANGLE,
)
from raspibot.hardware.servos.servo_template import ServoInterface
# Custom exceptions
from raspibot.exceptions import HardwareException

# Try to import Adafruit libraries
try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    ADAFRUIT_AVAILABLE = True
except ImportError:
    ADAFRUIT_AVAILABLE = False
    print("⚠️  Adafruit libraries not available. Install with: pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor")


class SimplePCA9685ServoController(ServoInterface):
    """Simple PCA9685 servo controller using Adafruit libraries."""
    
    def __init__(self, i2c_bus: int = I2C_BUS, address: int = PCA9685_ADDRESS):
        """Initialize the servo controller.
        
        Args:
            i2c_bus: I2C bus number
            address: PCA9685 I2C address
        """
        self.logger = logging.getLogger(__name__)
        self.address = address
        self.i2c_bus = i2c_bus
        
        # Initialize hardware
        self.pca = None
        self.servos: Dict[int, servo.Servo] = {}
        self.current_angles: Dict[int, float] = {}
        self.calibration_offsets: Dict[int, float] = {}
        
        if not ADAFRUIT_AVAILABLE:
            raise HardwareException("Adafruit libraries not available")
        
        self._init_hardware()
        self.logger.info("Simple PCA9685 servo controller initialized")
    
    def _init_hardware(self) -> None:
        """Initialize PCA9685 hardware."""
        try:
            # Initialize I2C bus
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(self.i2c, address=self.address)
            self.pca.frequency = 50  # 50Hz for servos
            
            # Create servo objects with calibrated pulse ranges
            self._create_servos()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PCA9685: {e}")
            raise HardwareException(f"PCA9685 initialization failed: {e}")
    
    def _create_servos(self) -> None:
        """Create servo objects with calibrated pulse ranges."""
        # Pan servo (channel 0) - calibrated pulse widths
        self.servos[0] = servo.Servo(
            self.pca.channels[0],
            min_pulse=int(SERVO_PAN_0_PULSE * 1000),    # Convert ms to microseconds
            max_pulse=int(SERVO_PAN_180_PULSE * 1000)
        )
        
        # Tilt servo (channel 1) - calibrated pulse widths
        self.servos[1] = servo.Servo(
            self.pca.channels[1],
            min_pulse=int(SERVO_TILT_0_PULSE * 1000),   # Convert ms to microseconds
            max_pulse=int(SERVO_TILT_180_PULSE * 1000)
        )
        
        # Initialize current angles
        self.current_angles = {0: SERVO_DEFAULT_ANGLE, 1: SERVO_DEFAULT_ANGLE}
        
        self.logger.info(f"Created servos with calibrated pulse ranges")
        self.logger.info(f"Pan: {SERVO_PAN_0_PULSE}ms - {SERVO_PAN_180_PULSE}ms")
        self.logger.info(f"Tilt: {SERVO_TILT_0_PULSE}ms - {SERVO_TILT_180_PULSE}ms")
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle with calibration offset.
        
        Args:
            channel: Servo channel (0-15)
            angle: Target angle in degrees (0-180)
        """
        # Validate channel
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        
        # Validate angle
        if not SERVO_MIN_ANGLE <= angle <= SERVO_MAX_ANGLE:
            raise HardwareException(f"Invalid angle: {angle}° (must be {SERVO_MIN_ANGLE}-{SERVO_MAX_ANGLE}°)")
        
        # TEMPORARY: Ban problematic 90-100° range to prevent jitter
        if 90 <= angle <= 100:
            self.logger.warning(f"TEMPORARY BAN: Angle {angle}° is in jitter-prone range (90-100°). Adjusting to safe angle.")
            if angle <= 95:
                angle = 89  # Move to safe angle below range
            else:
                angle = 101  # Move to safe angle above range
            self.logger.info(f"Adjusted angle to {angle}°")
        
        # Apply calibration offset
        offset = self.calibration_offsets.get(channel, 0.0)
        adjusted_angle = angle + offset
        
        # Clamp to valid range
        adjusted_angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, adjusted_angle))
        
        # Set servo angle
        self.servos[channel].angle = adjusted_angle
        
        # Update current angle
        self.current_angles[channel] = angle
        
        self.logger.debug(f"Servo {channel} set to {angle}° (adjusted: {adjusted_angle}°)")
    
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle.
        
        Args:
            channel: Servo channel (0-15)
            
        Returns:
            Current angle in degrees
        """
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        
        return self.current_angles.get(channel, SERVO_DEFAULT_ANGLE)
    
    def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Smooth movement to target angle.
        
        Args:
            channel: Servo channel (0-15)
            target_angle: Target angle in degrees
            speed: Movement speed (0.1-1.0, where 1.0 is fastest)
        """
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        
        if not SERVO_MIN_ANGLE <= target_angle <= SERVO_MAX_ANGLE:
            raise HardwareException(f"Invalid angle: {target_angle}°")
        
        # Clamp speed
        speed = max(0.1, min(1.0, speed))
        
        current_angle = self.get_servo_angle(channel)
        angle_diff = target_angle - current_angle
        
        # Skip if movement is too small
        if abs(angle_diff) < 0.5:
            return
        
        # Calculate steps for smooth movement
        steps = max(10, int(abs(angle_diff) / 2))
        step_size = angle_diff / steps
        step_delay = 0.02 / speed
        
        # Move in steps
        for i in range(steps):
            self.set_servo_angle(channel, current_angle + (step_size * i))
            time.sleep(step_delay)
        
        # Final position
        self.set_servo_angle(channel, target_angle)
        time.sleep(0.1)
    
    def emergency_stop(self) -> None:
        """Emergency stop - maintain current positions."""
        self.logger.warning("Emergency stop activated")
        # Servos will maintain current position (no movement)
    
    def set_calibration_offset(self, channel: int, offset: float) -> None:
        """Set calibration offset for a servo.
        
        Args:
            channel: Servo channel (0-15)
            offset: Angle offset in degrees
        """
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        
        self.calibration_offsets[channel] = offset
        self.logger.info(f"Calibration offset for servo {channel}: {offset}°")
    
    def get_calibration_offset(self, channel: int) -> float:
        """Get calibration offset for a servo.
        
        Args:
            channel: Servo channel (0-15)
            
        Returns:
            Calibration offset in degrees
        """
        return self.calibration_offsets.get(channel, 0.0)
    
    def shutdown(self) -> None:
        """Shutdown the controller."""
        self.logger.info("Shutting down servo controller")
        # Servos will maintain their current position
        # No need to explicitly stop them
    
    def get_controller_type(self) -> str:
        """Get controller type."""
        return "Simple PCA9685 (Adafruit)"
    
    def get_available_channels(self) -> list[int]:
        """Get available servo channels."""
        return list(self.servos.keys())


# Legacy class for backward compatibility
class PCA9685ServoController(SimplePCA9685ServoController):
    """Legacy PCA9685 servo controller - now uses Adafruit libraries."""
    
    def __init__(self, i2c_bus: int = I2C_BUS, address: int = PCA9685_ADDRESS):
        """Initialize the legacy servo controller."""
        super().__init__(i2c_bus, address)
        self.logger.info("Using legacy PCA9685ServoController (now with Adafruit libraries)")


# Keep the GPIO controller as is (it's already simple)
class GPIOServoController(ServoInterface):
    """GPIO-based servo controller for direct pin control."""
    
    def __init__(self, servo_pins: Optional[Dict[int, int]] = None):
        """Initialize GPIO servo controller.
        
        Args:
            servo_pins: Dictionary mapping channel to GPIO pin
        """
        self.logger = logging.getLogger(__name__)
        self.servo_pins = servo_pins or {0: 18, 1: 19}  # Default pins
        self.current_angles: Dict[int, float] = {}
        self.calibration_offsets: Dict[int, float] = {}
        
        # Initialize GPIO
        self._init_gpio()
        self.logger.info("GPIO servo controller initialized")
    
    def _init_gpio(self) -> bool:
        """Initialize GPIO pins."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            
            # Setup servo pins
            for channel, pin in self.servo_pins.items():
                GPIO.setup(pin, GPIO.OUT)
                self.current_angles[channel] = SERVO_DEFAULT_ANGLE
            
            self.gpio = GPIO
            return True
            
        except ImportError:
            self.logger.warning("RPi.GPIO not available - running in simulation mode")
            return False
        except Exception as e:
            self.logger.error(f"GPIO initialization failed: {e}")
            return False
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle using GPIO PWM."""
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        if not SERVO_MIN_ANGLE <= angle <= SERVO_MAX_ANGLE:
            raise HardwareException(f"Invalid angle: {angle}°")
        
        # TEMPORARY: Ban problematic 90-100° range to prevent jitter
        if 90 <= angle <= 100:
            self.logger.warning(f"TEMPORARY BAN: Angle {angle}° is in jitter-prone range (90-100°). Adjusting to safe angle.")
            if angle <= 95:
                angle = 89  # Move to safe angle below range
            else:
                angle = 101  # Move to safe angle above range
            self.logger.info(f"Adjusted angle to {angle}°")
        
        # Apply calibration offset
        offset = self.calibration_offsets.get(channel, 0.0)
        adjusted_angle = angle + offset
        
        # Set PWM for the angle
        self._set_pwm_for_angle(channel, adjusted_angle)
        
        # Update current angle
        self.current_angles[channel] = angle
        
        self.logger.debug(f"GPIO Servo {channel} set to {angle}°")
    
    def _set_pwm_for_angle(self, channel: int, angle: float) -> None:
        """Set PWM for servo angle using calibrated values."""
        # Get calibrated pulse width values based on channel
        if channel == 0:  # Pan servo
            min_pulse = SERVO_PAN_0_PULSE
            center_pulse = SERVO_PAN_90_PULSE
            max_pulse = SERVO_PAN_180_PULSE
        elif channel == 1:  # Tilt servo
            min_pulse = SERVO_TILT_0_PULSE
            center_pulse = SERVO_TILT_90_PULSE
            max_pulse = SERVO_TILT_180_PULSE
        else:
            # Fallback to generic values
            min_pulse = 0.4
            center_pulse = 1.45
            max_pulse = 2.7
        
        # Calculate pulse width using calibrated values
        if angle <= 0:
            pulse_width_ms = min_pulse
        elif angle >= 180:
            pulse_width_ms = max_pulse
        elif angle == 90:
            pulse_width_ms = center_pulse
        else:
            # Interpolate between calibrated points
            if angle < 90:
                ratio = angle / 90.0
                pulse_width_ms = min_pulse + (center_pulse - min_pulse) * ratio
            else:
                ratio = (angle - 90) / 90.0
                pulse_width_ms = center_pulse + (max_pulse - center_pulse) * ratio
        
        # Convert to duty cycle (20ms period at 50Hz)
        duty_cycle = pulse_width_ms / 20.0
        
        if hasattr(self, 'gpio'):
            # Set PWM using GPIO
            pin = self.servo_pins[channel]
            pwm = self.gpio.PWM(pin, 50)  # 50Hz
            pwm.start(duty_cycle * 100)  # Convert to percentage
            time.sleep(0.1)
            pwm.stop()
        else:
            # Simulation mode
            self.logger.debug(f"SIMULATION: GPIO Servo {channel} would move to {angle}° (pulse: {pulse_width_ms:.3f}ms)")
    
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle."""
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        return self.current_angles.get(channel, SERVO_DEFAULT_ANGLE)
    
    def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Smooth movement to target angle."""
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        if not SERVO_MIN_ANGLE <= target_angle <= SERVO_MAX_ANGLE:
            raise HardwareException(f"Invalid angle: {target_angle}°")
        
        # TEMPORARY: Ban problematic 90-100° range to prevent jitter
        if 90 <= target_angle <= 100:
            self.logger.warning(f"TEMPORARY BAN: Target angle {target_angle}° is in jitter-prone range (90-100°). Adjusting to safe angle.")
            if target_angle <= 95:
                target_angle = 89  # Move to safe angle below range
            else:
                target_angle = 101  # Move to safe angle above range
            self.logger.info(f"Adjusted target angle to {target_angle}°")
        
        # Clamp speed
        speed = max(0.1, min(1.0, speed))
        
        current_angle = self.get_servo_angle(channel)
        angle_diff = target_angle - current_angle
        
        # Skip if movement is too small
        if abs(angle_diff) < 0.5:
            return
        
        # Calculate steps for smooth movement
        steps = max(10, int(abs(angle_diff) / 2))
        step_size = angle_diff / steps
        step_delay = 0.02 / speed
        
        # Move in steps
        for i in range(steps):
            self.set_servo_angle(channel, current_angle + (step_size * i))
            time.sleep(step_delay)
        
        # Final position
        self.set_servo_angle(channel, target_angle)
        time.sleep(0.1)
    
    def emergency_stop(self) -> None:
        """Emergency stop."""
        self.logger.warning("Emergency stop activated")
        # Stop all PWM signals
        if hasattr(self, 'gpio'):
            for pin in self.servo_pins.values():
                self.gpio.output(pin, False)
    
    def set_calibration_offset(self, channel: int, offset: float) -> None:
        """Set calibration offset."""
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        self.calibration_offsets[channel] = offset
        self.logger.info(f"Calibration offset for GPIO servo {channel}: {offset}°")
    
    def get_calibration_offset(self, channel: int) -> float:
        """Get calibration offset."""
        return self.calibration_offsets.get(channel, 0.0)
    
    def shutdown(self) -> None:
        """Shutdown the controller."""
        self.logger.info("Shutting down GPIO servo controller")
        if hasattr(self, 'gpio'):
            self.gpio.cleanup() 