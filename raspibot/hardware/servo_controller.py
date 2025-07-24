"""PCA9685 and GPIO servo controller implementations.

This module provides real hardware servo control using either the PCA9685
PWM controller or direct GPIO control with safety features and calibration support.
Uses Adafruit CircuitPython libraries when available, falls back to smbus2 for PCA9685.
Uses RPi.GPIO for direct GPIO servo control.
"""

import time
import math
from typing import Dict, Optional

from raspibot.exceptions import HardwareException
from raspibot.utils.logging_config import setup_logging
from raspibot.hardware.servo_interface import ServoInterface
from raspibot.config.hardware_config import (
    I2C_BUS,
    PCA9685_ADDRESS,
    SERVO_MIN_ANGLE,
    SERVO_MAX_ANGLE,
    SERVO_DEFAULT_ANGLE,
    SERVO_CHANNELS,
    GPIO_SERVO_MIN_ANGLE,
    GPIO_SERVO_MAX_ANGLE,
    GPIO_SERVO_DEFAULT_ANGLE,
    GPIO_SERVO_FREQUENCY,
    GPIO_SERVO_MIN_PULSE,
    GPIO_SERVO_MAX_PULSE,
    GPIO_SERVO_PINS,
    GPIO_SERVO_DEADBAND,
    GPIO_SERVO_STABILIZATION_DELAY,
    GPIO_SERVO_MIN_STEP_SIZE,
    GPIO_SERVO_MAX_STEP_SIZE,
    GPIO_SERVO_STEP_DELAY,
    GPIO_SERVO_DUTY_CYCLE_PRECISION,
    PCA9685_DEADBAND,
    PCA9685_STABILIZATION_DELAY,
    PCA9685_MIN_STEP_SIZE,
    PCA9685_MAX_STEP_SIZE,
    PCA9685_STEP_DELAY,
    PCA9685_PWM_PRECISION,
)


