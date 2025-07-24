#!/usr/bin/env python3
"""Test script for Pi AI Camera integration."""

import argparse
import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.vision.camera_factory import CameraFactory, CameraType
from raspibot.vision.detection_models import PersonDetection
from raspibot.utils.logging_config import setup_logging


def test_camera_availability():
    """Test camera availability detection."""
    print("=== Testing Camera Availability ===")
    
    available_cameras = CameraFactory.get_available_cameras()
    print(f"Available camera types: {[c.value for c in available_cameras]}")
    
    recommended = CameraFactory.get_recommended_camera()
    print(f"Recommended camera: {recommended.value}")
    
    pi_ai_available = CameraFactory.is_pi_ai_available()
    print(f"Pi AI camera available: {pi_ai_available}")
    
    return pi_ai_available


def test_camera_creation(camera_type: str):
    """Test camera creation."""
    print(f"\n=== Testing Camera Creation ({camera_type}) ===")
    
    try:
        camera = CameraFactory.create_camera(camera_type)
        print(f"✓ Successfully created {camera_type} camera")
        print(f"  Camera class: {type(camera).__name__}")
        
        # Test camera interface methods
        print(f"  Resolution: {camera.get_resolution()}")
        print(f"  Available: {camera.is_available()}")
        
        return camera
        
    except Exception as e:
        print(f"✗ Failed to create {camera_type} camera: {e}")
        return None


def test_camera_operation(camera, duration: int = 5):
    """Test camera operation."""
    print(f"\n=== Testing Camera Operation ({duration}s) ===")
    
    try:
        # Start camera
        if not camera.start():
            print("✗ Failed to start camera")
            return False
        
        print("✓ Camera started successfully")
        print(f"  Resolution: {camera.get_resolution()}")
        
        # Capture frames
        frame_count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            frame = camera.get_frame()
            if frame is not None:
                frame_count += 1
                print(f"  Frame {frame_count}: {frame.shape}")
                
                # Test detections if available
                if hasattr(camera, 'get_detections'):
                    detections = camera.get_detections()
                    if detections:
                        print(f"    Detections: {len(detections)} people")
                        for i, detection in enumerate(detections):
                            print(f"      Person {i+1}: {detection.bbox}, confidence: {detection.confidence:.2f}")
                
                time.sleep(0.1)  # Small delay
            else:
                print("  ✗ Failed to capture frame")
                break
        
        # Calculate FPS
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"  Captured {frame_count} frames in {elapsed:.1f}s ({fps:.1f} FPS)")
        
        # Stop camera
        camera.stop()
        print("✓ Camera stopped successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Camera operation failed: {e}")
        return False


def test_detection_models():
    """Test detection model data structures."""
    print("\n=== Testing Detection Models ===")
    
    try:
        # Test PersonDetection
        person = PersonDetection(
            bbox=(100, 200, 150, 300),
            confidence=0.85,
            category="person"
        )
        
        print(f"✓ PersonDetection created successfully")
        print(f"  Bbox: {person.bbox}")
        print(f"  Center: {person.center}")
        print(f"  Area: {person.area}")
        print(f"  Confidence: {person.confidence}")
        
        return True
        
    except Exception as e:
        print(f"✗ Detection model test failed: {e}")
        return False


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Pi AI Camera integration")
    parser.add_argument("--camera", choices=["auto", "webcam", "pi_ai"], 
                       default="auto", help="Camera type to test")
    parser.add_argument("--duration", type=int, default=5, 
                       help="Test duration in seconds")
    parser.add_argument("--skip-operation", action="store_true",
                       help="Skip camera operation test")
    
    args = parser.parse_args()
    
    print("Pi AI Camera Integration Test")
    print("=" * 40)
    
    # Test availability
    pi_ai_available = test_camera_availability()
    
    # Test detection models
    models_ok = test_detection_models()
    
    # Test camera creation
    camera = test_camera_creation(args.camera)
    
    # Test camera operation
    operation_ok = False
    if camera and not args.skip_operation:
        operation_ok = test_camera_operation(camera, args.duration)
    
    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)
    print(f"Pi AI Camera Available: {'✓' if pi_ai_available else '✗'}")
    print(f"Detection Models: {'✓' if models_ok else '✗'}")
    print(f"Camera Creation: {'✓' if camera else '✗'}")
    print(f"Camera Operation: {'✓' if operation_ok else '✗'}")
    
    if pi_ai_available and models_ok and camera and operation_ok:
        print("\n🎉 All tests passed! Pi AI Camera integration is working.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 