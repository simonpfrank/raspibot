# RaspiBot - Product Requirements Document

## 1. Project Overview

### 1.1 Vision
A hobby development of simple robotics on a Raspberry Pi 5, progressing from basic pan/tilt camera control to autonomous movement capabilities.

### 1.2 Goals
- **Primary**: Pan and Tilt camera driven by face detection
- **Secondary**: Face recognition using OpenCV
- **Tertiary**: Voice to LLM integration with voice response
- **Long-term**: Wheeled base movement and autonomous navigation

### 1.3 Future Aspirations
- Experiment with models on the Raspberry Pi AI camera
- Autonomous movement using ultrasound and LIDAR sensors

## 2. Hardware Requirements

### 2.1 Phase 1 - Start (Current)
- Raspberry Pi 5 8GB
- Adafruit 16-Channel 12-bit PWM/Servo Driver - I2C interface (PCA9685)
- Adafruit mini Pan and Tilt kit with micro servos assembled

### 2.3 Phase 2 - Vision Enhancement
- Raspberry Pi AI Camera or Pi Camera 3

### 2.2 Phase 3 - Audio Enhancement
- 4-8 microphone array hat for Raspberry Pi (hardware to be chosen)
- Audio processing capabilities

### 2.4 Phase 4 - Mobility
- WaveShare Robot-Chassis-MP
- Adafruit DC & Stepper Motor Bonnet for Raspberry Pi
- Accelerometer/IMU sensor (for movement and interaction)

### 2.5 Phase 5 - Emotion Display
- Small pixel-driven display (hardware to be chosen)
- Emotion expression capabilities

## 3. Software Architecture

### 3.1 Directory Structure

```
raspibot/
├── raspibot/                    # Main package
│   ├── __init__.py
│   ├── main.py                  # Main application entry point
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py          # App settings and constants
│   │   └── hardware_config.py   # Hardware pin mappings, I2C addresses
│   ├── hardware/                # Hardware abstraction layer
│   │   ├── __init__.py
│   │   ├── servo_controller.py  # PCA9685 servo control
│   │   ├── camera.py            # Camera interface
│   │   ├── motors.py            # DC motor control (Phase 2)
│   │   ├── sensors.py           # Ultrasound, LIDAR sensors (Phase 3)
│   │   └── imu.py               # Accelerometer/IMU interface
│   ├── vision/                  # Computer vision modules
│   │   ├── __init__.py
│   │   ├── face_detection.py    # OpenCV face detection
│   │   ├── face_recognition.py  # Face recognition logic
│   │   └── tracking.py          # Object tracking for pan/tilt
│   ├── audio/                   # Audio processing
│   │   ├── __init__.py
│   │   ├── microphone_array.py  # Multi-mic array interface
│   │   ├── direction_finder.py  # Sound direction detection
│   │   ├── noise_reduction.py   # Background noise filtering
│   │   └── wake_word.py         # Wake word detection
│   ├── voice/                   # Voice processing
│   │   ├── __init__.py
│   │   ├── speech_to_text.py    # STT implementation
│   │   ├── text_to_speech.py    # TTS implementation
│   │   └── llm_interface.py     # LLM integration
│   ├── movement/                # Movement and navigation
│   │   ├── __init__.py
│   │   ├── pan_tilt.py          # Pan/tilt camera control
│   │   ├── locomotion.py        # Wheeled base movement (Phase 2)
│   │   └── navigation.py        # Autonomous navigation (Phase 3)
│   ├── core/                    # Core application logic
│   │   ├── __init__.py
│   │   ├── robot.py             # Main robot class
│   │   ├── state_machine.py     # Robot behavior state management
│   │   └── coordinator.py       # Coordinate between subsystems
│   ├── display/                 # Display and emotion system
│   │   ├── __init__.py
│   │   ├── emotion_display.py   # Pixel display interface
│   │   ├── text_display.py      # Text display interface
│   │   ├── emotion_engine.py    # Emotion state management
│   │   └── expressions.py       # Predefined emotion patterns
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── logging_config.py    # Logging setup
│       ├── calibration.py       # Servo/camera calibration tools
│       └── helpers.py           # Common utility functions
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_hardware/
│   ├── test_vision/
│   ├── test_voice/
│   └── test_movement/
├── scripts/                     # Standalone scripts
│   ├── calibrate_servos.py      # Hardware calibration
│   ├── test_camera.py           # Camera testing
│   └── setup_hardware.py       # Initial hardware setup
├── data/                        # Data storage
│   ├── models/                  # ML models, face encodings
│   ├── logs/                    # Application logs
│   └── calibration/             # Calibration data
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
└── .env.example                 # Environment variables template
```