class PCA9685ServoController(ServoInterface):
    """Real PCA9685 servo controller implementation using Adafruit libraries or smbus2."""
    
    def __init__(self, i2c_bus: int = I2C_BUS, address: int = PCA9685_ADDRESS):
        """Initialize PCA9685 controller.
        
        Args:
            i2c_bus: I2C bus number (default from config)
            address: PCA9685 I2C address (default 0x40)
        """
        self.logger = setup_logging(__name__)
        self.i2c_bus = i2c_bus
        self.address = address
        self.calibration_offsets: Dict[int, float] = {}
        self.current_angles: Dict[int, float] = {}
        self.pca9685 = None
        self.bus = None
        self.use_adafruit = False
        
        # Try to initialize with Adafruit libraries first
        if self._init_adafruit():
            self.use_adafruit = True
            self.logger.info("Using Adafruit CircuitPython libraries")
        else:
            # Fall back to smbus2
            if self._init_smbus():
                self.logger.info("Using smbus2 for I2C communication")
            else:
                self.logger.warning("Hardware not available - running in simulation mode")
    
    def _init_adafruit(self) -> bool:
        """Initialize using Adafruit libraries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import Adafruit libraries
            import board
            import busio
            from adafruit_pca9685 import PCA9685
            
            # Create I2C bus
            if self.i2c_bus == 1:
                i2c = busio.I2C(board.SCL, board.SDA)
            else:
                return False
            
            # Create PCA9685 instance
            self.pca9685 = PCA9685(i2c, address=self.address)
            
            # Set PWM frequency for servos (50Hz)
            self.pca9685.frequency = 50
            
            # Initialize all channels to center position
            for channel in SERVO_CHANNELS:
                self.current_angles[channel] = SERVO_DEFAULT_ANGLE
                self._set_pwm_for_angle(channel, SERVO_DEFAULT_ANGLE)
            
            self.logger.info(f"PCA9685 initialized with Adafruit on bus {self.i2c_bus}, address 0x{self.address:02x}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Adafruit initialization failed: {e}")
            return False
    
    def _init_smbus(self) -> bool:
        """Initialize using smbus2.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from smbus2 import SMBus
            
            # Create I2C bus
            self.bus = SMBus(self.i2c_bus)
            
            # Reset PCA9685
            self._reset()
            
            # Set PWM frequency for servos (50Hz)
            self._set_pwm_frequency(50)
            
            # Initialize all channels to center position
            for channel in SERVO_CHANNELS:
                self.current_angles[channel] = SERVO_DEFAULT_ANGLE
                self._set_pwm_for_angle(channel, SERVO_DEFAULT_ANGLE)
            
            self.logger.info(f"PCA9685 initialized with smbus2 on bus {self.i2c_bus}, address 0x{self.address:02x}")
            return True
            
        except Exception as e:
            self.logger.debug(f"smbus2 initialization failed: {e}")
            if self.bus:
                self.bus.close()
                self.bus = None
            return False
    
    def _reset(self) -> None:
        """Reset the PCA9685 controller (smbus2 only)."""
        if self.bus is None:
            return
        
        # PCA9685 registers
        MODE1 = 0x00
        
        # Set MODE1 register to reset
        self.bus.write_byte_data(self.address, MODE1, 0x80)
        time.sleep(0.01)  # Wait for reset
    
    def _set_pwm_frequency(self, frequency: int) -> None:
        """Set PWM frequency (smbus2 only).
        
        Args:
            frequency: PWM frequency in Hz (50Hz for servos)
        """
        if self.bus is None:
            return
        
        # PCA9685 registers
        MODE1 = 0x00
        PRESCALE = 0xFE
        
        if not 40 <= frequency <= 1000:
            raise HardwareException(f"Invalid PWM frequency: {frequency}Hz")
        
        # Calculate prescale value
        prescale = int(round(25000000.0 / (4096.0 * frequency)) - 1)
        
        # Set prescale
        self.bus.write_byte_data(self.address, PRESCALE, prescale)
        
        # Set MODE1 to enable auto-increment
        self.bus.write_byte_data(self.address, MODE1, 0xA1)
        
        self.logger.debug(f"PWM frequency set to {frequency}Hz (prescale: {prescale})")
    
    def set_pwm_frequency(self, frequency: int) -> None:
        """Set PWM frequency.
        
        Args:
            frequency: PWM frequency in Hz (50Hz for servos)
        """
        if not 40 <= frequency <= 1000:
            raise HardwareException(f"Invalid PWM frequency: {frequency}Hz")
        
        if self.use_adafruit and self.pca9685 is not None:
            self.pca9685.frequency = frequency
            self.logger.debug(f"PWM frequency set to {frequency}Hz (Adafruit)")
        elif self.bus is not None:
            self._set_pwm_frequency(frequency)
        else:
            self.logger.warning("Hardware not available - frequency setting simulated")
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle directly without anti-jitter measures.
        
        Args:
            channel: Servo channel (0-15)
            angle: Target angle in degrees (0-180)
        """
        # Validate channel
        if not 0 <= channel <= 15:
            raise HardwareException(f"Invalid channel: {channel}")
        
        # Validate angle
        if not SERVO_MIN_ANGLE <= angle <= SERVO_MAX_ANGLE:
            raise HardwareException(f"Invalid angle: {angle}° (must be {SERVO_MIN_ANGLE}-{SERVO_MAX_ANGLE}°)")
        
        # Apply calibration offset
        offset = self.calibration_offsets.get(channel, 0.0)
        adjusted_angle = angle + offset
        
        # Clamp to valid range
        adjusted_angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, adjusted_angle))
        
        # Set PWM for the angle
        self._set_pwm_for_angle(channel, adjusted_angle)
        
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
        if not 0 <= channel <= 15:
            raise HardwareException(f"Invalid channel: {channel}")
        
        return self.current_angles.get(channel, SERVO_DEFAULT_ANGLE)
    
    def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Smooth movement to target angle with anti-jitter measures.
        
        Args:
            channel: Servo channel (0-15)
            target_angle: Target angle in degrees
            speed: Movement speed (0.1-1.0, where 1.0 is fastest)
        """
        if not 0.1 <= speed <= 1.0:
            speed = max(0.1, min(1.0, speed))
        
        current_angle = self.get_servo_angle(channel)
        angle_diff = target_angle - current_angle
        
        # Check if movement is needed
        if abs(angle_diff) < PCA9685_DEADBAND:
            self.logger.debug(f"Servo {channel} movement {abs(angle_diff):.1f}° below deadband, skipping")
            return
        
        # Calculate step size and delay for smoother movement
        max_step = PCA9685_MAX_STEP_SIZE * speed
        min_step = PCA9685_MIN_STEP_SIZE
        
        # Use more steps for smoother movement (at least 20 steps for large movements)
        num_steps = max(20, int(abs(angle_diff) / 2))  # At least 20 steps, or 1 step per 2 degrees
        step_size = abs(angle_diff) / num_steps
        
        # Ensure step size is within bounds
        step_size = max(min_step, min(max_step, step_size))
        
        # Move in steps
        current = current_angle
        step_delay = PCA9685_STEP_DELAY / speed  # Adjust delay based on speed
        
        self.logger.debug(f"Servo {channel} smooth move: {current_angle:.1f}° -> {target_angle:.1f}°, "
                         f"step_size={step_size:.2f}°, steps={num_steps}, step_delay={step_delay:.3f}s")
        
        while abs(current - target_angle) > PCA9685_DEADBAND:
            if current < target_angle:
                current = min(current + step_size, target_angle)
            else:
                current = max(current - step_size, target_angle)
            
            self.set_servo_angle(channel, current)
            time.sleep(step_delay)
        
        # Final position (skip deadband check for final position)
        self._set_pwm_for_angle(channel, target_angle)
        self.current_angles[channel] = target_angle
        time.sleep(PCA9685_STABILIZATION_DELAY)
        
        self.logger.debug(f"Servo {channel} smooth move completed: {target_angle:.1f}°")
    
    def emergency_stop(self) -> None:
        """Emergency stop all servos."""
        self.logger.warning("Emergency stop activated")
        
        if self.use_adafruit and self.pca9685 is not None:
            for channel in range(16):
                try:
                    self.pca9685.channels[channel].duty_cycle = 0
                except Exception as e:
                    self.logger.error(f"Failed to stop servo {channel}: {e}")
        elif self.bus is not None:
            # PCA9685 registers
            LED0_ON_L = 0x06
            LED0_ON_H = 0x07
            LED0_OFF_L = 0x08
            LED0_OFF_H = 0x09
            
            for channel in range(16):
                try:
                    # Calculate register addresses for this channel
                    on_l = LED0_ON_L + (4 * channel)
                    on_h = LED0_ON_H + (4 * channel)
                    off_l = LED0_OFF_L + (4 * channel)
                    off_h = LED0_OFF_H + (4 * channel)
                    
                    # Set PWM values to 0 (stop)
                    self.bus.write_byte_data(self.address, on_l, 0)
                    self.bus.write_byte_data(self.address, on_h, 0)
                    self.bus.write_byte_data(self.address, off_l, 0)
                    self.bus.write_byte_data(self.address, off_h, 0)
                except Exception as e:
                    self.logger.error(f"Failed to stop servo {channel}: {e}")
        else:
            self.logger.warning("Hardware not available - emergency stop simulated")
    
    def set_calibration_offset(self, channel: int, offset: float) -> None:
        """Set calibration offset for a servo.
        
        Args:
            channel: Servo channel (0-15)
            offset: Angle offset in degrees
        """
        if not 0 <= channel <= 15:
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
    
    def _set_pwm_for_angle(self, channel: int, angle: float) -> None:
        """Set PWM duty cycle for servo angle with improved precision.
        
        Args:
            channel: Servo channel (0-15)
            angle: Angle in degrees
        """
        if self.use_adafruit and self.pca9685 is not None:
            # Convert angle to pulse width with improved precision
            # 0° = 1ms pulse, 180° = 2ms pulse
            # At 50Hz, 1ms = 0.05 duty cycle, 2ms = 0.1 duty cycle
            
            pulse_width_ms = 1.0 + (angle / 180.0)  # 1ms to 2ms
            duty_cycle = pulse_width_ms / 20.0  # 20ms period at 50Hz
            
            # Apply precision rounding to reduce jitter
            duty_cycle = round(duty_cycle, PCA9685_PWM_PRECISION)
            
            # Convert to 16-bit value (0-65535)
            pwm_value = int(duty_cycle * 65535)
            
            # Clamp to valid range
            pwm_value = max(0, min(65535, pwm_value))
            
            # Set PWM using Adafruit library
            self.pca9685.channels[channel].duty_cycle = pwm_value
            
        elif self.bus is not None:
            # Convert angle to pulse width with improved precision
            # 0° = 1ms pulse, 180° = 2ms pulse
            # At 50Hz, 1ms = 0.05 duty cycle, 2ms = 0.1 duty cycle
            
            pulse_width_ms = 1.0 + (angle / 180.0)  # 1ms to 2ms
            duty_cycle = pulse_width_ms / 20.0  # 20ms period at 50Hz
            
            # Apply precision rounding to reduce jitter
            duty_cycle = round(duty_cycle, PCA9685_PWM_PRECISION)
            
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
            self.bus.write_byte_data(self.address, on_l, 0)
            self.bus.write_byte_data(self.address, on_h, 0)
            self.bus.write_byte_data(self.address, off_l, pwm_value & 0xFF)
            self.bus.write_byte_data(self.address, off_h, (pwm_value >> 8) & 0xFF)
            
        else:
            # Simulation mode - just log the action
            self.logger.debug(f"SIMULATION: Servo {channel} would move to {angle}°")
    
    def shutdown(self) -> None:
        """Shutdown the servo controller safely."""
        self.logger.info("Shutting down servo controller")
        
        # Move all servos to center position
        for channel in SERVO_CHANNELS:
            try:
                self.set_servo_angle(channel, SERVO_DEFAULT_ANGLE)
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Failed to center servo {channel}: {e}")
        
        # Stop all PWM outputs
        self.emergency_stop()
        
        # Close I2C bus if using smbus2
        if self.bus:
            self.bus.close() 
    
    def get_controller_type(self) -> str:
        """Get the type of controller.
        
        Returns:
            Controller type string
        """
        return "PCA9685"
    
    def get_available_channels(self) -> list[int]:
        """Get list of available servo channels.
        
        Returns:
            List of available channel numbers
        """
        return list(SERVO_CHANNELS)


