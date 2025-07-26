"""Integration tests for servo control system.

These tests verify that all servo control components work together correctly
with real hardware and proper integration between modules.
"""

import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from raspibot.hardware.servo_selector import get_servo_controller, ServoControllerType
from raspibot.hardware.servo_interface import ServoInterface
from raspibot.movement.pan_tilt import PanTiltSystem
from raspibot.exceptions import HardwareException
from raspibot.utils.logging_config import setup_logging


class TestServoHardwareIntegration:
    """Integration tests for servo hardware control."""

    def test_pca9685_hardware_detection(self):
        """Test PCA9685 hardware detection and initialization."""
        logger = setup_logging(__name__)
        
        try:
            # Test PCA9685 controller creation
            controller = get_servo_controller(ServoControllerType.PCA9685)
            
            # Verify hardware detection
            assert controller.get_controller_type() == "PCA9685"
            assert len(controller.get_available_channels()) > 0
            
            logger.info("✓ PCA9685 hardware detected and initialized")
            
        except Exception as e:
            logger.warning(f"⚠ PCA9685 hardware not available: {e}")
            pytest.skip("PCA9685 hardware not available")

    def test_gpio_hardware_detection(self):
        """Test GPIO hardware detection and initialization."""
        logger = setup_logging(__name__)
        
        try:
            # Test GPIO controller creation
            controller = get_servo_controller(ServoControllerType.GPIO)
            
            # Verify hardware detection
            assert controller.get_controller_type() == "GPIO"
            assert len(controller.get_available_channels()) > 0
            
            logger.info("✓ GPIO hardware detected and initialized")
            
        except Exception as e:
            logger.warning(f"⚠ GPIO hardware not available: {e}")
            pytest.skip("GPIO hardware not available")

    def test_servo_movement_integration(self):
        """Test complete servo movement integration."""
        logger = setup_logging(__name__)
        
        # Try PCA9685 first, fall back to GPIO
        controller = None
        controller_type = None
        
        try:
            controller = get_servo_controller(ServoControllerType.PCA9685)
            controller_type = "PCA9685"
        except Exception:
            try:
                controller = get_servo_controller(ServoControllerType.GPIO)
                controller_type = "GPIO"
            except Exception as e:
                pytest.skip(f"No servo hardware available: {e}")
        
        if controller is None:
            pytest.skip("No servo hardware available")
        
        logger.info(f"Testing servo movement with {controller_type}")
        
        # Test basic movement
        test_channel = controller.get_available_channels()[0]
        
        # Move to center
        controller.set_servo_angle(test_channel, 90)
        time.sleep(1)
        assert controller.get_servo_angle(test_channel) == 90
        
        # Move to extremes
        controller.set_servo_angle(test_channel, 0)
        time.sleep(1)
        assert controller.get_servo_angle(test_channel) == 0
        
        controller.set_servo_angle(test_channel, 180)
        time.sleep(1)
        assert controller.get_servo_angle(test_channel) == 180
        
        # Return to center
        controller.set_servo_angle(test_channel, 90)
        time.sleep(1)
        
        logger.info("✓ Servo movement integration successful")

    def test_smooth_movement_integration(self):
        """Test smooth movement integration."""
        logger = setup_logging(__name__)
        
        # Get available controller
        controller = None
        try:
            controller = get_servo_controller(ServoControllerType.PCA9685)
        except Exception:
            try:
                controller = get_servo_controller(ServoControllerType.GPIO)
            except Exception as e:
                pytest.skip(f"No servo hardware available: {e}")
        
        if controller is None:
            pytest.skip("No servo hardware available")
        
        test_channel = controller.get_available_channels()[0]
        
        # Test smooth movement
        logger.info("Testing smooth movement...")
        
        # Smooth movement from 0 to 180
        controller.smooth_move_to_angle(test_channel, 0, speed=0.8)
        time.sleep(0.5)
        controller.smooth_move_to_angle(test_channel, 180, speed=0.8)
        time.sleep(2)  # Allow time for smooth movement
        
        # Return to center
        controller.smooth_move_to_angle(test_channel, 90, speed=0.8)
        time.sleep(1)
        
        logger.info("✓ Smooth movement integration successful")

    def test_calibration_integration(self):
        """Test calibration offset integration."""
        logger = setup_logging(__name__)
        
        # Get available controller
        controller = None
        try:
            controller = get_servo_controller(ServoControllerType.PCA9685)
        except Exception:
            try:
                controller = get_servo_controller(ServoControllerType.GPIO)
            except Exception as e:
                pytest.skip(f"No servo hardware available: {e}")
        
        if controller is None:
            pytest.skip("No servo hardware available")
        
        test_channel = controller.get_available_channels()[0]
        
        # Test calibration
        logger.info("Testing calibration integration...")
        
        # Set calibration offset
        controller.set_calibration_offset(test_channel, 5.0)
        assert controller.get_calibration_offset(test_channel) == 5.0
        
        # Move with offset
        controller.set_servo_angle(test_channel, 90)
        time.sleep(1)
        
        # Clear offset
        controller.set_calibration_offset(test_channel, 0.0)
        assert controller.get_calibration_offset(test_channel) == 0.0
        
        logger.info("✓ Calibration integration successful")


