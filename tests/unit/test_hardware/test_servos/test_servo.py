"""Simplified unit tests for raspibot.hardware.servos.servo module with essential coverage."""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock

from raspibot.hardware.servos.servo import (
    _validate_angle,
    _handle_jitter_zone,
    _apply_calibration,
    _smooth_move_implementation,
    PCA9685ServoController,
    GPIOServoController
)
from raspibot.exceptions import HardwareException


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_validate_angle_valid_angles(self):
        """Test valid angles pass validation."""
        # Should not raise exception
        _validate_angle(0)
        _validate_angle(90)
        _validate_angle(180)
        _validate_angle(45.5)
    
    def test_validate_angle_invalid_angles(self):
        """Test invalid angles raise HardwareException."""
        with pytest.raises(HardwareException, match="Invalid angle"):
            _validate_angle(-1)
        
        with pytest.raises(HardwareException, match="Invalid angle"):
            _validate_angle(181)
    
    def test_handle_jitter_zone_in_zone(self):
        """Test angles 87-104 are adjusted."""
        logger = Mock()
        
        # Test lower end of jitter zone
        result = _handle_jitter_zone(90, logger)
        assert result == 86
        logger.warning.assert_called_once()
        
        logger.reset_mock()
        
        # Test upper end of jitter zone
        result = _handle_jitter_zone(100, logger)
        assert result == 105
        logger.warning.assert_called_once()
    
    def test_handle_jitter_zone_outside_zone(self):
        """Test angles outside zone unchanged."""
        logger = Mock()
        
        # Below jitter zone
        result = _handle_jitter_zone(45, logger)
        assert result == 45
        logger.warning.assert_not_called()
        
        # Above jitter zone
        result = _handle_jitter_zone(120, logger)
        assert result == 120
        logger.warning.assert_not_called()
    
    def test_apply_calibration_normal(self):
        """Test calibration offset application."""
        # Positive offset
        result = _apply_calibration(90, 5)
        assert result == 95
        
        # Negative offset
        result = _apply_calibration(90, -10)
        assert result == 80
        
        # Zero offset
        result = _apply_calibration(90, 0)
        assert result == 90
    
    def test_apply_calibration_clamping(self):
        """Test offset clamping to valid range."""
        # Should clamp to max
        result = _apply_calibration(170, 20)
        assert result == 180
        
        # Should clamp to min
        result = _apply_calibration(10, -20)
        assert result == 0


class TestSmoothMoveImplementation:
    """Test shared smooth movement implementation."""

    @pytest.mark.asyncio
    async def test_smooth_move_small_diff(self):
        """Test no movement for <0.5 degree difference."""
        mock_controller = Mock()
        mock_controller.get_servo_angle.return_value = 90.0

        await _smooth_move_implementation(mock_controller, "pan", 90.4, 1.0)

        # Should not call set_servo_angle since difference is < 0.5
        mock_controller.set_servo_angle.assert_not_called()

    @pytest.mark.asyncio
    async def test_smooth_move_normal(self):
        """Test step calculation and movement sequence."""
        mock_controller = Mock()
        mock_controller.get_servo_angle.return_value = 90.0

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await _smooth_move_implementation(mock_controller, "pan", 120.0, 1.0)

        # Should call set_servo_angle multiple times for smooth movement
        assert mock_controller.set_servo_angle.call_count > 1

        # Final call should be with target angle
        final_call = mock_controller.set_servo_angle.call_args_list[-1]
        assert final_call[0][1] == 120.0

    @pytest.mark.asyncio
    async def test_smooth_move_angle_validation(self):
        """Test invalid target angle handling."""
        mock_controller = Mock()
        mock_controller.get_servo_angle.return_value = 90.0

        with pytest.raises(HardwareException):
            await _smooth_move_implementation(mock_controller, "pan", 200.0, 1.0)