### 3.2 Core Classes and Components

#### 3.2.1 Main Robot Controller
- **RaspiBot** (`core/robot.py`): Central robot coordinator
- **StateMachine** (`core/state_machine.py`): Behavior state management
- **SystemCoordinator** (`core/coordinator.py`): Inter-subsystem communication

#### 3.2.2 Hardware Layer
- **ServoController** (`hardware/servo_controller.py`): PCA9685 interface
- **CameraTemplate** (`hardware/camera.py`): Camera abstraction
- **MotorController** (`hardware/motors.py`): DC motor control
- **SensorInterface** (`hardware/sensors.py`): Sensor data collection
- **DisplayInterface** (`hardware/display.py`): Display hardware abstraction
- **IMUInterface** (`hardware/imu.py`): Accelerometer/IMU interface

#### 3.2.3 Vision System
- **FaceDetector** (`vision/face_detection.py`): OpenCV-based detection
- **FaceRecognizer** (`vision/face_recognition.py`): Recognition logic
- **ObjectTracker** (`vision/tracking.py`): Object tracking for camera control

#### 3.2.4 Audio Processing
- **MicrophoneArray** (`audio/microphone_array.py`): Multi-mic array interface
- **DirectionFinder** (`audio/direction_finder.py`): Sound direction detection
- **NoiseReducer** (`audio/noise_reduction.py`): Background noise filtering
- **WakeWordDetector** (`audio/wake_word.py`): Wake word detection

#### 3.2.5 Voice Processing
- **SpeechToText** (`voice/speech_to_text.py`): Voice input processing
- **TextToSpeech** (`voice/text_to_speech.py`): Voice output generation
- **LLMInterface** (`voice/llm_interface.py`): LLM integration

#### 3.2.6 Movement Control
- **PanTiltController** (`movement/pan_tilt.py`): Camera positioning
- **LocomotionController** (`movement/locomotion.py`): Base movement
- **NavigationSystem** (`movement/navigation.py`): Path planning

#### 3.2.7 Display System
- **EmotionDisplay** (`display/emotion_display.py`): Pixel display interface
- **TextDisplay** (`display/text_display.py`): Text display interface
- **EmotionEngine** (`display/emotion_engine.py`): Emotion state management
- **ExpressionManager** (`display/expressions.py`): Predefined emotion patterns

## 4. Feature Requirements by Phase

### 4.1 Phase 1 - Core Hardware & Basic Interaction
**Completed Features:**
- [x] Servo control via PCA9685 and GPIO
- [x] Basic camera pan/tilt movement with coordinate system
- [x] Hardware abstraction layer for servo controllers
- [x] Anti-jitter measures and smooth movement
- [x] Calibration tools for servo positions
- [x] Comprehensive testing (76% coverage)

**Remaining Features:**
- [ ] Face detection using OpenCV
- [ ] Automatic face tracking with camera
- [ ] Multi-camera support (webcam, PiCamera, AI camera)
- [ ] Face collection handling (multiple faces)
- [ ] Sleep mode (tilt down, pan center) with dramatic movement sequence
- [ ] Activity monitoring for sleep triggers
- [ ] Manual control interface (backlog)

**Technical Requirements:**
- I2C communication with PCA9685
- GPIO servo control with RPi.GPIO
- Real-time face detection (>10 FPS)
- Smooth servo movement (no jitter)
- Configurable servo limits and speeds
- Multi-camera abstraction layer
- Coordinate system translation for servo movement
- Sleep mode with camera processing disabled
- Activity monitoring with face detection
- Audio wake word detection during sleep

