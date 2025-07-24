# Iteration 3 Tech Spec: Face Detection & Tracking

**Version**: 1.0  
**Date**: 2024-07-21  
**Focus**: Computer Vision with Face Detection and Tracking  
**PRD Support**: Implements PRD Phase 1 - Face detection and tracking system  
**Dependencies**: Iteration 2 (Servo Control System)

## 1. Overview

### 1.1 Objective
Implement a comprehensive face detection and tracking system that automatically centers the camera on detected faces using the pan/tilt system from Iteration 2. The system must support multiple camera types and handle multiple faces in the field of view.

### 1.2 Key Requirements
- **Simple camera interface**: Start with webcam, easy to extend
- **Face detection**: Real-time detection using OpenCV
- **Face tracking**: Automatic centering with pan/tilt movement
- **Visual display**: Show camera feed with face detection boxes
- **Coordinate translation**: Simple pixel-to-servo conversion
- **Sleep mode**: Dramatic movement sequence to tilt down, pan center position

### 1.3 Success Criteria
- Face detection at ≥10 FPS at 1280x480 resolution
- Automatic face centering within 2 seconds of detection
- Support for multiple faces with intelligent centering
- Seamless operation with both servo controller types
- Comprehensive test coverage (70%+)

## 2. Architecture

### 2.1 System Components

```
raspibot/
├── vision/                      # Computer vision modules
│   ├── __init__.py
│   ├── camera.py                # Simple camera class (webcam first)
│   ├── face_detector.py         # Face detection with OpenCV
│   ├── face_tracker.py          # Face tracking logic
│   └── display.py               # Visual display for camera feed
├── movement/                    # Movement system (from Iteration 2)
│   └── pan_tilt.py             # Pan/tilt system
└── core/                        # Simple integration
    └── face_tracking_robot.py   # Main robot class
```

### 2.2 Design Patterns
- **Abstract Factory**: Camera creation and management
- **Strategy Pattern**: Different face detection algorithms
- **Observer Pattern**: Face detection events to tracking system
- **Adapter Pattern**: Coordinate system translation

## 3. Simple Implementation

### 3.1 Camera (`raspibot/vision/camera.py`)

```python
import cv2
import numpy as np
from typing import Optional, Tuple

class Camera:
    """Simple camera class - start with webcam, easy to extend later."""
    
    def __init__(self, device_id: int = 0, width: int = 1280, height: int = 480):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.cap = None
    
    def start(self) -> bool:
        """Start camera capture."""
        self.cap = cv2.VideoCapture(self.device_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return self.cap.isOpened()
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get a single frame."""
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def stop(self) -> None:
        """Stop camera capture."""
        if self.cap:
            self.cap.release()
```

### 3.2 Face Detector (`raspibot/vision/face_detector.py`)

```python
import cv2
import numpy as np
from typing import List, Tuple

class FaceDetector:
    """Simple face detection using OpenCV."""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces and return rectangles (x, y, w, h)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        return [(x, y, w, h) for (x, y, w, h) in faces]
    
    def get_largest_face(self, faces: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
        """Get the largest face from the list."""
        if not faces:
            return None
        return max(faces, key=lambda face: face[2] * face[3])  # max by area (w * h)
    
    def get_face_center(self, face: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Get center point of face rectangle."""
        x, y, w, h = face
        return (x + w // 2, y + h // 2)
```

### 3.3 Face Tracker (`raspibot/vision/face_tracker.py`)