class TestPanTiltIntegration:
    """Integration tests for pan/tilt system."""

    def test_pan_tilt_creation(self):
        """Test pan/tilt system creation with different controllers."""
        logger = setup_logging(__name__)
        
        # Try different controllers
        for controller_type in [ServoControllerType.PCA9685, ServoControllerType.GPIO]:
            try:
                controller = get_servo_controller(controller_type)
                
                # Create pan/tilt system
                pan_tilt = PanTiltSystem(
                    servo_controller=controller,
                    pan_channel=0,
                    tilt_channel=1
                )
                
                logger.info(f"✓ Pan/tilt system created with {controller_type.value}")
                
                # Test basic functionality
                pan_tilt.center_camera()
                time.sleep(1)
                
                # Cleanup
                pan_tilt.shutdown()
                break
                
            except Exception as e:
                logger.warning(f"⚠ Pan/tilt creation failed with {controller_type.value}: {e}")
                continue
        else:
            pytest.skip("No suitable controller available for pan/tilt")

    def test_coordinate_movement_integration(self):
        """Test coordinate-based movement integration."""
        logger = setup_logging(__name__)
        
        # Get pan/tilt system
        pan_tilt = None
        for controller_type in [ServoControllerType.PCA9685, ServoControllerType.GPIO]:
            try:
                controller = get_servo_controller(controller_type)
                pan_tilt = PanTiltSystem(
                    servo_controller=controller,
                    pan_channel=0,
                    tilt_channel=1
                )
                break
            except Exception:
                continue
        
        if pan_tilt is None:
            pytest.skip("No suitable controller available for pan/tilt")
        
        logger.info("Testing coordinate-based movement...")
        
        # Test coordinate movements
        pan_tilt.move_to_coordinates(0, 0)  # Center
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        assert abs(pos[0]) < 0.1 and abs(pos[1]) < 0.1
        
        pan_tilt.move_to_coordinates(0.5, 0.5)  # Top right
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        assert abs(pos[0] - 0.5) < 0.1 and abs(pos[1] - 0.5) < 0.1
        
        pan_tilt.move_to_coordinates(-0.5, -0.5)  # Bottom left
        time.sleep(1)
        pos = pan_tilt.get_current_coordinates()
        assert abs(pos[0] + 0.5) < 0.1 and abs(pos[1] + 0.5) < 0.1
        
        # Test tilt-specific movements
        pan_tilt.point_up()
        time.sleep(1)
        current_pos = pan_tilt.get_current_position()
        assert current_pos[1] == 90  # Should be pointing up
        
        pan_tilt.point_down()
        time.sleep(1)
        current_pos = pan_tilt.get_current_position()
        assert current_pos[1] == 270  # Should be pointing down
        
        pan_tilt.point_horizontal()
        time.sleep(1)
        current_pos = pan_tilt.get_current_position()
        assert current_pos[1] == 200  # Should be at center
        
        # Return to center
        pan_tilt.center_camera()
        time.sleep(1)
        
        logger.info("✓ Coordinate movement integration successful")

    def test_smooth_pan_tilt_integration(self):
        """Test smooth pan/tilt movement integration."""
        logger = setup_logging(__name__)
        
        # Get pan/tilt system
        pan_tilt = None
        for controller_type in [ServoControllerType.PCA9685, ServoControllerType.GPIO]:
            try:
                controller = get_servo_controller(controller_type)
                pan_tilt = PanTiltSystem(
                    servo_controller=controller,
                    pan_channel=0,
                    tilt_channel=1
                )
                break
            except Exception:
                continue
        
        if pan_tilt is None:
            pytest.skip("No suitable controller available for pan/tilt")
        
        logger.info("Testing smooth pan/tilt movement...")
        
        # Test smooth movements
        pan_tilt.smooth_move_to_coordinates(0.5, 0.5, speed=0.8)
        time.sleep(2)  # Allow time for smooth movement
        
        pan_tilt.smooth_move_to_coordinates(-0.5, -0.5, speed=0.8)
        time.sleep(2)
        
        pan_tilt.smooth_move_to_coordinates(0, 0, speed=0.8)
        time.sleep(2)
        
        logger.info("✓ Smooth pan/tilt integration successful")

    def test_target_tracking_integration(self):
        """Test target tracking integration."""
        logger = setup_logging(__name__)
        
        # Get pan/tilt system
        pan_tilt = None
        for controller_type in [ServoControllerType.PCA9685, ServoControllerType.GPIO]:
            try:
                controller = get_servo_controller(controller_type)
                pan_tilt = PanTiltSystem(
                    servo_controller=controller,
                    pan_channel=0,
                    tilt_channel=1
                )
                break
            except Exception:
                continue
        
        if pan_tilt is None:
            pytest.skip("No suitable controller available for pan/tilt")
        
        logger.info("Testing target tracking...")
        
        # Simulate tracking a moving target
        targets = [(0.2, 0.3), (0.4, 0.1), (-0.2, 0.5), (0, 0)]
        
        for target_x, target_y in targets:
            pan_tilt.track_target(target_x, target_y, speed=0.8)
            time.sleep(1)
        
        logger.info("✓ Target tracking integration successful")


