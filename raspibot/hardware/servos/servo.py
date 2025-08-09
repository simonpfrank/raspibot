#!/usr/bin/env python3
"""Unified servo controllers with asyncio support.

Simple, clean servo control for PCA9685 and GPIO with shared utilities.
"""

import asyncio
import time
import logging
from typing import Dict, Optional

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
from raspibot.exceptions import HardwareException

try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    ADAFRUIT_AVAILABLE = True
except ImportError:
    ADAFRUIT_AVAILABLE = False


def _validate_angle(angle: float) -> None:
    """Validate servo angle is in valid range."""
    if not SERVO_MIN_ANGLE <= angle <= SERVO_MAX_ANGLE:
        raise HardwareException(f"Invalid angle: {angle}° (must be {SERVO_MIN_ANGLE}-{SERVO_MAX_ANGLE}°)")


def _handle_jitter_zone(angle: float, logger: logging.Logger) -> float:
    """Handle problematic jitter zone by adjusting angle."""
    if 90 <= angle <= 100:
        logger.warning(f"JITTER ZONE: Adjusting angle {angle}° to avoid jitter")
        adjusted = 89 if angle <= 95 else 101
        logger.info(f"Adjusted angle to {adjusted}°")
        return adjusted
    return angle


def _apply_calibration(angle: float, offset: float) -> float:
    """Apply calibration offset and clamp to valid range."""
    adjusted = angle + offset
    return max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, adjusted))


async def _smooth_move_implementation(
    servo_controller, channel: int, target_angle: float, speed: float
) -> None:
    """Shared smooth movement implementation."""
    _validate_angle(target_angle)
    speed = max(0.1, min(1.0, speed))
    
    current_angle = servo_controller.get_servo_angle(channel)
    angle_diff = target_angle - current_angle
    
    if abs(angle_diff) < 0.5:
        return
    
    steps = max(10, int(abs(angle_diff) / 2))
    step_size = angle_diff / steps
    step_delay = 0.02 / speed
    
    for i in range(steps):
        servo_controller.set_servo_angle(channel, current_angle + (step_size * i))
        await asyncio.sleep(step_delay)
    
    servo_controller.set_servo_angle(channel, target_angle)
    await asyncio.sleep(0.1)


