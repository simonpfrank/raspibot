# Display Setup for Raspberry Pi Connect

## Overview

This document explains how to set up display functionality when using Raspberry Pi Connect (WayVNC) for remote desktop access.

## Environment Detection

The Display class automatically detects and handles different display environments:

### 1. Raspberry Pi Connect (WayVNC)
- **Auto-detection**: Detects WayVNC socket at `/tmp/wayvnc/wayvncctl.sock`
- **X11 Integration**: Automatically sets `DISPLAY=:0` if X11 server is available
- **Window Creation**: Creates OpenCV windows that appear in your remote desktop

### 2. Headless Environment
- **Fallback Mode**: Runs in headless mode with logging instead of GUI
- **No Dependencies**: Doesn't require display server
- **CI/CD Compatible**: Works in automated testing environments

## Manual Setup

### Option 1: Environment Variable (Recommended)
```bash
# Add to ~/.bashrc for permanent setup
export DISPLAY=:0

# Or set temporarily
export DISPLAY=:0
```

### Option 2: Test Runner Script
```bash
# Use the provided script
./run_tests.sh

# Or run specific tests
./run_tests.sh tests/integration/test_vision_integration.py
```

### Option 3: Force Headless Mode
```python
# In your code
display = Display(headless=True)
```

## Troubleshooting

### Issue: "Cannot open display"
**Solution**: Set DISPLAY environment variable
```bash
export DISPLAY=:0
```

### Issue: "No module named 'cv2'"
**Solution**: Activate virtual environment
```bash
source .venv/bin/activate
```

### Issue: Tests fail in CI/CD
**Solution**: Use headless mode
```python
display = Display(headless=True)
```

## Display Configuration

### Available Resolutions (WayVNC)
- 1464x759 (current)
- 1280x720
- 1024x576
- 800x600
- 640x480

### Performance Notes
- OpenCV windows work well over VNC
- Frame rate may be limited by network connection
- Consider headless mode for high-performance applications

## Testing

### Run Display Tests
```bash
# All integration tests
./run_tests.sh tests/integration/test_vision_integration.py

# Just display test
./run_tests.sh tests/integration/test_vision_integration.py::TestVisionIntegration::test_display_integration
```

### Verify Display Works
```bash
# Test OpenCV window creation
python -c "import cv2; cv2.namedWindow('test'); cv2.destroyWindow('test'); print('Success')"
```

## Integration with Face Tracking

The Display class integrates seamlessly with the face tracking system:

```python
from raspibot.vision.display import Display
from raspibot.vision.camera import Camera
from raspibot.vision.face_detector import FaceDetector

# Initialize components
camera = Camera()
detector = FaceDetector()
display = Display()  # Auto-detects environment

# Main loop
while True:
    frame = camera.get_frame()
    faces = detector.detect_faces(frame)
    
    # Display with face detection
    if not display.show_frame(frame, faces=faces):
        break  # User pressed 'q'

display.close()
```

## Best Practices

1. **Always use the Display class**: Don't call OpenCV functions directly
2. **Handle headless environments**: Use `headless=True` for CI/CD
3. **Clean up resources**: Always call `display.close()`
4. **Use context manager**: `with Display() as display:`
5. **Test in your environment**: Run tests before deploying

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DISPLAY` | X11 display server | `:0` |
| `WAYLAND_DISPLAY` | Wayland display | `wayland-0` |
| `XDG_SESSION_TYPE` | Session type | `wayland` or `x11` | 