# Raspibot

A hobby development of simple robotics on a Raspberry Pi 5, progressing from basic pan/tilt camera control to autonomous movement capabilities.

## 🎯 Development Progress

### ✅ Completed Features
- [x] **Servo Control System** - Unified PCA9685 and GPIO servo controllers with asyncio support
- [x] **Camera System** - Universal camera interface auto-detecting Pi AI, Pi Camera, or USB cameras
- [x] **Room Scanning System** - Systematic room scanning with servo movement coordination
- [x] **Object Detection** - Real-time object detection with hardware AI acceleration (Pi AI Camera)
- [x] **Object Deduplication** - Advanced deduplication with spatial, temporal, and overlap algorithms
- [x] **Configuration Management** - Environment-based configuration with servo calibration
- [x] **Logging Infrastructure** - Structured logging with correlation IDs and async support
- [x] **Testing Framework** - Comprehensive unit and integration tests
- [x] **Hardware Abstraction** - Modular design supporting multiple hardware configurations

### 🚧 Planned (Not Yet Implemented)
- [ ] **Face Detection & Tracking** - Real-time face detection with camera centering
- [ ] **Face Recognition** - Person identification using face encodings
- [ ] **Pan/Tilt Tracking** - Automatic camera tracking of detected objects/faces
- [ ] **Audio Enhancement** - Directional microphone array and wake word detection
- [ ] **Voice Integration** - Speech-to-text, LLM integration, and voice response
- [ ] **Mobility** - Wheeled base movement and autonomous navigation
- [ ] **Emotion Display** - LED/screen expressions and interaction detection
- [ ] **Advanced AI** - Custom models and gesture recognition

## 🎯 Project Aims

* **Primary**: Pan and Tilt camera driven by face detection 🚧
* **Secondary**: Face recognition using OpenCV 📋
* **Tertiary**: Voice to LLM integration with voice response 📋
* **Long-term**: Wheeled base movement and autonomous navigation 📋

## 🔧 Current Capabilities

* **Multi-Camera Support**: Automatically detects and uses Pi AI Camera, Pi Camera, or USB cameras
* **Servo Control**: PCA9685 and GPIO servo controllers with smooth movement and jitter handling
* **Room Scanning**: Systematic 360° scanning with intelligent position calculation
* **Object Detection**: Real-time detection using hardware acceleration when available
* **Smart Deduplication**: Eliminates duplicate detections using spatial, temporal, and overlap analysis
* **Asyncio Support**: Full async/await support for smooth concurrent operations

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 5 8GB
- **Option 1**: Adafruit 16-Channel PWM/Servo Driver (PCA9685) + I2C connection
- **Option 2**: Direct GPIO servo control
- 2x Servos for pan/tilt (e.g., Adafruit mini Pan and Tilt kit)
- Camera: Pi AI Camera, Pi Camera, or USB webcam

### Installation
```bash
# Install for development
pip install -e ".[dev]"

# Run basic room scan demo
python -m raspibot.core.room_scan

# Run main application
python -m raspibot.main
# or
raspibot
```

### Development Commands
```bash
# Testing
python -m pytest tests/ -v

# Formatting  
black --line-length 119 .
isort .

# Type checking
mypy raspibot/
```

## 📁 Project Structure

```
raspibot/
├── raspibot/                    # Main package
│   ├── hardware/                # Hardware abstraction layer
│   │   ├── cameras/             # Universal camera support (Pi AI, Pi, USB)
│   │   └── servos/              # Servo controllers (PCA9685, GPIO)
│   ├── vision/                  # Computer vision modules
│   │   ├── deduplication.py     # Object deduplication algorithms
│   │   └── search_pattern.py    # Search pattern utilities
│   ├── movement/                # Movement and scanning
│   │   └── scanner.py           # Room scanning patterns
│   ├── core/                    # Core application logic
│   │   └── room_scan.py         # Room scanning coordinator
│   ├── settings/                # Configuration management
│   │   └── config.py            # Hardware and app configuration
│   └── utils/                   # Utility functions
│       ├── logging_config.py    # Structured logging with correlation IDs
│       └── helpers.py           # Common utilities
├── examples/                    # Educational examples and demos
├── experiments/                 # Development experiments
├── tests/                       # Comprehensive test suite
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
└── docs/                        # Documentation and specifications
    └── specs/                   # Technical specifications
```

## 🔧 Hardware Requirements

### Current Implementation ✅
* **Raspberry Pi 5** 8GB (required)
* **Servo Control** (choose one):
  - Adafruit 16-Channel PWM/Servo Driver (PCA9685) + I2C
  - Direct GPIO servo control
* **Pan/Tilt Mount**: 2x servos (e.g., Adafruit mini Pan and Tilt kit)
* **Camera** (auto-detected):
  - Raspberry Pi AI Camera (preferred for hardware acceleration)
  - Pi Camera 3 or earlier
  - USB webcam

### Future Phases 📋
* **Audio**: Multi-microphone array for directional detection
* **Mobility**: WaveShare Robot-Chassis-MP + motor controller
* **Display**: LED matrix or small screen for emotion display
* **Sensors**: Ultrasonic, LIDAR for autonomous navigation

## 📚 Documentation

- [Development Guidelines](CLAUDE.md) - Coding standards and development workflow
- [Project History](.history.md) - Development decisions and lessons learned
- [Examples Guide](examples/README.md) - Learn how to use the project
- [Hardware Setup](docs/how_to/) - Hardware configuration guides
- [Technical Specifications](docs/specs/) - Detailed technical documentation

## 🔄 Key Features

### Camera System
- **Universal Interface**: Single Camera class auto-detects hardware
- **Hardware Acceleration**: Pi AI Camera provides real-time object detection
- **Fallback Support**: Gracefully degrades to software detection for other cameras
- **Threading**: Non-blocking detection processing

### Servo Control
- **Dual Controllers**: Supports both PCA9685 and GPIO servo control
- **Jitter Handling**: Automatic avoidance of problematic servo angles
- **Smooth Movement**: Asyncio-based smooth servo transitions
- **Calibration**: Built-in calibration support for servo offset correction

### Room Scanning
- **Intelligent Patterns**: FOV-based position calculation for complete coverage
- **Object Tracking**: Correlates detections with precise servo angles
- **Deduplication**: Advanced algorithms eliminate duplicate detections
- **Async Support**: Full async/await support for smooth operation


