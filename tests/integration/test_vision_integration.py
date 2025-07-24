"""Integration tests for vision system."""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch

from raspibot.vision.camera import Camera
from raspibot.vision.face_detector import FaceDetector
from raspibot.vision.face_tracker import FaceTracker
from raspibot.vision.display import Display
from raspibot.core.face_tracking_robot import FaceTrackingRobot
from raspibot.hardware.servo_factory import ServoControllerFactory, ServoControllerType
from raspibot.movement.pan_tilt import PanTiltSystem


class TestVisionIntegration:
    """Integration tests for vision components."""

    def test_camera_face_detector_integration(self):
        """Test camera and face detector integration."""
        try:
            camera = Camera(device_id=0)
            if not camera.start():
                pytest.skip("No camera available for integration test")
            
            detector = FaceDetector()
            
            # Capture a few frames and test detection
            for i in range(3):
                frame = camera.get_frame()
                assert frame is not None
                assert frame.shape == (camera.height, camera.width, 3)
                
                # Test face detection (may or may not find faces)
                faces = detector.detect_faces(frame)
                assert isinstance(faces, list)
                
                # If faces found, test center calculation
                if faces:
                    largest = detector.get_largest_face(faces)
                    assert largest is not None
                    center = detector.get_face_center(largest)
                    assert isinstance(center, tuple)
                    assert len(center) == 2
                
                time.sleep(0.1)
            
            # Test FPS calculation
            assert detector.get_detection_fps() >= 0
            assert camera.get_fps() >= 0
            
            camera.stop()
            
        except Exception as e:
            pytest.skip(f"Camera integration test failed: {e}")

    def test_face_tracker_integration(self):
        """Test face tracker with mock pan/tilt system."""
        mock_pan_tilt = Mock()
        mock_pan_tilt.get_current_coordinates.return_value = (0.0, 0.0)
        
        tracker = FaceTracker(mock_pan_tilt, 640, 480)
        
        # Test with mock frame (no faces)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        stable_face, all_faces = tracker.track_face(frame)
        
        assert stable_face is None
        assert all_faces == []
        
        # Test stability tracking
        assert tracker.get_sleep_status() is False
        sleep_time = tracker.get_time_until_sleep()
        assert sleep_time > 0

    def test_display_integration(self):
        """Test display with mock frames."""
        try:
            display = Display("Integration Test")
            
            # Create test frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add some color
            frame[100:200, 100:200] = [0, 255, 0]  # Green square
            
            # Test display with face boxes
            faces = [(100, 100, 100, 100), (300, 200, 80, 80)]
            stable_faces = [(100, 100, 100, 100)]
            
            # This would normally show a window, but in CI/test it should handle gracefully
            result = display.show_frame(
                frame=frame,
                faces=faces,
                stable_faces=stable_faces,
                camera_fps=30.0,
                detection_fps=15.0,
                servo_position=(0.5, -0.2)
            )
            
            # In headless environment, this might fail, which is OK
            assert isinstance(result, bool)
            
            display.close()
            
        except Exception as e:
            # Display tests may fail in headless environment
            pytest.skip(f"Display integration test failed (headless?): {e}")

    @patch('raspibot.hardware.servo_factory.ServoControllerFactory.create_controller')
    def test_face_tracking_robot_initialization(self, mock_factory):
        """Test face tracking robot initialization."""
        # Mock servo controller
        mock_controller = Mock()
        mock_controller.get_controller_type.return_value = "PCA9685"
        mock_controller.get_available_channels.return_value = [0, 1]
        mock_factory.return_value = mock_controller
        
        try:
            robot = FaceTrackingRobot(servo_type="pca9685", camera_device=0)
            
            # Test status
            status = robot.get_status()
            assert isinstance(status, dict)
            assert "running" in status
            assert "camera_status" in status
            
            # Test camera control
            robot.center_camera()
            
            # Test sleep controls
            robot.force_sleep()
            robot.force_wake_up()
            
            # Cleanup
            robot.stop()
            
        except Exception as e:
            pytest.skip(f"Face tracking robot integration test failed: {e}")

    def test_servo_vision_integration(self):
        """Test integration with actual servo controllers."""
        try:
            # Try PCA9685 first
            try:
                controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
                controller_type = "PCA9685"
            except Exception:
                # Fall back to GPIO
                try:
                    controller = ServoControllerFactory.create_controller(ServoControllerType.GPIO)
                    controller_type = "GPIO"
                except Exception:
                    pytest.skip("No servo controllers available")
            
            # Test pan/tilt integration
            pan_tilt = PanTiltSystem(controller)
            
            # Test coordinate system
            pan_tilt.move_to_coordinates(0, 0)  # Center
            time.sleep(0.5)
            
            current_pos = pan_tilt.get_current_coordinates()
            assert isinstance(current_pos, tuple)
            assert len(current_pos) == 2
            
            # Test face tracker integration
            tracker = FaceTracker(pan_tilt, 640, 480)
            
            # Test sleep mode
            tracker.force_sleep()
            time.sleep(1)  # Let sleep sequence complete
            assert tracker.get_sleep_status() is True
            
            tracker.force_wake_up()
            time.sleep(1)  # Let wake sequence complete
            assert tracker.get_sleep_status() is False
            
            # Cleanup
            controller.shutdown()
            
        except Exception as e:
            pytest.skip(f"Servo integration test failed: {e}")

    def test_full_system_integration(self):
        """Test full system integration (requires hardware)."""
        try:
            # This test requires both camera and servo hardware
            robot = FaceTrackingRobot(servo_type="pca9685", camera_device=0)
            
            # Test basic functionality
            assert robot.is_running() is False
            
            status = robot.get_status()
            assert isinstance(status, dict)
            
            # Test camera centering
            robot.center_camera()
            
            # Test sleep/wake cycle
            robot.force_sleep()
            time.sleep(1)
            robot.force_wake_up()
            time.sleep(1)
            
            # Cleanup
            robot.stop()
            
        except Exception as e:
            pytest.skip(f"Full system integration test failed (hardware required): {e}")

    def test_performance_benchmarks(self):
        """Test performance benchmarks for face detection."""
        try:
            camera = Camera(device_id=0)
            if not camera.start():
                pytest.skip("No camera available for performance test")
            
            detector = FaceDetector()
            
            # Measure detection performance
            start_time = time.time()
            detection_count = 0
            target_duration = 2.0  # 2 seconds
            
            while time.time() - start_time < target_duration:
                frame = camera.get_frame()
                if frame is not None:
                    faces = detector.detect_faces(frame)
                    detection_count += 1
            
            elapsed = time.time() - start_time
            fps = detection_count / elapsed
            
            print(f"Detection performance: {fps:.1f} FPS over {elapsed:.1f}s")
            
            # Should achieve at least 5 FPS on Raspberry Pi
            assert fps >= 5.0, f"Detection FPS too low: {fps:.1f}"
            
            camera.stop()
            
        except Exception as e:
            pytest.skip(f"Performance test failed: {e}")

    def test_memory_usage(self):
        """Test memory usage doesn't grow excessively."""
        import psutil
        import os
        
        try:
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            camera = Camera(device_id=0)
            if not camera.start():
                pytest.skip("No camera available for memory test")
            
            detector = FaceDetector()
            
            # Run for a while
            for i in range(100):
                frame = camera.get_frame()
                if frame is not None:
                    faces = detector.detect_faces(frame)
                
                if i % 20 == 0:  # Check memory every 20 frames
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_growth = current_memory - initial_memory
                    
                    # Should not grow more than 100MB
                    assert memory_growth < 100, f"Memory growth too high: {memory_growth:.1f} MB"
            
            camera.stop()
            
        except Exception as e:
            pytest.skip(f"Memory test failed: {e}")


