"""Tests for hardware interface classes.

This module tests the simple hardware interface classes that use
NotImplementedError for interface enforcement.
"""

import pytest

# Import the interfaces module (will be created after tests)
# from raspibot.hardware import interfaces


class TestServoController:
    """Test the ServoController interface class."""

    def test_servo_controller_raises_not_implemented(self):
        """Test that ServoController methods raise NotImplementedError."""
        from raspibot.hardware.servos.servo_interface import ServoController
        
        controller = ServoController()
        
        with pytest.raises(NotImplementedError):
            controller.set_angle(0, 90)
        
        with pytest.raises(NotImplementedError):
            controller.get_angle(0)
        
        with pytest.raises(NotImplementedError):
            controller.initialize()
        
        with pytest.raises(NotImplementedError):
            controller.shutdown()

    def test_servo_controller_subclass_works(self):
        """Test that a subclass can override the methods."""
        from raspibot.hardware.servos.servo_interface import ServoController
        
        class MockServoController(ServoController):
            def set_angle(self, channel: int, angle: float) -> None:
                self.last_channel = channel
                self.last_angle = angle
            
            def get_angle(self, channel: int) -> float:
                return 90.0
            
            def initialize(self) -> None:
                self.initialized = True
            
            def shutdown(self) -> None:
                self.shutdown_called = True
        
        controller = MockServoController()
        controller.initialize()
        assert controller.initialized is True
        
        controller.set_angle(1, 45.0)
        assert controller.last_channel == 1
        assert controller.last_angle == 45.0
        
        angle = controller.get_angle(1)
        assert angle == 90.0
        
        controller.shutdown()
        assert controller.shutdown_called is True

    def test_servo_controller_documentation(self):
        """Test that ServoController has proper documentation."""
        from raspibot.hardware.servos.servo_interface import ServoController
        
        assert ServoController.__doc__ is not None
        assert "Hardware interface for servo control" in ServoController.__doc__
        
        # Check method documentation
        assert ServoController.set_angle.__doc__ is not None
        assert ServoController.get_angle.__doc__ is not None
        assert ServoController.initialize.__doc__ is not None
        assert ServoController.shutdown.__doc__ is not None


class TestCameraTemplate:
    """Test the Camera interface class."""

    def test_camera_raises_not_implemented(self):
        """Test that Camera methods raise NotImplementedError."""
        from raspibot.hardware.servos.servo_interface import Camera
        
        camera = Camera()
        
        with pytest.raises(NotImplementedError):
            camera.capture_frame()
        
        with pytest.raises(NotImplementedError):
            camera.start_stream()
        
        with pytest.raises(NotImplementedError):
            camera.stop_stream()
        
        with pytest.raises(NotImplementedError):
            camera.set_resolution(640, 480)

    def test_camera_subclass_works(self):
        """Test that a subclass can override the methods."""
        from raspibot.hardware.servos.servo_interface import Camera
        
        class MockCamera(Camera):
            def capture_frame(self):
                return "mock_frame_data"
            
            def start_stream(self) -> None:
                self.streaming = True
            
            def stop_stream(self) -> None:
                self.streaming = False
            
            def set_resolution(self, width: int, height: int) -> None:
                self.width = width
                self.height = height
        
        camera = MockCamera()
        camera.start_stream()
        assert camera.streaming is True
        
        frame = camera.capture_frame()
        assert frame == "mock_frame_data"
        
        camera.set_resolution(1280, 720)
        assert camera.width == 1280
        assert camera.height == 720
        
        camera.stop_stream()
        assert camera.streaming is False 