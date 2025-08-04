# Camera Modes Implementation

## Overview

This document describes the implementation of camera modes in the raspibot vision module. The new camera modes provide optimized configurations for different use cases while maintaining backward compatibility.

## Camera Modes

### 1. Normal Video Mode (`normal_video`)
- **Purpose**: Standard video capture and display
- **Detection Resolution**: 1280x720
- **Detection Format**: XBGR8888 (color)
- **Display Resolution**: 1280x720
- **Display Format**: BGR (color)
- **Memory Usage**: 3.52 MB/frame
- **Use Case**: Live video feed, user interface, monitoring

### 2. AI Detection Mode (`ai_detection`)
- **Purpose**: High-resolution AI detection with 50% memory reduction
- **Detection Resolution**: 1920x1080
- **Detection Format**: YUV420 (color with 50% memory reduction)
- **Display Resolution**: 1280x720
- **Display Format**: BGR (color)
- **Memory Usage**: 2.64 MB/frame
- **Use Case**: AI detection at all resolutions, IMX500 hardware acceleration

### 3. OpenCV Detection Mode (`opencv_detection`)
- **Purpose**: Grayscale processing for OpenCV face detection
- **Detection Resolution**: 1280x720
- **Detection Format**: Grayscale
- **Display Resolution**: 1280x720
- **Display Format**: BGR (color)
- **Memory Usage**: 0.88 MB/frame
- **Use Case**: OpenCV face detection, object recognition, tracking

## Implementation Details

### Configuration Updates

#### `raspibot/config/hardware_config.py`
- Added `camera_modes` section to `PI_AI_CAMERA_CONFIG`
- Each mode defines detection and display configurations
- Added YUV420 processing benefits documentation
- Maintained backward compatibility with legacy configurations

### Camera Class Updates

#### `raspibot/vision/pi_ai_camera.py`
- Added `camera_mode` parameter to constructor
- Updated `start()` method to configure camera based on mode
- Added `get_detection_frame()` method for format-specific frame capture
- Added `get_camera_mode_info()` method for mode information
- Enhanced `get_frame()` and `get_frame_grayscale()` for mode-specific processing

#### `raspibot/vision/pi_camera.py`
- Added `camera_mode` parameter to constructor
- Updated initialization to set appropriate resolution and format
- Added `get_detection_frame()` method for OpenCV detection
- Added `get_camera_mode_info()` method for mode information
- Enhanced `get_frame()` for BGR conversion

### Example Updates

#### `examples/basic/camera_basics.py`
- Added `--camera-mode` argument
- Updated to use `camera_selector` with mode parameter
- Enhanced output to show camera mode information

#### `examples/basic/face_detection.py`
- Added `--camera-mode` argument (defaults to `opencv_detection`)
- Updated to use `camera_selector` with mode parameter
- Uses `get_detection_frame()` for better performance
- Shows camera mode information

#### `examples/advanced/pi_ai_camera.py`
- Added `--camera-mode` argument (defaults to `ai_detection`)
- Updated to use detection frame for AI detection mode
- Shows detailed camera mode information

### Test Updates

#### `tests/unit/test_vision/test_camera_selector.py`
- Added tests for camera mode parameter passing
- Tests for both Pi AI and Basic camera modes

#### `tests/unit/test_pi_ai_camera.py`
- Added tests for camera mode initialization
- Added tests for invalid camera mode handling
- Added tests for camera mode information retrieval

#### `tests/unit/test_vision/test_camera.py`
- Added `TestPiCamera` class
- Tests for camera mode initialization
- Tests for detection frame capture
- Tests for camera mode information

## Usage Examples

### Command Line Usage

```bash
# Normal video mode
python examples/basic/camera_basics.py --camera-mode normal_video

# AI detection mode
python examples/advanced/pi_ai_camera.py --camera-mode ai_detection

# OpenCV detection mode
python examples/basic/face_detection.py --camera-mode opencv_detection
```

### Programmatic Usage

```python
from raspibot.vision.camera_selector import get_camera

# Create camera with specific mode
camera = get_camera("pi_ai", camera_mode="ai_detection")

# Get mode information
mode_info = camera.get_camera_mode_info()
print(f"Detection resolution: {mode_info['detection']['resolution']}")

# Get frames in appropriate format
display_frame = camera.get_frame()  # BGR format for display
detection_frame = camera.get_detection_frame()  # Format-specific for detection
```

## Benefits

### Memory Efficiency
- **YUV420**: 50% memory reduction vs color formats
- **Grayscale**: 75% memory reduction vs color formats
- **AI Detection**: Works at all resolutions with YUV420

### Performance
- **AI Detection**: Higher resolution (1920x1080) with efficient format
- **OpenCV Detection**: Optimized grayscale processing
- **Display**: Always BGR format for consistent overlays

### Flexibility
- **Backward Compatibility**: Existing code continues to work
- **Mode Selection**: Easy switching between modes
- **Format Optimization**: Automatic format conversion for display

## Migration Guide

### For Existing Code
- No changes required for basic usage
- Camera modes are optional parameters
- Default behavior remains unchanged

### For New Features
- Use `camera_mode` parameter for optimized configurations
- Use `get_detection_frame()` for detection-specific processing
- Use `get_camera_mode_info()` for mode information

### For Examples
- Add `--camera-mode` argument to command line interfaces
- Use `camera_selector` instead of direct camera instantiation
- Display camera mode information for better user experience

## Future Enhancements

### Planned Features
- **Webcam Modes**: Extend camera modes to webcam implementations
- **Dynamic Mode Switching**: Runtime mode changes
- **Custom Mode Definitions**: User-defined camera configurations
- **Performance Monitoring**: Real-time mode performance metrics

### Potential Improvements
- **Format Validation**: Ensure format compatibility across modes
- **Resolution Scaling**: Automatic resolution adjustment
- **Memory Monitoring**: Track memory usage per mode
- **Error Handling**: Enhanced error messages for mode-specific issues 