### 4.2 Phase 2 - Enhanced Vision and Voice
**Features:**
- [ ] Face recognition (identify specific people)
- [ ] Voice-to-LLM integration
- [ ] Voice response system
- [ ] Improved camera quality (Pi AI Camera/Pi Camera 3)
- [ ] Multiple face tracking
- [ ] Person following mode

**Technical Requirements:**
- Face encoding storage and retrieval
- Real-time speech processing
- LLM API integration (local or cloud)
- Text-to-speech output
- Enhanced camera resolution and AI capabilities

### 4.2 Phase 2 - Enhanced Vision and Voice
**Features:**
- [ ] Face recognition (identify specific people)
- [ ] Voice-to-LLM integration
- [ ] Voice response system
- [ ] Improved camera quality (Pi AI Camera/Pi Camera 3)
- [ ] Multiple face tracking
- [ ] Person following mode

**Technical Requirements:**
- Face encoding storage and retrieval
- Real-time speech processing
- LLM API integration (local or cloud)
- Text-to-speech output
- Enhanced camera resolution and AI capabilities


### 4.2 Phase 2 - Enhanced Vision
**Features:**
- [ ] Face recognition (identify specific people)
- [ ] Voice-to-LLM integration
- [ ] Voice response system
- [ ] Improved camera quality (Pi AI Camera/Pi Camera 3)
- [ ] Multiple face tracking
- [ ] Person following mode

**Technical Requirements:**
- Face encoding storage and retrieval
- Enhanced camera resolution and AI capabilities

### 4.3 Phase 3 - Audio Enhancement
**Features:**
- [ ] Directional microphone array setup
- [ ] Sound direction detection (identify direction of noises)
- [ ] Background noise reduction (lower gain on continual noise sources)
- [ ] Wake word detection
- [ ] Wake word direction with camera focus on that face
- [ ] Temporary face-conversation association (until conversation ends)

**Technical Requirements:**
- Multi-microphone array processing
- Real-time audio direction finding
- Adaptive noise reduction algorithms
- Wake word detection with direction
- Face-audio correlation system
- Audio-visual coordination

#### 4.3.5 LLM Enhancement
- [ ] Real-time speech processing (optional)
- [ ] LLM API integration (local or cloud)
- [ ] Text-to-speech output

**Technical Requirements:**
- Real time speech processing (optional)
- speech to text/text to speech API
- Simple LLM integration

### 4.5 Phase 5 - Emotion Display
**Features:**
- [ ] Basic emotion display setup
- [ ] Simple emotion expressions (happy, sad, neutral, curious)
- [ ] Emotion triggers based on robot state
- [ ] Display integration with face detection
- [ ] Physical interaction detection (pat on head)
- [ ] Dizziness display when patted

**Technical Requirements:**
- Pixel display hardware interface
- Emotion state management system
- Real-time display updates
- Integration with robot behavior states
- Accelerometer-based interaction detection
- Motion pattern recognition for "patting"

### 4.6 Phase 6 - Mobility and Autonomy
**Features:**
- [ ] Wheeled base movement
- [ ] Obstacle detection and avoidance
- [ ] Autonomous navigation
- [ ] Person following with movement
- [ ] Voice-controlled movement commands
- [ ] LIDAR integration for mapping

**Technical Requirements:**
- DC motor control for wheeled chassis
- Ultrasonic sensor integration
- LIDAR data processing
- Path planning algorithms
- Safety systems for autonomous movement
- Real-time obstacle avoidance

## 5. Technical Specifications

### 5.1 Performance Requirements
- **Face Detection**: ≥10 FPS at 640x480 resolution
- **Servo Response**: <100ms from detection to movement
- **Voice Processing**: <2s response time for voice commands


### 5.2 Software Dependencies
- **Core**: Python 3.9+, asyncio for concurrent operations
- **Vision**: OpenCV, face_recognition, NumPy
- **Hardware**: RPi.GPIO, adafruit-circuitpython-pca9685
- **Audio**: pyaudio, numpy, scipy (for audio processing)
- **Voice**: SpeechRecognition, pyttsx3, openai/transformers
- **Utilities**: logging, configparser, pytest
- Others to be chosen e.g. for wake word detection

### 5.3 Configuration Management
- Environment-based configuration files (YAML)
- Hardware pin mapping configuration
- Calibration data persistence (if necessary)
- User preference storage (YAML)

