# Display Setup for Raspberry Pi Connect

## Overview

This document explains how to set up display functionality when using Raspberry Pi Connect (WayVNC) for remote desktop access.

## Pi 5 Headless Display Issue

**Problem**: Raspberry Pi 5 running headless (no monitor connected) cannot use Wayland/WayVNC for Pi Connect screen sharing. The GPU/DRM devices (`/dev/dri/`) are not created without a physical display, causing Wayfire to crash with "Found 0 GPUs, cannot create backend".

**Symptoms**:
- Pi Connect shows "Screen sharing: allowed" but cannot connect
- `~/.xsession-errors` shows: `Failed to open any DRM device`
- `/dev/dri/` directory does not exist
- `rpi-connect-wayvnc` service fails with: `test -S /run/user/1001/wayland-0` failure

### Solution 1: X11 Mode (Headless Workaround)

Use X11 instead of Wayland when running without a monitor:

```bash
sudo raspi-config
```
→ Advanced Options → Wayland → **X11** → Reboot

X11 can use a virtual framebuffer and works headless with Pi Connect.

### Solution 2: Connect HDMI Display (Enables Wayland)

When you have a micro HDMI adapter/cable:

1. Connect any HDMI display to Pi 5 (micro HDMI port)
2. Switch back to Wayland:
   ```bash
   sudo raspi-config
   ```
   → Advanced Options → Wayland → **Wayfire** (or **LabWC**) → Reboot

3. Verify it works:
   ```bash
   ls -la /dev/dri/           # Should show card0, card1, renderD128
   ls -la /run/user/1001/wayland*  # Should show wayland-0 or wayland-1
   systemctl --user status rpi-connect-wayvnc  # Should be active
   ```

4. Pi Connect screen sharing should now work

### Solution 3: HDMI Dummy Plug (Permanent Headless Wayland)

For permanent headless Wayland operation, use an HDMI dummy plug (~$5-10):
- Plugs into micro HDMI port
- Emulates a connected display
- GPU devices are created
- Wayland/WayVNC works without real monitor

### Switching Between X11 and Wayland

| Mode | Command | Use Case |
|------|---------|----------|
| X11 | `sudo raspi-config` → Advanced → Wayland → X11 | Headless, no display |
| Wayfire | `sudo raspi-config` → Advanced → Wayland → Wayfire | Display connected |
| LabWC | `sudo raspi-config` → Advanced → Wayland → LabWC | Display connected (alternative) |

**Always reboot after changing this setting.**

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

### Issue: Pi Connect screen sharing doesn't work (Pi 5 headless)
**Cause**: No GPU devices created without display connected
**Solution**: Switch to X11 mode (see "Pi 5 Headless Display Issue" above)
```bash
sudo raspi-config  # → Advanced Options → Wayland → X11
sudo reboot
```

### Issue: Qt platform plugin "wayland" fails to load
**Error**: `Could not load the Qt platform plugin "wayland"`
**Cause**: No Wayland display socket exists
**Solution**: Either switch to X11 or connect a display (see above)

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