```python
import time
from typing import Optional, Tuple
from .face_detector import FaceDetector
from ..movement.pan_tilt import PanTiltSystem

class FaceTracker:
    """Simple face tracking - center camera on largest stable face."""
    
    def __init__(self, pan_tilt: PanTiltSystem, camera_width: int = 1280, camera_height: int = 480):
        self.pan_tilt = pan_tilt
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.face_detector = FaceDetector()
        self.last_face_time = time.time()
        self.sleep_timeout = 300  # 5 minutes
        
        # Movement and stability thresholds
        self.movement_threshold = 50  # pixels
        self.stability_threshold = 100  # pixels - faces moving more than this are ignored
        self.stability_frames = 3  # face must be stable for this many frames
        self.face_history = []  # track recent face positions for stability
    
    def track_face(self, frame) -> Optional[Tuple[int, int, int, int]]:
        """Track faces and move camera. Returns largest stable face if found."""
        faces = self.face_detector.detect_faces(frame)
        largest_face = self.face_detector.get_largest_face(faces)
        
        if largest_face:
            stable_face = self._check_face_stability(largest_face)
            if stable_face:
                self.last_face_time = time.time()
                self._center_on_face(stable_face)
                return stable_face
        
        # Clean up old face history
        self._cleanup_face_history()
        
        # Check if we should go to sleep
        if time.time() - self.last_face_time > self.sleep_timeout:
            self._go_to_sleep()
        return None
    
    def _check_face_stability(self, face: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        """Check if face is stable enough to track (not fast-moving)."""
        face_center = self.face_detector.get_face_center(face)
        current_time = time.time()
        
        # Add current face to history
        self.face_history.append((current_time, face_center, face))
        
        # Keep only recent history
        self.face_history = [(t, center, f) for t, center, f in self.face_history 
                            if current_time - t < 2.0]  # 2 second window
        
        # Need at least stability_frames to consider stable
        if len(self.face_history) < self.stability_frames:
            return None
        
        # Check if recent faces are close together (stable)
        recent_centers = [center for _, center, _ in self.face_history[-self.stability_frames:]]
        
        for i in range(1, len(recent_centers)):
            distance = ((recent_centers[i][0] - recent_centers[0][0]) ** 2 + 
                       (recent_centers[i][1] - recent_centers[0][1]) ** 2) ** 0.5
            if distance > self.stability_threshold:
                return None  # Face is moving too fast, ignore
        
        return face  # Face is stable, track it
    
    def _cleanup_face_history(self) -> None:
        """Remove old face history entries."""
        current_time = time.time()
        self.face_history = [(t, center, f) for t, center, f in self.face_history 
                            if current_time - t < 2.0]
    
    def _center_on_face(self, face: Tuple[int, int, int, int]) -> None:
        """Center camera on face using simple coordinate conversion.
        
        Note: This coordinate system is designed to be extensible for future 
        view mapping experiments where we'll map camera coordinates to 
        world/room coordinates.
        """
        face_x, face_y = self.face_detector.get_face_center(face)
        
        # Convert to camera center offset
        offset_x = face_x - (self.camera_width // 2)
        offset_y = face_y - (self.camera_height // 2)
        
        # Only move if offset is significant
        if abs(offset_x) > self.movement_threshold or abs(offset_y) > self.movement_threshold:
            # Simple proportion-based movement
            move_x = offset_x / (self.camera_width // 2)   # -1.0 to 1.0
            move_y = offset_y / (self.camera_height // 2)  # -1.0 to 1.0
            
            # Get current position and adjust
            current_x, current_y = self.pan_tilt.get_current_coordinates()
            new_x = max(-1.0, min(1.0, current_x + move_x * 0.3))  # Scale down movement
            new_y = max(-1.0, min(1.0, current_y + move_y * 0.3))
            
            self.pan_tilt.move_to_coordinates(new_x, new_y)
    
    def _go_to_sleep(self) -> None:
        """Go to sleep position with drama."""
        # Simple dramatic sequence
        self.pan_tilt.move_to_coordinates(-0.5, 0)    # Look left
        time.sleep(0.5)
        self.pan_tilt.move_to_coordinates(0.5, 0)     # Look right  
        time.sleep(0.5)
        self.pan_tilt.move_to_coordinates(0, 0.3)     # Look up slightly
        time.sleep(0.5)
        self.pan_tilt.move_to_coordinates(0, -1.0)    # Look down (sleep)
```

### 3.4 Display (`raspibot/vision/display.py`)

```python
import cv2
import numpy as np
from typing import List, Tuple, Optional

class Display:
    """Simple display for camera feed with face detection boxes."""
    
    def __init__(self, window_name: str = "Face Tracking Robot"):
        self.window_name = window_name
        cv2.namedWindow(self.window_name)
    
    def show_frame(self, frame: np.ndarray, faces: List[Tuple[int, int, int, int]] = None) -> bool:
        """Show frame with face detection boxes. Returns False if user pressed 'q'."""
        display_frame = frame.copy()
        
        # Draw face rectangles
        if faces:
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Draw center point
                center_x, center_y = x + w // 2, y + h // 2
                cv2.circle(display_frame, (center_x, center_y), 5, (0, 255, 0), -1)
        
        # Add status text
        cv2.putText(display_frame, f"Faces: {len(faces) if faces else 0}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow(self.window_name, display_frame)
        return cv2.waitKey(1) & 0xFF != ord('q')
    
    def close(self) -> None:
        """Close display window."""
        cv2.destroyAllWindows()
```

### 3.5 Main Robot Class (`raspibot/core/face_tracking_robot.py`)

