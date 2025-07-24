# Search Pattern System Guide

## Overview

The Search Pattern System implements a **systematic raster scan** approach to face detection when no faces are detected in the current camera view. This replaces the previous "wait and react" approach with an active search strategy.

## How It Works

### 🔍 **Raster Scan Pattern**

The system performs a systematic search using a **raster scan pattern**:

1. **Start Position**: Begins at the top-left (or bottom-left) of the camera's field of view
2. **Horizontal Sweep**: Moves horizontally across the field of view
3. **Vertical Step**: Moves down (or up) to the next level
4. **Reverse Direction**: Sweeps in the opposite direction
5. **Repeat**: Continues until the entire field is covered

### 📊 **Search Configuration**

```python
# From hardware_config.py
SEARCH_PATTERN_ENABLED: Final[bool] = True      # Enable/disable search patterns
SEARCH_PAN_STEPS: Final[int] = 8               # Number of pan steps per tilt level
SEARCH_TILT_STEPS: Final[int] = 6              # Number of tilt levels to scan
SEARCH_MOVEMENT_SPEED: Final[float] = 0.3      # Slow movement speed (0.1-1.0)
SEARCH_STABILIZATION_DELAY: Final[float] = 0.5 # Delay after movement (seconds)
SEARCH_FACE_DETECTION_DELAY: Final[float] = 0.2 # Face detection delay (seconds)
SEARCH_PATTERN_TIMEOUT: Final[int] = 60        # Search timeout (seconds)
SEARCH_RETURN_TO_CENTER: Final[bool] = True    # Return to center after search
```

### 🎯 **Search Triggers**

The search pattern activates when:

1. **No faces detected** for the configured interval (default: 30 seconds)
2. **Manual trigger** via `force_search()` method
3. **After wake-up** from sleep mode

### 🛑 **Search Termination**

The search stops when:

1. **Faces detected** at any search position
2. **Manual stop** via `stop_search()` method
3. **Timeout reached** (default: 60 seconds)
4. **User interaction** (pressing 'q' in display)

## Usage Examples

### Basic Usage

```python
from raspibot.core.face_tracking_robot import FaceTrackingRobot

# Create robot with search pattern enabled
robot = FaceTrackingRobot(servo_type="pca9685", camera_device=0)

# Start face tracking (search pattern will activate automatically)
robot.start()
```

### Manual Search Control

```python
# Force start search pattern
success = robot.force_search()

# Stop current search
robot.stop_search()

# Get search status
status = robot.get_search_status()
print(f"Search active: {status['active']}")
print(f"Progress: {status['progress']}")
print(f"Time remaining: {status['time_remaining']:.1f}s")
```

### Custom Search Parameters

```python
from raspibot.vision.search_pattern import SearchDirection

# Get search pattern instance
search_pattern = robot.face_tracker.search_pattern

# Configure custom parameters
search_pattern.set_search_parameters(
    pan_steps=6,                    # Fewer pan steps (faster)
    tilt_steps=4,                   # Fewer tilt levels
    movement_speed=0.5,             # Faster movement
    direction=SearchDirection.UP_FIRST  # Start from bottom
)

# Set search interval
robot.set_search_interval(15.0)  # Search every 15 seconds
```

## Demo Script

Use the provided demo script to test the search pattern:

```bash
# Basic demo
python scripts/search_pattern_demo.py

# Custom parameters
python scripts/search_pattern_demo.py \
    --servo gpio \
    --direction up \
    --interval 15 \
    --pan-steps 6 \
    --tilt-steps 4 \
    --speed 0.5
```

## Configuration Options

### Search Direction

- **DOWN_FIRST**: Start from top, scan downward (default)
- **UP_FIRST**: Start from bottom, scan upward

### Movement Speed

- **0.1**: Very slow, precise movements
- **0.3**: Slow, smooth movements (default)
- **0.5**: Medium speed
- **1.0**: Fast movements

### Grid Density

- **High Density** (8x6): Thorough coverage, slower
- **Medium Density** (6x4): Balanced coverage and speed
- **Low Density** (4x3): Fast search, less thorough

## Integration with Face Tracking

### Automatic Integration

The search pattern integrates seamlessly with the face tracking system:

1. **Normal Operation**: Face tracking works as before
2. **No Faces Detected**: Search pattern activates after timeout
3. **Faces Found**: Search stops, normal tracking resumes
4. **Sleep Mode**: Search pattern respects sleep/wake cycles

### Status Display

The display shows search pattern status:

```
Faces: 0 (Stable: 0, Unstable: 0)
Camera FPS: 30.0
Detection FPS: 15.0
Servo: Pan 0.25, Tilt -0.10
Search: ACTIVE
Press 'q' to quit
```

## Performance Considerations

### Timing

- **Complete Search**: ~60 seconds (8x6 grid, 0.3 speed)
- **Face Detection**: 0.2 seconds per position
- **Movement**: 0.5 seconds stabilization per position
- **Total Coverage**: 48 positions (8 pan × 6 tilt)

### Optimization

For faster searches:
- Reduce `pan_steps` and `tilt_steps`
- Increase `movement_speed`
- Decrease `stabilization_delay`

For more thorough searches:
- Increase `pan_steps` and `tilt_steps`
- Decrease `movement_speed`
- Increase `stabilization_delay`

## Troubleshooting

### Search Not Starting

1. **Check Configuration**: Ensure `SEARCH_PATTERN_ENABLED = True`
2. **Check Interval**: Verify search interval is reasonable (>5 seconds)
3. **Check Hardware**: Ensure servos and camera are working

### Search Too Slow/Fast

1. **Adjust Speed**: Modify `SEARCH_MOVEMENT_SPEED`
2. **Adjust Grid**: Change `SEARCH_PAN_STEPS` and `SEARCH_TILT_STEPS`
3. **Adjust Delays**: Modify stabilization and detection delays

### Search Not Finding Faces

1. **Check Coverage**: Increase grid density
2. **Check Timing**: Increase stabilization delay
3. **Check Lighting**: Ensure adequate lighting for face detection

## Advanced Features

### Custom Search Patterns

You can implement custom search patterns by extending the `SearchPattern` class:

```python
class CustomSearchPattern(SearchPattern):
    def _calculate_search_positions(self):
        # Implement custom position calculation
        pass
```

### Search Pattern Recording

The system records search positions for analysis:

```python
# Get search positions
positions = search_pattern.search_positions
for i, (pan, tilt) in enumerate(positions):
    print(f"Position {i}: pan={pan:.1f}°, tilt={tilt:.1f}°")
```

### Integration with Other Systems

The search pattern can be integrated with:

- **Audio Systems**: Search toward detected sounds
- **Motion Sensors**: Focus on areas with movement
- **AI Models**: Use object detection for better targeting

## Best Practices

1. **Start Conservative**: Use default settings first
2. **Test Thoroughly**: Verify search coverage in your environment
3. **Monitor Performance**: Watch for servo stress or overheating
4. **Adjust Gradually**: Make small changes and test
5. **Document Settings**: Keep track of optimal configurations

## Future Enhancements

### Planned Features

- **Adaptive Search**: Learn from successful face detection
- **Multi-Pattern Support**: Different search patterns for different scenarios
- **Audio Integration**: Search toward detected sounds
- **Motion Detection**: Focus on moving objects
- **AI-Powered Search**: Use machine learning for optimal search paths 