class PCA9685ServoController:
    """PCA9685 servo controller using Adafruit libraries."""
    
    def __init__(self, i2c_bus: int = I2C_BUS, address: int = PCA9685_ADDRESS):
        self.logger = logging.getLogger(__name__)
        self.address = address
        self.i2c_bus = i2c_bus
        
        self.pca = None
        self.servos: Dict[int, servo.Servo] = {}
        self.current_angles: Dict[int, float] = {}
        self.calibration_offsets: Dict[int, float] = {}
        
        if not ADAFRUIT_AVAILABLE:
            raise HardwareException("Adafruit libraries not available")
        
        self._init_hardware()
        self.logger.info("PCA9685 servo controller initialized")
    
    def _init_hardware(self) -> None:
        """Initialize PCA9685 hardware."""
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(self.i2c, address=self.address)
            self.pca.frequency = 50
            self._create_servos()
        except Exception as e:
            raise HardwareException(f"PCA9685 initialization failed: {e}")
    
    def _create_servos(self) -> None:
        """Create servo objects with calibrated pulse ranges."""
        self.servos[0] = servo.Servo(
            self.pca.channels[0],
            min_pulse=int(SERVO_PAN_0_PULSE * 1000),
            max_pulse=int(SERVO_PAN_180_PULSE * 1000)
        )
        
        self.servos[1] = servo.Servo(
            self.pca.channels[1],
            min_pulse=int(SERVO_TILT_0_PULSE * 1000),
            max_pulse=int(SERVO_TILT_180_PULSE * 1000)
        )
        
        self.current_angles = {0: SERVO_DEFAULT_ANGLE, 1: SERVO_DEFAULT_ANGLE}
        self.logger.info("Created servos with calibrated pulse ranges")
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle with validation and calibration."""
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        
        _validate_angle(angle)
        angle = _handle_jitter_zone(angle, self.logger)
        
        offset = self.calibration_offsets.get(channel, 0.0)
        adjusted_angle = _apply_calibration(angle, offset)
        
        self.servos[channel].angle = adjusted_angle
        self.current_angles[channel] = angle
        
        self.logger.debug(f"Servo {channel} set to {angle}° (adjusted: {adjusted_angle}°)")
    
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle."""
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        return self.current_angles.get(channel, SERVO_DEFAULT_ANGLE)
    
    async def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Move servo smoothly to target angle."""
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        await _smooth_move_implementation(self, channel, target_angle, speed)
    
    def emergency_stop(self) -> None:
        """Emergency stop - servos maintain current positions."""
        self.logger.warning("Emergency stop activated")
    
    def set_calibration_offset(self, channel: int, offset: float) -> None:
        """Set calibration offset for servo."""
        if channel not in self.servos:
            raise HardwareException(f"Invalid channel: {channel}")
        self.calibration_offsets[channel] = offset
        self.logger.info(f"Calibration offset for servo {channel}: {offset}°")
    
    def get_calibration_offset(self, channel: int) -> float:
        """Get calibration offset for servo."""
        return self.calibration_offsets.get(channel, 0.0)
    
    def shutdown(self) -> None:
        """Shutdown the controller."""
        self.logger.info("Shutting down servo controller")
    
    def get_controller_type(self) -> str:
        """Get controller type."""
        return "PCA9685"
    
    def get_available_channels(self) -> list[int]:
        """Get available servo channels."""
        return list(self.servos.keys())


class GPIOServoController:
    """GPIO-based servo controller for direct pin control."""
    
    def __init__(self, servo_pins: Optional[Dict[int, int]] = None):
        self.logger = logging.getLogger(__name__)
        self.servo_pins = servo_pins or {0: 18, 1: 19}
        self.current_angles: Dict[int, float] = {}
        self.calibration_offsets: Dict[int, float] = {}
        self.gpio_available = False
        
        self._init_gpio()
        self.logger.info("GPIO servo controller initialized")
    
    def _init_gpio(self) -> None:
        """Initialize GPIO pins."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            
            for channel, pin in self.servo_pins.items():
                GPIO.setup(pin, GPIO.OUT)
                self.current_angles[channel] = SERVO_DEFAULT_ANGLE
            
            self.gpio = GPIO
            self.gpio_available = True
            
        except ImportError:
            self.logger.warning("RPi.GPIO not available - simulation mode")
        except Exception as e:
            self.logger.error(f"GPIO initialization failed: {e}")
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle using GPIO PWM."""
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        _validate_angle(angle)
        angle = _handle_jitter_zone(angle, self.logger)
        
        offset = self.calibration_offsets.get(channel, 0.0)
        adjusted_angle = _apply_calibration(angle, offset)
        
        self._set_pwm_for_angle(channel, adjusted_angle)
        self.current_angles[channel] = angle
        
        self.logger.debug(f"GPIO Servo {channel} set to {angle}°")
    
    def _set_pwm_for_angle(self, channel: int, angle: float) -> None:
        """Set PWM for servo angle using calibrated values."""
        if channel == 0:
            min_pulse = SERVO_PAN_0_PULSE
            center_pulse = SERVO_PAN_90_PULSE
            max_pulse = SERVO_PAN_180_PULSE
        elif channel == 1:
            min_pulse = SERVO_TILT_0_PULSE
            center_pulse = SERVO_TILT_90_PULSE
            max_pulse = SERVO_TILT_180_PULSE
        else:
            min_pulse = 0.4
            center_pulse = 1.45
            max_pulse = 2.7
        
        if angle <= 0:
            pulse_width_ms = min_pulse
        elif angle >= 180:
            pulse_width_ms = max_pulse
        elif angle == 90:
            pulse_width_ms = center_pulse
        else:
            if angle < 90:
                ratio = angle / 90.0
                pulse_width_ms = min_pulse + (center_pulse - min_pulse) * ratio
            else:
                ratio = (angle - 90) / 90.0
                pulse_width_ms = center_pulse + (max_pulse - center_pulse) * ratio
        
        duty_cycle = pulse_width_ms / 20.0
        
        if self.gpio_available:
            pin = self.servo_pins[channel]
            pwm = self.gpio.PWM(pin, 50)
            pwm.start(duty_cycle * 100)
            time.sleep(0.1)
            pwm.stop()
        else:
            self.logger.debug(f"SIMULATION: GPIO Servo {channel} -> {angle}° (pulse: {pulse_width_ms:.3f}ms)")
    
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle."""
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        return self.current_angles.get(channel, SERVO_DEFAULT_ANGLE)
    
    async def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Move servo smoothly to target angle."""
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        await _smooth_move_implementation(self, channel, target_angle, speed)
    
    def emergency_stop(self) -> None:
        """Emergency stop."""
        self.logger.warning("Emergency stop activated")
        if self.gpio_available:
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
        if self.gpio_available:
            self.gpio.cleanup()
    
    def get_controller_type(self) -> str:
        """Get controller type."""
        return "GPIO"
    
    def get_available_channels(self) -> list[int]:
        """Get available servo channels."""
        return list(self.servo_pins.keys())


if __name__ == "__main__":
    async def demo():
        """Demo PCA9685 servo controller."""
        import logging
        logging.basicConfig(level=logging.INFO)
        
        try:
            controller = PCA9685ServoController()
            print(f"Initialized {controller.get_controller_type()} controller")
            print(f"Available channels: {controller.get_available_channels()}")
            
            for channel in controller.get_available_channels():
                print(f"\nTesting servo on channel {channel}")
                
                print("Moving to 0°...")
                controller.set_servo_angle(channel, 0)
                await asyncio.sleep(1)
                
                print("Moving to 60°...")
                await controller.smooth_move_to_angle(channel, 60, speed=0.5)
                await asyncio.sleep(1)
                
                print(f"Current angle: {controller.get_servo_angle(channel)}°")
            
            controller.shutdown()
            print("Demo completed")
            
        except Exception as e:
            print(f"Demo failed: {e}")
    
    asyncio.run(demo())