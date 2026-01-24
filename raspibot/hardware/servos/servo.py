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
    PCA9685_PRESCALE,
    SERVO_MIN_ANGLE,
    SERVO_MAX_ANGLE,
    SERVO_DEFAULT_ANGLE,
    SERVO_CONFIGS,
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
        raise HardwareException(
            f"Invalid angle: {angle}° (must be {SERVO_MIN_ANGLE}-{SERVO_MAX_ANGLE}°)"
        )


def _handle_jitter_zone(angle: float, logger: logging.Logger) -> float:
    """Handle problematic jitter zone by adjusting angle."""
    if 87 <= angle <= 104:
        logger.warning(f"JITTER ZONE: Adjusting angle {angle}° to avoid jitter")
        adjusted = 86 if angle <= 95 else 105
        logger.info(f"Adjusted angle to {adjusted}°")
        return adjusted
    return angle


def _apply_calibration(angle: float, offset: float) -> float:
    """Apply calibration offset and clamp to valid range."""
    adjusted = angle + offset
    return max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, adjusted))


async def _smooth_move_implementation(
    servo_controller, name: str, target_angle: float, speed: float
) -> None:
    """Shared smooth movement implementation."""
    _validate_angle(target_angle)
    speed = max(0.1, min(1.0, speed))

    current_angle = servo_controller.get_servo_angle(name)
    angle_diff = target_angle - current_angle

    if abs(angle_diff) < 0.5:
        return

    steps = max(10, int(abs(angle_diff) / 2))
    step_size = angle_diff / steps
    step_delay = 0.02 / speed

    for i in range(steps):
        servo_controller.set_servo_angle(name, current_angle + (step_size * i))
        await asyncio.sleep(step_delay)

    servo_controller.set_servo_angle(name, target_angle)
    await asyncio.sleep(0.1)