## 6. Safety and Constraints

### 6.1 Safety Requirements
- Servo position limits to prevent mechanical damage
- Emergency stop functionality
- Safe movement speeds for Phase 3
- Obstacle detection before movement

### 6.2 System Constraints
- Raspberry Pi 5 computational limits
- I2C bus bandwidth limitations
- Power consumption considerations
- Real-time processing requirements

## 7. Testing Strategy

### 7.1 Unit Testing
- Hardware interface mocking
- Vision algorithm testing with static images
- Configuration loading tests

### 7.2 Integration Testing
- Servo movement validation
- End-to-end face tracking scenarios
- Hardware calibration verification
- Multi-subsystem coordination tests
- Performance benchmarking

### 7.3 Hardware Testing
- Servo calibration and range testing
- Camera quality and positioning tests
- I2C communication reliability


## 8. Development Milestones

### 8.1 Milestone 1: Basic Infrastructure (Week 1-2)
- [ ] Project structure setup
- [ ] Hardware configuration
- [ ] Basic servo control
- [ ] Sleep mode implementation
- [ ] Activity monitoring system


### 8.2 Milestone 2: Face Detection (Week 3-4)
- [ ] Camera interface
- [ ] OpenCV integration
- [ ] Real-time face detection
- [ ] Pan/tilt tracking
- [ ] Calibration tools
- [ ] Sleep mode with camera disabled, audio active
- [ ] Wake word detection during sleep

### 8.3 Milestone 3: Audio Enhancement (Week 5-6)
- [ ] Microphone array setup and testing
- [ ] Sound direction detection
- [ ] Wake word detection
- [ ] Audio-visual coordination

### 8.4 Milestone 4: Face Recognition (Week 7-8)
- [ ] Face encoding system
- [ ] Recognition database
- [ ] Identity-based behaviors

### 8.5 Milestone 5: Emotion Display (Week 9-10)
- [ ] Display hardware setup
- [ ] Basic emotion expressions
- [ ] Emotion state integration
- [ ] Enhanced emotion patterns
- [ ] Accelerometer integration
- [ ] Physical interaction detection

### 8.6 Milestone 6: Voice Integration (Week 11-12)
- [ ] Speech-to-text implementation
- [ ] LLM integration
- [ ] Text-to-speech output
- [ ] Voice command processing

## 9. Future Enhancements

### 9.1 Movement and Locomotion
- Wheeled base movement implementation
- Obstacle detection and avoidance
- Autonomous navigation capabilities
- Person following with movement
- Accelerometer-based movement feedback
- Balance and orientation detection

### 9.2 Advanced AI Features
- On-device model inference with Pi AI Camera
- Custom trained models for specific recognition tasks
- Edge AI optimization for real-time processing
- Object detection using existing YOLO11 model ?

### 9.3 Connectivity and Remote Control
- Web-based control interface

### 9.4 Backlog
- Mobile app integration
- Remote monitoring capabilities
- Cloud data synchronization

#### 9.4.1 Advanced Navigation
- SLAM (Simultaneous Localization and Mapping)
- Multi-room navigation
- Dynamic obstacle avoidance
- Collaborative robot behaviors 

#### 9.4.2 Gesture & Body Language Recognition
- Hand gesture commands: Wave hello, thumbs up, pointing
- Body language interpretation: Detect slouching, excitement, fatigue
- Interactive gestures: High-fives, handshakes with servo response
- Possible gesturing with fake arms

#### 9.4.3 Behavioral & Personality Features
- Curiosity responses: Following interesting sounds or movements
- "Boredom" behaviors: Idle animations when not engaged
- Personality evolution: Robot's personality changes based on interactions

#### 9.4.4 Advanced Learning & Memory
- Conversation threading: Remember and continue previous conversations
- Preference learning: Learn favorite topics, jokes, music styles
- Relationship mapping: Understand family/friend relationships

#### 9.4.5 Enhanced Vision Capabilities
- Object recognition: Identify and comment on objects in view

#### 9.4.6 AI Infrastructure
- Possible use of local models using additional Processor Hat

#### 9.4.7 Local LLM
- possible local small llm with AI Hat.