class GPIOServoController(ServoInterface):
    """GPIO-based servo controller implementation using RPi.GPIO PWM."""
    
    def __init__(self, servo_pins: Optional[Dict[int, int]] = None):
        """Initialize GPIO servo controller.
        
        Args:
            servo_pins: Dictionary mapping servo channels to GPIO pins.
                       If None, uses GPIO_SERVO_PINS from config.
                       Format: {channel: gpio_pin}
                       Example: {0: 17, 1: 18} for servos on GPIO 17 and 18
        """
        self.logger = setup_logging(__name__)
        self.servo_pins = servo_pins or GPIO_SERVO_PINS.copy()
        self.calibration_offsets: Dict[int, float] = {}
        self.current_angles: Dict[int, float] = {}
        self.pwm_objects: Dict[int, any] = {}
        self.gpio_initialized = False
        
        # Validate servo pins
        if not self.servo_pins:
            raise HardwareException("No servo pins configured")
        
        # Initialize GPIO and PWM
        if self._init_gpio():
            self.logger.info(f"GPIO servo controller initialized with pins: {self.servo_pins}")
        else:
            self.logger.warning("GPIO not available - running in simulation mode")
    
    def _init_gpio(self) -> bool:
        """Initialize GPIO and PWM for servo control.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import RPi.GPIO as GPIO
            
            # Set GPIO mode to BCM numbering
            GPIO.setmode(GPIO.BCM)
            
            # Setup GPIO pins and PWM
            for channel, pin in self.servo_pins.items():
                # Setup pin as output
                GPIO.setup(pin, GPIO.OUT)
                
                # Create PWM object
                pwm = GPIO.PWM(pin, GPIO_SERVO_FREQUENCY)
                pwm.start(0)  # Start with 0% duty cycle
                
                self.pwm_objects[channel] = pwm
                
                # Initialize to default angle
                self.current_angles[channel] = GPIO_SERVO_DEFAULT_ANGLE
                self._set_pwm_for_angle(channel, GPIO_SERVO_DEFAULT_ANGLE)
            
            self.gpio_initialized = True
            return True
            
        except Exception as e:
            self.logger.debug(f"GPIO initialization failed: {e}")
            return False
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle with validation and anti-jitter measures.
        
        Args:
            channel: Servo channel (must be in servo_pins)
            angle: Target angle in degrees (0-270)
        """
        # Validate channel
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        # Validate angle
        if not GPIO_SERVO_MIN_ANGLE <= angle <= GPIO_SERVO_MAX_ANGLE:
            raise HardwareException(
                f"Invalid angle: {angle}° (must be {GPIO_SERVO_MIN_ANGLE}-{GPIO_SERVO_MAX_ANGLE}°)"
            )
        
        # Get current angle
        current_angle = self.current_angles.get(channel, GPIO_SERVO_DEFAULT_ANGLE)
        
        # Check deadband to prevent jitter
        angle_diff = abs(angle - current_angle)
        if angle_diff < GPIO_SERVO_DEADBAND:
            self.logger.debug(f"Angle change {angle_diff}° below deadband {GPIO_SERVO_DEADBAND}°, ignoring")
            return
        
        # Apply calibration offset
        offset = self.calibration_offsets.get(channel, 0.0)
        adjusted_angle = angle + offset
        
        # Clamp to valid range
        adjusted_angle = max(GPIO_SERVO_MIN_ANGLE, min(GPIO_SERVO_MAX_ANGLE, adjusted_angle))
        
        # Set PWM for the angle
        self._set_pwm_for_angle(channel, adjusted_angle)
        
        # Update current angle
        self.current_angles[channel] = angle
        
        # Add stabilization delay to reduce jitter
        time.sleep(GPIO_SERVO_STABILIZATION_DELAY)
        
        self.logger.debug(f"GPIO Servo {channel} (pin {self.servo_pins[channel]}) set to {angle}° (adjusted: {adjusted_angle}°)")
    
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle.
        
        Args:
            channel: Servo channel (must be in servo_pins)
            
        Returns:
            Current angle in degrees
        """
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        return self.current_angles.get(channel, GPIO_SERVO_DEFAULT_ANGLE)
    
    def set_pwm_frequency(self, frequency: int) -> None:
        """Set PWM frequency (GPIO limitation: frequency affects all servos).
        
        Args:
            frequency: PWM frequency in Hz (50Hz recommended for servos)
        """
        if not 40 <= frequency <= 1000:
            raise HardwareException(f"Invalid PWM frequency: {frequency}Hz")
        
        if self.gpio_initialized:
            # Note: Changing frequency affects all PWM objects
            # This is a limitation of RPi.GPIO software PWM
            self.logger.warning("GPIO PWM frequency change affects all servos")
            
            # Recreate PWM objects with new frequency
            for channel, pwm in self.pwm_objects.items():
                current_angle = self.get_servo_angle(channel)
                pwm.stop()
                
                import RPi.GPIO as GPIO
                new_pwm = GPIO.PWM(self.servo_pins[channel], frequency)
                new_pwm.start(0)
                self.pwm_objects[channel] = new_pwm
                
                # Restore angle
                self._set_pwm_for_angle(channel, current_angle)
            
            self.logger.debug(f"PWM frequency changed to {frequency}Hz")
        else:
            self.logger.warning("GPIO not available - frequency setting simulated")
    
    def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Smooth movement to target angle with anti-jitter measures.
        
        Args:
            channel: Servo channel (must be in servo_pins)
            target_angle: Target angle in degrees
            speed: Movement speed (0.7-1.0, where 1.0 is fastest and smoothest)
        """
        if not 0.7 <= speed <= 1.0:
            speed = max(0.7, min(1.0, speed))
        
        current_angle = self.get_servo_angle(channel)
        angle_diff = target_angle - current_angle
        
        # Check if movement is needed
        if abs(angle_diff) < GPIO_SERVO_DEADBAND:
            self.logger.debug(f"Movement {angle_diff}° below deadband, skipping")
            return
        
        # Calculate optimal step size for smooth movement
        total_steps = max(5, int(abs(angle_diff) / GPIO_SERVO_MIN_STEP_SIZE))  # At least 5 steps
        step_size = abs(angle_diff) / total_steps
        
        # Apply speed factor and clamp to limits
        step_size = step_size * speed
        step_size = max(GPIO_SERVO_MIN_STEP_SIZE, min(GPIO_SERVO_MAX_STEP_SIZE, step_size))
        
        # Calculate step delay for smooth movement
        step_delay = GPIO_SERVO_STEP_DELAY / speed
        
        self.logger.debug(f"Smooth movement: {current_angle}° to {target_angle}° in {total_steps} steps of {step_size:.2f}°")
        
        # Move in steps
        current = current_angle
        while abs(current - target_angle) > GPIO_SERVO_DEADBAND:
            if current < target_angle:
                current = min(current + step_size, target_angle)
            else:
                current = max(current - step_size, target_angle)
            
            # Use direct PWM setting to avoid deadband checks during smooth movement
            self._set_pwm_for_angle_direct(channel, current)
            time.sleep(step_delay)
        
        # Final position with full validation
        self.set_servo_angle(channel, target_angle)
    
    def emergency_stop(self) -> None:
        """Emergency stop all servos."""
        self.logger.warning("GPIO Emergency stop activated")
        
        if self.gpio_initialized:
            for channel, pwm in self.pwm_objects.items():
                try:
                    pwm.ChangeDutyCycle(0)  # Stop PWM
                except Exception as e:
                    self.logger.error(f"Failed to stop GPIO servo {channel}: {e}")
        else:
            self.logger.warning("GPIO not available - emergency stop simulated")
    
    def set_calibration_offset(self, channel: int, offset: float) -> None:
        """Set calibration offset for a servo.
        
        Args:
            channel: Servo channel (must be in servo_pins)
            offset: Angle offset in degrees
        """
        if channel not in self.servo_pins:
            raise HardwareException(f"Invalid channel: {channel}")
        
        self.calibration_offsets[channel] = offset
        self.logger.info(f"GPIO Calibration offset for servo {channel}: {offset}°")
    
    def get_calibration_offset(self, channel: int) -> float:
        """Get calibration offset for a servo.
        
        Args:
            channel: Servo channel (must be in servo_pins)
            
        Returns:
            Calibration offset in degrees
        """
        return self.calibration_offsets.get(channel, 0.0)
    
    def _set_pwm_for_angle(self, channel: int, angle: float) -> None:
        """Set PWM duty cycle for servo angle with precision control.
        
        Args:
            channel: Servo channel (must be in servo_pins)
            angle: Angle in degrees (0-270)
        """
        if self.gpio_initialized and channel in self.pwm_objects:
            # Convert angle to pulse width with improved precision
            # 0° = 0.5ms pulse, 270° = 2.5ms pulse
            # Linear interpolation between min and max pulse widths
            pulse_width_ms = GPIO_SERVO_MIN_PULSE + (angle / GPIO_SERVO_MAX_ANGLE) * (GPIO_SERVO_MAX_PULSE - GPIO_SERVO_MIN_PULSE)
            
            # Convert to duty cycle percentage with precision control
            # At 50Hz, period is 20ms
            duty_cycle = (pulse_width_ms / 20.0) * 100.0
            
            # Round to specified precision to reduce jitter
            duty_cycle = round(duty_cycle, GPIO_SERVO_DUTY_CYCLE_PRECISION)
            
            # Clamp to valid range (0-100%)
            duty_cycle = max(0.0, min(100.0, duty_cycle))
            
            # Set PWM using RPi.GPIO
            self.pwm_objects[channel].ChangeDutyCycle(duty_cycle)
            
        else:
            # Simulation mode - just log the action
            self.logger.debug(f"GPIO SIMULATION: Servo {channel} would move to {angle}°")
    
    def _set_pwm_for_angle_direct(self, channel: int, angle: float) -> None:
        """Set PWM duty cycle directly without validation (for smooth movement).
        
        Args:
            channel: Servo channel (must be in servo_pins)
            angle: Angle in degrees (0-270)
        """
        if self.gpio_initialized and channel in self.pwm_objects:
            # Convert angle to pulse width
            pulse_width_ms = GPIO_SERVO_MIN_PULSE + (angle / GPIO_SERVO_MAX_ANGLE) * (GPIO_SERVO_MAX_PULSE - GPIO_SERVO_MIN_PULSE)
            
            # Convert to duty cycle percentage
            duty_cycle = (pulse_width_ms / 20.0) * 100.0
            
            # Round to specified precision
            duty_cycle = round(duty_cycle, GPIO_SERVO_DUTY_CYCLE_PRECISION)
            
            # Clamp to valid range
            duty_cycle = max(0.0, min(100.0, duty_cycle))
            
            # Set PWM directly without logging or delays
            self.pwm_objects[channel].ChangeDutyCycle(duty_cycle)
    
    def shutdown(self) -> None:
        """Shutdown the GPIO servo controller safely."""
        self.logger.info("Shutting down GPIO servo controller")
        
        # Move all servos to center position
        for channel in self.servo_pins:
            try:
                self.set_servo_angle(channel, GPIO_SERVO_DEFAULT_ANGLE)
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Failed to center GPIO servo {channel}: {e}")
        
        # Stop all PWM outputs
        self.emergency_stop()
        
        # Clean up GPIO
        if self.gpio_initialized:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
                self.logger.info("GPIO cleanup completed")
            except Exception as e:
                self.logger.error(f"Error during GPIO cleanup: {e}")
    
    def get_controller_type(self) -> str:
        """Get the type of controller.
        
        Returns:
            Controller type string
        """
        return "GPIO"
    
    def get_available_channels(self) -> list[int]:
        """Get list of available servo channels.
        
        Returns:
            List of available channel numbers
        """
        return list(self.servo_pins.keys()) 