class PCA9685ServoController:
    """PCA9685 servo controller using Adafruit libraries."""

    def __init__(self, i2c_bus: int = I2C_BUS, address: int = PCA9685_ADDRESS):
        self.logger = logging.getLogger(__name__)
        self.address = address
        self.i2c_bus = i2c_bus

        self.pca = None
        self.servos: Dict[str, servo.Servo] = {}
        self.current_angles: Dict[str, float] = {}
        self.calibration_offsets: Dict[str, float] = {}

        if not ADAFRUIT_AVAILABLE:
            raise HardwareException("Adafruit libraries not available")

        self._init_hardware()
        self.logger.info("PCA9685 servo controller initialized")

    def _init_hardware(self) -> None:
        """Initialize PCA9685 hardware with calibrated prescale."""
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(self.i2c, address=self.address)
            self.pca.frequency = 50
            # Override prescale with calibrated value for this board's oscillator
            # Standard prescale=121 for 50Hz, but this board runs ~8% fast
            self._set_calibrated_prescale()
            self._create_servos()
        except Exception as e:
            raise HardwareException(f"PCA9685 initialization failed: {e}")

    def _set_calibrated_prescale(self) -> None:
        """Set calibrated prescale value to compensate for oscillator drift."""
        import smbus2
        mode1_reg = 0x00
        prescale_reg = 0xFE
        bus = smbus2.SMBus(I2C_BUS)
        try:
            # Enter sleep mode to set prescale
            old_mode = bus.read_byte_data(self.address, mode1_reg)
            bus.write_byte_data(self.address, mode1_reg, (old_mode & 0x7F) | 0x10)
            bus.write_byte_data(self.address, prescale_reg, PCA9685_PRESCALE)
            bus.write_byte_data(self.address, mode1_reg, old_mode)
            time.sleep(0.005)
            bus.write_byte_data(self.address, mode1_reg, old_mode | 0x80)
            self.logger.info(f"PCA9685 prescale set to {PCA9685_PRESCALE} (calibrated)")
        finally:
            bus.close()

    def _create_servos(self) -> None:
        """Create servo objects from SERVO_CONFIGS."""
        for name, config in SERVO_CONFIGS.items():
            channel = config["channel"]
            self.servos[name] = servo.Servo(
                self.pca.channels[channel],
                min_pulse=int(config["min_pulse"] * 1000),
                max_pulse=int(config["max_pulse"] * 1000),
            )
            self.current_angles[name] = config.get("default_angle", SERVO_DEFAULT_ANGLE)
            self.logger.info(f"Created servo '{name}' on channel {channel:#x}")

    def set_servo_angle(self, name: str, angle: float) -> None:
        """Set servo angle with validation and calibration.

        Args:
            name: Servo name (e.g., "pan", "tilt") - must match SERVO_CONFIGS key.
            angle: Target angle in degrees.

        Raises:
            HardwareException: If servo name is not found in SERVO_CONFIGS.
        """
        if name not in self.servos:
            available = list(self.servos.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")

        _validate_angle(angle)
        if name == "pan":
            angle = _handle_jitter_zone(angle, self.logger)

        offset = self.calibration_offsets.get(name, 0.0)
        adjusted_angle = _apply_calibration(angle, offset)

        self.servos[name].angle = adjusted_angle
        self.current_angles[name] = angle

        self.logger.debug(f"Servo '{name}' set to {angle}° (adjusted: {adjusted_angle}°)")

    def get_servo_angle(self, name: str) -> float:
        """Get current servo angle."""
        if name not in self.servos:
            available = list(self.servos.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")
        return self.current_angles.get(name, SERVO_DEFAULT_ANGLE)

    async def smooth_move_to_angle(
        self, name: str, target_angle: float, speed: float = 1.0
    ) -> None:
        """Move servo smoothly to target angle."""
        if name not in self.servos:
            available = list(self.servos.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")
        await _smooth_move_implementation(self, name, target_angle, speed)

    def emergency_stop(self) -> None:
        """Emergency stop - servos maintain current positions."""
        self.logger.warning("Emergency stop activated")

    def set_calibration_offset(self, name: str, offset: float) -> None:
        """Set calibration offset for servo."""
        if name not in self.servos:
            available = list(self.servos.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")
        self.calibration_offsets[name] = offset
        self.logger.info(f"Calibration offset for servo '{name}': {offset}°")

    def get_calibration_offset(self, name: str) -> float:
        """Get calibration offset for servo."""
        return self.calibration_offsets.get(name, 0.0)

    def shutdown(self) -> None:
        """Shutdown the controller."""
        self.logger.info("Shutting down servo controller")

    def get_controller_type(self) -> str:
        """Get controller type."""
        return "PCA9685"

    def get_available_servos(self) -> list[str]:
        """Get available servo names."""
        return list(self.servos.keys())


class GPIOServoController:
    """GPIO-based servo controller for direct pin control."""

    def __init__(self, servo_pins: Optional[Dict[str, int]] = None):
        """Initialize GPIO servo controller.

        Args:
            servo_pins: Mapping of servo names to GPIO pin numbers (BCM).
                       Defaults to {"pan": 17, "tilt": 18}.
        """
        self.logger = logging.getLogger(__name__)
        self.servo_pins: Dict[str, int] = servo_pins or {"pan": 17, "tilt": 18}
        self.current_angles: Dict[str, float] = {}
        self.calibration_offsets: Dict[str, float] = {}
        self.gpio_available = False

        self._init_gpio()
        self.logger.info("GPIO servo controller initialized")

    def _init_gpio(self) -> None:
        """Initialize GPIO pins."""
        try:
            import RPi.GPIO as GPIO

            GPIO.setmode(GPIO.BCM)

            for name, pin in self.servo_pins.items():
                GPIO.setup(pin, GPIO.OUT)
                config = SERVO_CONFIGS.get(name, {})
                self.current_angles[name] = config.get("default_angle", SERVO_DEFAULT_ANGLE)

            self.gpio = GPIO
            self.gpio_available = True

        except ImportError:
            self.logger.warning("RPi.GPIO not available - simulation mode")
        except Exception as e:
            self.logger.error(f"GPIO initialization failed: {e}")

    def set_servo_angle(self, name: str, angle: float) -> None:
        """Set servo angle using GPIO PWM."""
        if name not in self.servo_pins:
            available = list(self.servo_pins.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")

        _validate_angle(angle)
        if name == "pan":
            angle = _handle_jitter_zone(angle, self.logger)

        offset = self.calibration_offsets.get(name, 0.0)
        adjusted_angle = _apply_calibration(angle, offset)

        self._set_pwm_for_angle(name, adjusted_angle)
        self.current_angles[name] = angle

        self.logger.debug(f"GPIO Servo '{name}' set to {angle}°")

    def _set_pwm_for_angle(self, name: str, angle: float) -> None:
        """Set PWM for servo angle using calibrated values from SERVO_CONFIGS."""
        config = SERVO_CONFIGS.get(name, {})
        min_pulse = config.get("min_pulse", 0.4)
        center_pulse = config.get("center_pulse", 1.45)
        max_pulse = config.get("max_pulse", 2.7)

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
            pin = self.servo_pins[name]
            pwm = self.gpio.PWM(pin, 50)
            pwm.start(duty_cycle * 100)
            time.sleep(0.1)
            pwm.stop()
        else:
            self.logger.debug(
                f"SIMULATION: GPIO Servo '{name}' -> {angle}° (pulse: {pulse_width_ms:.3f}ms)"
            )

    def get_servo_angle(self, name: str) -> float:
        """Get current servo angle."""
        if name not in self.servo_pins:
            available = list(self.servo_pins.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")
        return self.current_angles.get(name, SERVO_DEFAULT_ANGLE)

    async def smooth_move_to_angle(
        self, name: str, target_angle: float, speed: float = 1.0
    ) -> None:
        """Move servo smoothly to target angle."""
        if name not in self.servo_pins:
            available = list(self.servo_pins.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")
        await _smooth_move_implementation(self, name, target_angle, speed)

    def emergency_stop(self) -> None:
        """Emergency stop."""
        self.logger.warning("Emergency stop activated")
        if self.gpio_available:
            for pin in self.servo_pins.values():
                self.gpio.output(pin, False)

    def set_calibration_offset(self, name: str, offset: float) -> None:
        """Set calibration offset."""
        if name not in self.servo_pins:
            available = list(self.servo_pins.keys())
            raise HardwareException(f"Unknown servo '{name}'. Available: {available}")
        self.calibration_offsets[name] = offset
        self.logger.info(f"Calibration offset for GPIO servo '{name}': {offset}°")

    def get_calibration_offset(self, name: str) -> float:
        """Get calibration offset."""
        return self.calibration_offsets.get(name, 0.0)

    def shutdown(self) -> None:
        """Shutdown the controller."""
        self.logger.info("Shutting down GPIO servo controller")
        if self.gpio_available:
            self.gpio.cleanup()

    def get_controller_type(self) -> str:
        """Get controller type."""
        return "GPIO"

    def get_available_servos(self) -> list[str]:
        """Get available servo names."""
        return list(self.servo_pins.keys())


if __name__ == "__main__":

    async def demo():
        """Demo PCA9685 servo controller."""
        import logging

        logging.basicConfig(level=logging.INFO)

        try:
            controller = PCA9685ServoController()
            print(f"Initialized {controller.get_controller_type()} controller")
            print(f"Available servos: {controller.get_available_servos()}")

            print("Moving pan to 60°...")
            controller.set_servo_angle("pan", 60)
            await asyncio.sleep(1)

            print("Moving tilt to 100°...")
            await controller.smooth_move_to_angle("tilt", 100, speed=0.5)
            await asyncio.sleep(1)

            print(f"Pan angle: {controller.get_servo_angle('pan')}°")
            print(f"Tilt angle: {controller.get_servo_angle('tilt')}°")

            controller.shutdown()
            print("Demo completed")

        except Exception as e:
            print(f"Demo failed: {e}")

    asyncio.run(demo())