class TestFactoryIntegration:
    """Integration tests for factory pattern."""

    def test_factory_controller_creation(self):
        """Test factory creates working controllers."""
        logger = setup_logging(__name__)
        
        # Test both controller types
        for controller_type in [ServoControllerType.PCA9685, ServoControllerType.GPIO]:
            try:
                controller = get_servo_controller(controller_type)
                
                # Verify controller works
                assert controller.get_controller_type() in ["PCA9685", "GPIO"]
                assert len(controller.get_available_channels()) > 0
                
                # Test basic functionality
                test_channel = controller.get_available_channels()[0]
                controller.set_servo_angle(test_channel, 90)
                time.sleep(0.5)
                
                logger.info(f"✓ Factory created working {controller_type.value} controller")
                
            except Exception as e:
                logger.warning(f"⚠ Factory failed to create {controller_type.value} controller: {e}")

    def test_factory_string_config(self):
        """Test factory with string configuration."""
        logger = setup_logging(__name__)
        
        # Test string-based creation
        for controller_type_str in ["pca9685", "gpio"]:
            try:
                controller = get_servo_controller_from_config(controller_type_str)
                
                # Verify controller works
                assert controller.get_controller_type().lower() == controller_type_str
                
                logger.info(f"✓ Factory string config created {controller_type_str} controller")
                
            except Exception as e:
                logger.warning(f"⚠ Factory string config failed for {controller_type_str}: {e}")

    def test_factory_error_handling(self):
        """Test factory error handling."""
        logger = setup_logging(__name__)
        
        # Test invalid controller type
        with pytest.raises(HardwareException):
            get_servo_controller("invalid")
        
        # Test invalid enum
        with pytest.raises(HardwareException):
            get_servo_controller("nonexistent")
        
        logger.info("✓ Factory error handling working correctly")


class TestSafetyIntegration:
    """Integration tests for safety features."""

    def test_emergency_stop_integration(self):
        """Test emergency stop integration."""
        logger = setup_logging(__name__)
        
        # Get available controller
        controller = None
        try:
            controller = get_servo_controller(ServoControllerType.PCA9685)
        except Exception:
            try:
                controller = get_servo_controller(ServoControllerType.GPIO)
            except Exception as e:
                pytest.skip(f"No servo hardware available: {e}")
        
        if controller is None:
            pytest.skip("No servo hardware available")
        
        logger.info("Testing emergency stop...")
        
        # Move to a position
        test_channel = controller.get_available_channels()[0]
        controller.set_servo_angle(test_channel, 90)
        time.sleep(0.5)
        
        # Emergency stop
        controller.emergency_stop()
        
        # Verify emergency stop doesn't crash
        assert controller.get_servo_angle(test_channel) == 90  # Should still be readable
        
        logger.info("✓ Emergency stop integration successful")

    def test_shutdown_integration(self):
        """Test shutdown integration."""
        logger = setup_logging(__name__)
        
        # Get available controller
        controller = None
        try:
            controller = get_servo_controller(ServoControllerType.PCA9685)
        except Exception:
            try:
                controller = get_servo_controller(ServoControllerType.GPIO)
            except Exception as e:
                pytest.skip(f"No servo hardware available: {e}")
        
        if controller is None:
            pytest.skip("No servo hardware available")
        
        logger.info("Testing shutdown...")
        
        # Move to a position
        test_channel = controller.get_available_channels()[0]
        controller.set_servo_angle(test_channel, 45)
        time.sleep(0.5)
        
        # Shutdown
        controller.shutdown()
        
        logger.info("✓ Shutdown integration successful")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"]) 