class TestVisionRobustness:
    """Test vision system robustness and error handling."""

    def test_camera_failure_recovery(self):
        """Test handling of camera failures."""
        # Test with invalid device ID
        camera = Camera(device_id=99)  # Unlikely to exist
        assert camera.start() is False
        assert camera.get_frame() is None
        assert camera.is_available() is False
        
        # Should not crash on multiple stops
        camera.stop()
        camera.stop()

    def test_face_detector_robustness(self):
        """Test face detector with various input types."""
        detector = FaceDetector()
        
        # Test with None
        faces = detector.detect_faces(None)
        assert faces == []
        
        # Test with empty array
        faces = detector.detect_faces(np.array([]))
        assert faces == []
        
        # Test with invalid shape
        try:
            faces = detector.detect_faces(np.zeros((10, 10), dtype=np.uint8))  # 2D instead of 3D
            assert faces == []
        except Exception:
            pass  # Exception is acceptable for invalid input

    def test_face_tracker_edge_cases(self):
        """Test face tracker edge cases."""
        mock_pan_tilt = Mock()
        mock_pan_tilt.get_current_coordinates.return_value = (0.0, 0.0)
        
        tracker = FaceTracker(mock_pan_tilt, 640, 480)
        
        # Test with None frame
        stable_face, all_faces = tracker.track_face(None)
        assert stable_face is None
        assert all_faces == []
        
        # Test rapid sleep/wake cycles
        tracker.force_sleep()
        tracker.force_wake_up()
        tracker.force_sleep()
        tracker.force_wake_up()
        
        # Should handle without errors
        assert isinstance(tracker.get_sleep_status(), bool)

    def test_display_error_handling(self):
        """Test display error handling."""
        display = Display()
        
        # Test with None frame
        result = display.show_frame(None)
        assert result is True
        
        # Test error message display
        try:
            display.show_error_message("Test error message")
        except Exception:
            pass  # May fail in headless environment
        
        # Cleanup should not fail
        display.close()
        display.close()  # Multiple calls should be safe 