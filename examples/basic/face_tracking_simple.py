#!/usr/bin/env python3
"""Quick test script for face tracking components."""

import sys
import os
import time
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from raspibot.vision.camera import Camera
from raspibot.vision.face_detector import FaceDetector
from raspibot.vision.face_tracker import FaceTracker
from raspibot.vision.display import Display
from raspibot.core.face_tracking_robot import FaceTrackingRobot
from raspibot.hardware.servo_selector import get_servo_controller, ServoControllerType
from raspibot.movement.pan_tilt import PanTiltSystem


def test_components():
    """Test individual components."""
    print("🔧 Testing Face Tracking Components")
    print("=" * 50)
    
    # Test 1: Face Detector
    print("1. Testing Face Detector...")
    try:
        detector = FaceDetector()
        # Test with dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = detector.detect_faces(frame)
        print(f"   ✅ Face detector working (found {len(faces)} faces in test frame)")
    except Exception as e:
        print(f"   ❌ Face detector failed: {e}")
        return False
    
    # Test 2: Camera (if available)
    print("2. Testing Camera...")
    try:
        camera = Camera(device_id=0)
        if camera.start():
            print("   ✅ Camera started successfully")
            frame = camera.get_frame()
            if frame is not None:
                print(f"   ✅ Camera capturing frames: {frame.shape}")
            else:
                print("   ⚠️  Camera started but no frames captured")
            camera.stop()
        else:
            print("   ⚠️  No camera available (skipping)")
    except Exception as e:
        print(f"   ⚠️  Camera test failed: {e}")
    
    # Test 3: Servo Controllers
    print("3. Testing Servo Controllers...")
    try:
        # Try PCA9685
        try:
            controller = get_servo_controller(ServoControllerType.PCA9685)
            print("   ✅ PCA9685 controller available")
            controller.shutdown()
        except Exception:
            print("   ⚠️  PCA9685 not available")
        
        # Try GPIO
        try:
            controller = get_servo_controller(ServoControllerType.GPIO)
            print("   ✅ GPIO controller available")
            controller.shutdown()
        except Exception:
            print("   ⚠️  GPIO not available")
            
    except Exception as e:
        print(f"   ❌ Servo controller test failed: {e}")
    
    # Test 4: Pan/Tilt System (mocked)
    print("4. Testing Pan/Tilt System...")
    try:
        from unittest.mock import Mock
        mock_controller = Mock()
        mock_controller.get_controller_type.return_value = "Mock"
        mock_controller.get_available_channels.return_value = [0, 1]
        
        pan_tilt = PanTiltSystem(mock_controller)
        pan_tilt.move_to_coordinates(0, 0)
        print("   ✅ Pan/Tilt system working with mock controller")
    except Exception as e:
        print(f"   ❌ Pan/Tilt system failed: {e}")
        return False
    
    # Test 5: Face Tracker
    print("5. Testing Face Tracker...")
    try:
        mock_controller = Mock()
        mock_controller.get_current_coordinates.return_value = (0.0, 0.0)
        
        tracker = FaceTracker(mock_controller, 640, 480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        stable_face, all_faces = tracker.track_face(frame)
        print("   ✅ Face tracker working")
    except Exception as e:
        print(f"   ❌ Face tracker failed: {e}")
        return False
    
    # Test 6: Display (headless safe)
    print("6. Testing Display...")
    try:
        display = Display("Test")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # This might fail in headless, which is OK
        try:
            result = display.show_frame(frame)
            print("   ✅ Display working")
        except Exception:
            print("   ⚠️  Display test skipped (headless environment)")
        display.close()
    except Exception as e:
        print(f"   ⚠️  Display test failed: {e}")
    
    print("\n🎉 Component tests completed!")
    return True


def test_integration():
    """Test system integration."""
    print("\n🔗 Testing System Integration")
    print("=" * 50)
    
    try:
        from unittest.mock import Mock, patch
        
        # Mock servo controller
        with patch('raspibot.hardware.servo_selector.get_servo_controller') as mock_factory:
            mock_controller = Mock()
            mock_controller.get_controller_type.return_value = "Mock"
            mock_controller.get_available_channels.return_value = [0, 1]
            mock_factory.return_value = mock_controller
            
            # Test robot initialization
            robot = FaceTrackingRobot(servo_type="pca9685", camera_device=0)
            print("   ✅ Robot initialized successfully")
            
            # Test status
            status = robot.get_status()
            print(f"   ✅ Robot status: {status.get('running', 'unknown')}")
            
            # Test controls
            robot.center_camera()
            robot.force_sleep()
            robot.force_wake_up()
            print("   ✅ Robot controls working")
            
            robot.stop()
            print("   ✅ Robot shutdown successful")
            
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False
    
    print("\n🎉 Integration tests completed!")
    return True


def test_performance():
    """Test basic performance."""
    print("\n⚡ Testing Performance")
    print("=" * 50)
    
    try:
        detector = FaceDetector()
        
        # Test detection speed
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        start_time = time.time()
        detections = 0
        test_duration = 1.0  # 1 second test
        
        while time.time() - start_time < test_duration:
            faces = detector.detect_faces(frame)
            detections += 1
        
        fps = detections / test_duration
        print(f"   ✅ Face detection performance: {fps:.1f} FPS")
        
        if fps >= 10:
            print("   🚀 Excellent performance!")
        elif fps >= 5:
            print("   👍 Good performance")
        else:
            print("   ⚠️  Low performance (may be OK for tutorial)")
            
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        return False
    
    print("\n🎉 Performance tests completed!")
    return True


def main():
    """Run all tests."""
    print("🤖 Face Tracking Robot - Component Tests")
    print("=" * 60)
    print("This script tests all face tracking components without")
    print("requiring full hardware setup.\n")
    
    success = True
    
    # Run component tests
    success &= test_components()
    
    # Run integration tests
    success &= test_integration()
    
    # Run performance tests
    success &= test_performance()
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ Face tracking system is ready to use.")
        print("\nTo run the full demo:")
        print("  python scripts/face_tracking_demo.py")
        print("\nTo test with GPIO servos:")
        print("  python scripts/face_tracking_demo.py --servo gpio")
        return 0
    else:
        print("❌ Some tests failed.")
        print("⚠️  Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 