```python
import time
from ..hardware.servo_factory import ServoControllerFactory, ServoControllerType
from ..movement.pan_tilt import PanTiltSystem
from ..vision.camera import Camera
from ..vision.face_tracker import FaceTracker
from ..vision.display import Display

class FaceTrackingRobot:
    """Simple face tracking robot - brings it all together."""
    
    def __init__(self, servo_type: str = "pca9685"):
        # Initialize hardware
        controller_type = ServoControllerType.PCA9685 if servo_type == "pca9685" else ServoControllerType.GPIO
        self.servo_controller = ServoControllerFactory.create_controller(controller_type)
        self.pan_tilt = PanTiltSystem(self.servo_controller)
        
        # Initialize vision
        self.camera = Camera()
        self.face_tracker = FaceTracker(self.pan_tilt)
        self.display = Display()
        
        self.running = False
    
    def start(self) -> None:
        """Start the face tracking robot."""
        if not self.camera.start():
            raise RuntimeError("Failed to start camera")
        
        # Start in center position
        self.pan_tilt.move_to_coordinates(0, 0)
        self.running = True
        
        print("Face tracking robot started! Press 'q' to quit.")
        
        try:
            while self.running:
                frame = self.camera.get_frame()
                if frame is None:
                    continue
                
                # Track faces
                largest_face = self.face_tracker.track_face(frame)
                faces = [largest_face] if largest_face else []
                
                # Show display
                if not self.display.show_frame(frame, faces):
                    break
                
                time.sleep(0.03)  # ~30 FPS
                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the robot."""
        self.running = False
        self.camera.stop()
        self.display.close()
        self.servo_controller.shutdown()
```

## 4. Simple Demo Script

### 4.1 Demo Script (`scripts/face_tracking_demo.py`)

```python
#!/usr/bin/env python3
"""Simple face tracking demo script."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from raspibot.core.face_tracking_robot import FaceTrackingRobot

def main():
    """Run the face tracking demo."""
    print("=== Face Tracking Robot Demo ===")
    print("Starting face tracking robot...")
    print("Press 'q' in the camera window to quit")
    
    # Create and start robot
    try:
        robot = FaceTrackingRobot(servo_type="pca9685")  # or "gpio"
        robot.start()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## 5. Simple Configuration

### 5.1 Basic Constants (`raspibot/config/hardware_config.py`)

```python
# Camera Configuration
CAMERA_DEFAULT_WIDTH: Final[int] = 1280
CAMERA_DEFAULT_HEIGHT: Final[int] = 480
CAMERA_DEVICE_ID: Final[int] = 0

# Face Tracking Configuration  
FACE_MOVEMENT_THRESHOLD: Final[int] = 50   # pixels - minimum movement to trigger servo
FACE_MOVEMENT_SCALE: Final[float] = 0.3    # how much to move servo per pixel offset
FACE_STABILITY_THRESHOLD: Final[int] = 100 # pixels - max movement to be considered stable
FACE_STABILITY_FRAMES: Final[int] = 3      # frames needed to confirm stability
SLEEP_TIMEOUT: Final[int] = 300            # 5 minutes of no faces
```

## 6. Simple Implementation Plan

### 6.1 Day 1: Basic Vision Setup
- [ ] Create `Camera` class (simple OpenCV wrapper)
- [ ] Create `FaceDetector` class (OpenCV face detection)
- [ ] Create `Display` class (show camera feed with boxes)
- [ ] Test camera and face detection

### 6.2 Day 2: Face Tracking
- [ ] Create `FaceTracker` class (coordinate conversion)
- [ ] Integrate with existing pan/tilt system
- [ ] Add sleep mode with dramatic sequence
- [ ] Test tracking with real hardware

### 6.3 Day 3: Integration & Demo
- [ ] Create `FaceTrackingRobot` main class
- [ ] Create demo script
- [ ] Add basic tests
- [ ] Performance tuning and documentation

## 7. Simple Testing

### 7.1 Basic Tests
- **Face detection**: Verify faces are detected in test images
- **Camera**: Verify camera starts and captures frames
- **Tracking**: Verify servo moves when face moves
- **Sleep mode**: Verify dramatic sequence works

### 7.2 Demo Testing
- **Real-time demo**: Test with live camera and servo movement
- **Performance**: Ensure smooth operation at ~30 FPS

## 8. Dependencies

### 8.1 Python Dependencies
```txt
opencv-python>=4.8.0  # Face detection and camera
numpy>=1.24.0         # Image processing
```

### 8.2 Internal Dependencies
- Uses existing `PanTiltSystem` from Iteration 2
- Uses existing servo controller abstractions

## 9. Success Criteria

### 9.1 Core Functionality
- Face detection works with webcam
- Camera view displays with face detection boxes
- Servo tracks faces smoothly
- Sleep mode activates after timeout with dramatic sequence

### 9.2 Performance Goals
- Real-time face detection (≥10 FPS)
- Smooth servo movement without jitter
- Responsive face tracking (< 1 second delay)

### 9.3 Tutorial Goals
- Code is simple and easy to understand
- Clear separation of concerns (camera, detection, tracking, display)
- Easy to extend for future camera types
- Architecture supports future experiments (view mapping, curiosity features)
- Good documentation and examples 