#!/usr/bin/env python3
"""Headless test script for face tracking components (no display)."""

import sys
import os
import time
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.vision.camera import Camera
from raspibot.vision.face_detector import FaceDetector
from raspibot.vision.face_tracker import FaceTracker
from raspibot.hardware.servo_factory import ServoControllerFactory, ServoControllerType
from raspibot.movement.pan_tilt import PanTiltSystem


def test_components():
    """Test individual components (no display)."""
    print("🔧 Testing Face Tracking Components (Headless)")
    print("=" * 55)
    
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
                
                # Test face detection on real frame
                detector = FaceDetector()
                faces = detector.detect_faces(frame)
                print(f"   ✅ Face detection on real frame: {len(faces)} faces found")
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
            controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
            print("   ✅ PCA9685 controller available")
            print(f"      Type: {controller.get_controller_type()}")
            print(f"      Channels: {controller.get_available_channels()}")
            controller.shutdown()
        except Exception:
            print("   ⚠️  PCA9685 not available")
        
        # Try GPIO
        try:
            controller = ServoControllerFactory.create_controller(ServoControllerType.GPIO)
            print("   ✅ GPIO controller available")
            print(f"      Type: {controller.get_controller_type()}")
            print(f"      Channels: {controller.get_available_channels()}")
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
        pan_tilt.move_to_coordinates(0.5, -0.5)
        pan_tilt.move_to_coordinates(-0.5, 0.5)
        print("   ✅ Pan/Tilt system working with mock controller")
    except Exception as e:
        print(f"   ❌ Pan/Tilt system failed: {e}")
        return False
    
    # Test 5: Face Tracker
    print("5. Testing Face Tracker...")
    try:
        from unittest.mock import Mock
        mock_controller = Mock()
        mock_controller.get_current_coordinates.return_value = (0.0, 0.0)
        
        tracker = FaceTracker(mock_controller, 640, 480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        stable_face, all_faces = tracker.track_face(frame)
        
        # Test sleep functionality
        print(f"      Sleep status: {tracker.get_sleep_status()}")
        print(f"      Time until sleep: {tracker.get_time_until_sleep():.1f}s")
        
        # Test forced sleep/wake
        tracker.force_sleep()
        print(f"      After forced sleep: {tracker.get_sleep_status()}")
        tracker.force_wake_up()
        print(f"      After forced wake: {tracker.get_sleep_status()}")
        
        print("   ✅ Face tracker working")
    except Exception as e:
        print(f"   ❌ Face tracker failed: {e}")
        return False
    
    print("\n🎉 Component tests completed!")
    return True


def test_integration():
    """Test system integration (headless)."""
    print("\n🔗 Testing System Integration (Headless)")
    print("=" * 55)
    
    try:
        from unittest.mock import Mock, patch
        
        # Mock servo controller
        with patch('raspibot.hardware.servo_factory.ServoControllerFactory.create_controller') as mock_factory:
            mock_controller = Mock()
            mock_controller.get_controller_type.return_value = "Mock"
            mock_controller.get_available_channels.return_value = [0, 1]
            mock_factory.return_value = mock_controller
            
            # Test robot initialization (skip camera to avoid display issues)
            print("   Initializing robot with mock components...")
            
            # Create components separately to avoid display
            from raspibot.vision.face_tracker import FaceTracker
            from raspibot.movement.pan_tilt import PanTiltSystem
            
            controller = ServoControllerFactory.create_controller(ServoControllerType.PCA9685)
            pan_tilt = PanTiltSystem(controller)
            tracker = FaceTracker(pan_tilt, 640, 480)
            
            print("   ✅ Core components initialized")
            
            # Test functionality
            pan_tilt.move_to_coordinates(0, 0)
            
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            stable_face, all_faces = tracker.track_face(frame)
            
            print("   ✅ System integration working")
            
            # Cleanup
            controller.shutdown()
            print("   ✅ System shutdown successful")
            
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False
    
    print("\n🎉 Integration tests completed!")
    return True


def test_performance():
    """Test basic performance."""
    print("\n⚡ Testing Performance")
    print("=" * 55)
    
    try:
        detector = FaceDetector()
        
        # Test detection speed
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        print("   Running 2-second performance test...")
        start_time = time.time()
        detections = 0
        test_duration = 2.0  # 2 second test
        
        while time.time() - start_time < test_duration:
            faces = detector.detect_faces(frame)
            detections += 1
        
        fps = detections / test_duration
        print(f"   ✅ Face detection performance: {fps:.1f} FPS")
        
        if fps >= 15:
            print("   🚀 Excellent performance!")
        elif fps >= 10:
            print("   👍 Good performance")
        elif fps >= 5:
            print("   ✅ Acceptable performance")
        else:
            print("   ⚠️  Low performance (may affect real-time tracking)")
            
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        return False
    
    print("\n🎉 Performance tests completed!")
    return True


def main():
    """Run all tests."""
    print("🤖 Face Tracking Robot - Headless Component Tests")
    print("=" * 65)
    print("This script tests all face tracking components without")
    print("requiring display output (safe for headless environments).\n")
    
    success = True
    
    # Run component tests
    success &= test_components()
    
    # Run integration tests
    success &= test_integration()
    
    # Run performance tests
    success &= test_performance()
    
    # Summary
    print("\n" + "=" * 65)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ Face tracking system is ready to use.")
        print("\nSystem capabilities detected:")
        
        # Check what's available
        try:
            camera = Camera(device_id=0)
            if camera.start():
                print("  📹 Camera: Available")
                camera.stop()
            else:
                print("  📹 Camera: Not available")
        except:
            print("  📹 Camera: Not available")
        
        try:
            ServoControllerFactory.create_controller(ServoControllerType.PCA9685).shutdown()
            print("  🎛️  PCA9685 Servos: Available")
        except:
            print("  🎛️  PCA9685 Servos: Not available")
        
        try:
            ServoControllerFactory.create_controller(ServoControllerType.GPIO).shutdown()
            print("  🔌 GPIO Servos: Available")
        except:
            print("  🔌 GPIO Servos: Not available")
        
        print("\nTo run the full demo (requires display):")
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