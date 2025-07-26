# Examples Directory

This directory contains educational examples and demonstrations for the Raspibot project, organized by complexity and purpose.

## Directory Structure

### `/basic/` - Simple Examples
Start here if you're new to the project. These examples demonstrate single concepts and are easy to understand.

- **camera_basics.py** - Basic camera operations and selection
- **camera_capture.py** - Simple camera capture and display
- **face_detection.py** - Simple face detection without tracking
- **face_tracking_simple.py** - Basic face tracking demonstration
- **servo_control.py** - Interactive servo control with patterns and individual servo control

### `/advanced/` - Feature Demonstrations
Complete feature demonstrations that showcase the full capabilities of the system.

- **face_tracking.py** - Complete face tracking with servo control
- **face_tracking_headless.py** - Headless operation for deployment
- **pi_ai_camera.py** - Pi AI camera with people detection
- **search_patterns.py** - Systematic search when no faces found

### `/hardware/` - Hardware Tutorials
Hardware-specific examples and tutorials for servo control and GPIO operations.

- **gpio_servo_basics.py** - Direct GPIO servo control
- **gpio_stability_test.py** - GPIO anti-jitter testing
- **servo_positioning.py** - Interactive servo positioning with proper angle ranges
- **servo_system_demo.py** - Complete servo system test with factory, interface, and pan/tilt

## How to Run Examples

1. **Prerequisites**: Ensure you have installed all dependencies (see `scripts/setup/install_dependencies.sh`)
2. **Hardware Setup**: Most examples require specific hardware (camera, servos, etc.)
3. **Run from project root**: `python examples/basic/camera_basics.py`

## Example Progression

For beginners, we recommend this learning path:

1. Start with `/basic/camera_capture.py` to understand basic camera operations
2. Try `/basic/camera_basics.py` to learn about camera selection
3. Explore `/basic/servo_control.py` to understand servo movement
4. Try `/basic/face_detection.py` to see face detection in action
5. Move to `/basic/face_tracking_simple.py` for basic tracking
6. Explore `/hardware/` examples for advanced servo control
7. Finally, try `/advanced/` examples for complete system demonstrations

## Troubleshooting

- **Import errors**: Make sure you're running from the project root directory
- **Hardware not found**: Check your hardware connections and permissions
- **Camera issues**: Ensure your camera is properly connected and accessible
- **Servo problems**: Verify servo wiring and power supply

## Contributing

When adding new examples:
- Follow the naming convention (descriptive names, no test/demo prefixes)
- Place in appropriate directory based on complexity
- Include proper docstrings and comments
- Ensure examples are self-contained and educational 