class TestPCA9685ServoController:
    """Test PCA9685 servo controller (simplified tests)."""
    
    def test_init_without_hardware(self):
        """Test initialization when Adafruit libs unavailable."""
        with patch('raspibot.hardware.servos.servo.ADAFRUIT_AVAILABLE', False):
            with pytest.raises(HardwareException, match="Adafruit libraries not available"):
                PCA9685ServoController()


class TestGPIOServoController:
    """Test GPIO servo controller."""

    def test_init_without_gpio(self):
        """Test initialization when RPi.GPIO unavailable (logs warning but doesn't fail)."""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'RPi.GPIO'")):
            controller = GPIOServoController()
            assert controller.servo_pins == {"pan": 17, "tilt": 18}  # Default pins
            assert controller.current_angles == {}  # No angles set when GPIO unavailable
            assert controller.calibration_offsets == {}
            assert controller.gpio_available is False

    def test_init_with_gpio_mock(self, mock_gpio):
        """Test successful initialization with mocked GPIO."""
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'RPi.GPIO':
                    return mock_gpio['gpio']
                return __import__(name, *args, **kwargs)
            mock_import.side_effect = import_side_effect

            controller = GPIOServoController()

            assert controller.servo_pins == {"pan": 17, "tilt": 18}
            assert controller.gpio_available is True

    def test_init_custom_pins(self):
        """Test initialization with custom pin mapping."""
        custom_pins = {"pan": 12, "tilt": 13}
        controller = GPIOServoController(servo_pins=custom_pins)

        assert controller.servo_pins == custom_pins

    def test_set_servo_angle_valid(self, mock_gpio):
        """Test setting valid angles."""
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'RPi.GPIO':
                    return mock_gpio['gpio']
                return __import__(name, *args, **kwargs)
            mock_import.side_effect = import_side_effect

            controller = GPIOServoController()
            controller.set_servo_angle("pan", 90)

            # 90° is in the jitter zone and gets adjusted to 86°
            assert controller.current_angles["pan"] == 86

    def test_set_servo_angle_invalid(self):
        """Test invalid angle handling."""
        controller = GPIOServoController()

        with pytest.raises(HardwareException, match="Invalid angle"):
            controller.set_servo_angle("pan", -10)

    def test_set_servo_angle_unknown_servo(self):
        """Test unknown servo name raises error."""
        controller = GPIOServoController()

        with pytest.raises(HardwareException, match="Unknown servo 'invalid'"):
            controller.set_servo_angle("invalid", 90)

    def test_get_servo_angle(self, mock_gpio):
        """Test angle retrieval."""
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'RPi.GPIO':
                    return mock_gpio['gpio']
                return __import__(name, *args, **kwargs)
            mock_import.side_effect = import_side_effect

            controller = GPIOServoController()
            controller.current_angles["pan"] = 45

            assert controller.get_servo_angle("pan") == 45

            # Test default angle for servo that wasn't explicitly set
            assert controller.get_servo_angle("tilt") == 90  # Default from initialization

    def test_set_calibration_offset(self):
        """Test calibration offset setting."""
        controller = GPIOServoController()

        controller.set_calibration_offset("pan", 5.0)
        assert controller.calibration_offsets["pan"] == 5.0

        controller.set_calibration_offset("tilt", -2.5)
        assert controller.calibration_offsets["tilt"] == -2.5

    def test_controller_info_methods(self):
        """Test controller info methods."""
        controller = GPIOServoController()

        assert controller.get_controller_type() == "GPIO"
        assert controller.get_available_servos() == ["pan", "tilt"]

    def test_shutdown_cleanup(self):
        """Test proper shutdown."""
        controller = GPIOServoController()
        controller.shutdown()

        # Should not throw exception

    @pytest.mark.asyncio
    async def test_smooth_move_to_angle_async(self):
        """Test async smooth movement."""
        controller = GPIOServoController()
        controller.current_angles["pan"] = 90

        with patch('raspibot.hardware.servos.servo._smooth_move_implementation', new_callable=AsyncMock) as mock_smooth:
            await controller.smooth_move_to_angle("pan", 120, 1.0)

            mock_smooth.assert_called_once_with(controller, "pan", 120, 1.0)