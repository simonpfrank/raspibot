"""Integration tests for vision module with real hardware.

These tests use the actual Pi AI camera to verify end-to-end functionality.
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock

from raspibot.vision.camera_selector import get_camera, CameraType, is_pi_ai_available
from raspibot.vision import SimpleFaceTracker, FaceTracker, FaceDetector
from raspibot.vision.detection_models import PersonDetection


class TestVisionIntegration:
    """Integration tests for vision module with real hardware."""

    def test_pi_ai_camera_availability(self):
        """Test that Pi AI camera is actually available on this system."""
        available = is_pi_ai_available()
        print(f"Pi AI camera available: {available}")
        
        # This should be True since user has Pi AI camera connected
        assert available is True, "Pi AI camera should be available on this system"

    def test_camera_selector_with_pi_ai(self):
        """Test camera selector creates Pi AI camera successfully."""
        camera = get_camera(CameraType.PI_AI)
        
        assert camera is not None
        assert hasattr(camera, 'start')
        assert hasattr(camera, 'get_frame')
        assert hasattr(camera, 'stop')
        
        print(f"✓ Successfully created camera: {type(camera).__name__}")

    def test_camera_auto_selection(self):
        """Test auto camera selection prefers Pi AI camera."""
        camera = get_camera(CameraType.AUTO)
        
        assert camera is not None
        # Should select Pi AI camera since it's available
        assert "PiAICamera" in type(camera).__name__
        
        print(f"✓ Auto selection chose: {type(camera).__name__}")

    def test_camera_lifecycle(self):
        """Test complete camera lifecycle with real hardware."""
        camera = get_camera(CameraType.PI_AI)
        
        # Start camera
        success = camera.start()
        assert success is True, "Camera should start successfully"
        print("✓ Camera started successfully")
        
        # Get a frame
        frame = camera.get_frame()
        assert frame is not None, "Should get a valid frame"
        assert isinstance(frame, np.ndarray), "Frame should be numpy array"
        # Pi AI camera returns RGBA (4 channels), webcam returns BGR (3 channels)
        assert frame.shape[2] in [3, 4], f"Frame should have 3 or 4 color channels, got {frame.shape[2]}"
        
        print(f"✓ Got frame with shape: {frame.shape} ({frame.shape[2]} channels)")
        
        # Check resolution
        width, height = camera.get_resolution()
        assert width > 0 and height > 0, "Resolution should be positive"
        print(f"✓ Camera resolution: {width}x{height}")
        
        # Check FPS
        fps = camera.get_fps()
        assert fps >= 0, "FPS should be non-negative"
        print(f"✓ Camera FPS: {fps:.1f}")
        
        # Stop camera
        camera.stop()
        print("✓ Camera stopped successfully")

    def test_face_detection_with_real_camera(self):
        """Test face detection with real camera frames."""
        camera = get_camera(CameraType.PI_AI)
        detector = FaceDetector()
        
        camera.start()
        
        # Get multiple frames to test detection
        for i in range(5):
            frame = camera.get_frame()
            if frame is not None:
                faces = detector.detect_faces(frame)
                print(f"Frame {i+1}: Detected {len(faces)} faces")
                
                if len(faces) > 0:
                    print(f"  Face locations: {faces[:3]}...")  # Show first 3 faces
                
                # Small delay between frames
                time.sleep(0.1)
        
        camera.stop()
        print("✓ Face detection test completed")

    def test_simple_face_tracker_integration(self):
        """Test SimpleFaceTracker with real camera (mocked pan/tilt)."""
        # Mock pan/tilt system for integration test
        mock_pan_tilt = Mock()
        mock_pan_tilt.get_current_coordinates.return_value = (0.0, 0.0)
        mock_pan_tilt.move_to_coordinates = Mock()
        
        camera = get_camera(CameraType.PI_AI)
        tracker = SimpleFaceTracker(mock_pan_tilt, 1280, 480)
        
        camera.start()
        
        # Test tracking for a few frames
        for i in range(3):
            frame = camera.get_frame()
            if frame is not None:
                stable_face, all_faces = tracker.track_face(frame)
                
                print(f"Frame {i+1}: {len(all_faces)} total faces, "
                      f"{'stable' if stable_face else 'no stable'} face")
                
                if stable_face:
                    print(f"  Tracking face at: {stable_face}")
                    # Should have called pan/tilt movement
                    assert mock_pan_tilt.move_to_coordinates.called
                
                time.sleep(0.2)
        
        camera.stop()
        print("✓ Simple face tracker integration test completed")

    def test_camera_performance_metrics(self):
        """Test camera performance with real hardware."""
        camera = get_camera(CameraType.PI_AI)
        
        camera.start()
        
        # Measure frame capture performance
        start_time = time.time()
        frame_count = 0
        
        for i in range(10):
            frame = camera.get_frame()
            if frame is not None:
                frame_count += 1
            time.sleep(0.1)
        
        elapsed_time = time.time() - start_time
        actual_fps = frame_count / elapsed_time
        
        print(f"Performance metrics:")
        print(f"  Frames captured: {frame_count}")
        print(f"  Time elapsed: {elapsed_time:.2f}s")
        print(f"  Actual FPS: {actual_fps:.1f}")
        print(f"  Reported FPS: {camera.get_fps():.1f}")
        
        # Basic performance assertions
        assert frame_count > 0, "Should capture at least one frame"
        assert actual_fps > 0, "Should have positive FPS"
        assert elapsed_time > 0, "Should have elapsed time"
        
        camera.stop()
        print("✓ Performance test completed")

    def test_camera_error_handling(self):
        """Test camera error handling with real hardware."""
        camera = get_camera(CameraType.PI_AI)
        
        # Test stopping without starting
        camera.stop()  # Should not crash
        
        # Test getting frame without starting
        frame = camera.get_frame()
        assert frame is None, "Should return None when not started"
        
        # Test availability check
        available = camera.is_available()
        assert isinstance(available, bool), "Availability should be boolean"
        
        print("✓ Error handling test completed")

    @pytest.mark.slow
    def test_extended_camera_operation(self):
        """Test extended camera operation (longer duration)."""
        camera = get_camera(CameraType.PI_AI)
        
        camera.start()
        
        # Run for 5 seconds to test stability
        start_time = time.time()
        frame_count = 0
        error_count = 0
        
        while time.time() - start_time < 5.0:
            try:
                frame = camera.get_frame()
                if frame is not None:
                    frame_count += 1
                time.sleep(0.1)
            except Exception as e:
                error_count += 1
                print(f"Error during extended test: {e}")
        
        elapsed_time = time.time() - start_time
        
        print(f"Extended operation results:")
        print(f"  Duration: {elapsed_time:.1f}s")
        print(f"  Frames captured: {frame_count}")
        print(f"  Errors: {error_count}")
        print(f"  Average FPS: {frame_count / elapsed_time:.1f}")
        
        # Should have captured many frames with few errors
        assert frame_count > 10, "Should capture many frames during extended test"
        assert error_count < 5, "Should have few errors during extended test"
        
        camera.stop()
        print("✓ Extended operation test completed")


class TestVisionModuleCompatibility:
    """Test compatibility between different vision components."""

    def test_camera_selector_compatibility(self):
        """Test that camera selector works with all camera types."""
        # Test Pi AI camera
        pi_camera = get_camera(CameraType.PI_AI)
        assert pi_camera is not None
        
        # Test webcam (should work even if hardware not available)
        try:
            webcam = get_camera(CameraType.WEBCAM)
            assert webcam is not None
            print("✓ Webcam camera created successfully")
        except Exception as e:
            print(f"⚠ Webcam not available: {e}")
        
        # Test auto selection
        auto_camera = get_camera(CameraType.AUTO)
        assert auto_camera is not None
        
        print("✓ Camera selector compatibility test completed")

    def test_face_detector_compatibility(self):
        """Test face detector works with different camera types."""
        detector = FaceDetector()
        
        # Test with Pi AI camera
        camera = get_camera(CameraType.PI_AI)
        camera.start()
        
        frame = camera.get_frame()
        if frame is not None:
            faces = detector.detect_faces(frame)
            print(f"Pi AI camera: Detected {len(faces)} faces")
        
        camera.stop()
        print("✓ Face detector compatibility test completed")


if __name__ == "__main__":
    # Run basic integration test
    print("Running vision integration tests...")
    
    test_instance = TestVisionIntegration()
    
    # Test Pi AI camera availability
    test_instance.test_pi_ai_camera_availability()
    
    # Test camera creation
    test_instance.test_camera_selector_with_pi_ai()
    
    # Test basic camera operation
    test_instance.test_camera_lifecycle()
    
    print("Integration tests completed successfully!") 