# RaspiBot - Product Requirements Document

## 1. Project Overview

### 1.1 Vision
A hobby development of simple robotics on a Raspberry Pi 5, progressing from basic pan/tilt camera control to autonomous movement capabilities.

### 1.2 Goals
- **Primary**: Pan, Tilt, and Roll head movement driven by face detection
- **Secondary**: Face recognition using OpenCV
- **Tertiary**: Directional audio detection (turn toward speaker)
- **Quaternary**: Voice to LLM integration with voice response
- **Long-term**: Wheeled base movement and autonomous navigation

### 1.3 Future Aspirations
- Experiment with models on the Raspberry Pi AI camera
- Autonomous movement using ultrasound and LIDAR sensors

## 2. Hardware Requirements

### 2.1 Phase 1 - Core Hardware (Current)
- Raspberry Pi 5 8GB
- Adafruit 16-Channel 12-bit PWM/Servo Driver - I2C interface (PCA9685)
- Adafruit mini Pan and Tilt kit with micro servos assembled (initial 2-axis)
- **Upgrade**: Pan/Tilt/Roll 3-axis servo mount (e.g., FatShark FSV1603 or similar ~£25)
- **Upgrade**: Robot head/enclosure compatible with 3-axis mount (to be sourced)
- Note: Future upgrade path to Stewart platform (6-DOF) for more expressive movement

### 2.2 Phase 2 - Vision Enhancement
- Raspberry Pi AI Camera or Pi Camera 3

### 2.3 Phase 3 - Audio Enhancement
- 2-6 microphone setup for directional audio detection
  - Start with 2 microphones for basic left/right detection
  - Expandable to 4-6 for more precise angular detection
- USB microphones or microphone array HAT (hardware to be chosen)
- Audio processing capabilities

### 2.4 Phase 4 - Voice Integration
- Speaker for text-to-speech output (hardware to be chosen)

### 2.5 Phase 5 - Emotion Display
- Small pixel-driven display (hardware to be chosen)
- Emotion expression capabilities

### 2.6 Phase 6 - Mobility
- WaveShare Robot-Chassis-MP
- Adafruit DC & Stepper Motor Bonnet for Raspberry Pi
- Accelerometer/IMU sensor (for movement and interaction)

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
- **CameraInterface** (`hardware/camera.py`): Camera abstraction
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
- [ ] **Upgrade to 3-axis pan/tilt/roll movement**
- [ ] Roll axis for expressive head tilts (e.g., "curious" gesture)
- [ ] Robot head enclosure integration
- [ ] Calibration for 3-axis system

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
- **3-axis servo coordination (pan, tilt, roll)**
- **Roll axis integration with existing PanTiltSystem → PanTiltRollSystem**
- **Head mounting compatibility and calibration**

### 4.2 Phase 2 - Face Recognition
**Features:**
- [ ] Face recognition (identify specific people)
- [ ] Face encoding storage and database
- [ ] Multiple face tracking and identification
- [ ] Identity-based greeting behaviors
- [ ] Unknown face handling
- [ ] Person following mode (track identified person)

**Technical Requirements:**
- Face encoding generation and storage
- face_recognition library or dlib integration
- Database for known faces (SQLite or file-based)
- Real-time recognition performance (>5 FPS with recognition)
- Enhanced camera resolution (Pi AI Camera/Pi Camera 3)

### 4.3 Phase 3 - Directional Audio
**Features:**
- [ ] Multi-microphone setup (2-6 microphones)
- [ ] Sound direction detection (identify direction of speaker)
- [ ] Background noise suppression (adaptive filtering)
- [ ] Turn head toward sound source (audio-first behavior)
- [ ] Visual confirmation after audio turn (look for face in that direction)
- [ ] Audio-visual coordination (correlate voice direction with detected face)
- [ ] Wake word detection with directional awareness

**Behavior:** When audio is detected from a direction:
1. Turn head toward sound source (even if no face visible)
2. Camera then searches for face in that direction
3. If face found, track it; if not, return to previous position or continue listening

**Technical Requirements:**
- Time Difference of Arrival (TDOA) or beamforming for direction
- Minimum 2 microphones for basic left/right detection
- 4-6 microphones for more precise angular detection
- Noise reduction algorithms (spectral subtraction or similar)
- Integration with pan/tilt/roll system for head turning
- Audio-face correlation for conversation tracking
- Timeout behavior when no face found after audio turn

### 4.4 Phase 4 - Voice and LLM Integration
**Features:**
- [ ] Speech-to-text processing
- [ ] LLM API integration (cloud-based initially)
- [ ] Text-to-speech response
- [ ] Conversational interaction
- [ ] Voice command recognition

**Technical Requirements:**
- STT API (Whisper, Google Speech, or similar)
- TTS API (pyttsx3, Google TTS, or ElevenLabs)
- LLM API integration (OpenAI, Anthropic, or local)
- Response latency <2 seconds

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

### 8.1 Milestone 1: Basic Infrastructure ✓
- [x] Project structure setup
- [x] Hardware configuration
- [x] Basic servo control (2-axis pan/tilt)
- [x] Anti-jitter measures
- [x] Calibration tools

### 8.2 Milestone 2: Face Detection & Tracking
- [ ] Camera interface (multi-camera support)
- [ ] OpenCV integration with YuNet
- [ ] Real-time face detection
- [ ] Pan/tilt tracking
- [ ] Sleep mode implementation
- [ ] Activity monitoring system

### 8.3 Milestone 3: 3-Axis Head Movement
- [ ] Upgrade to pan/tilt/roll hardware (FatShark or similar)
- [ ] PanTiltRollSystem implementation
- [ ] Roll axis calibration
- [ ] Expressive head tilts ("curious" gesture)
- [ ] Robot head enclosure integration

### 8.4 Milestone 4: Face Recognition
- [ ] Face encoding system
- [ ] Recognition database
- [ ] Identity-based behaviors
- [ ] Unknown face handling

### 8.5 Milestone 5: Directional Audio
- [ ] Multi-microphone setup (2-6 mics)
- [ ] Sound direction detection (TDOA/beamforming)
- [ ] Background noise suppression
- [ ] Audio-first head turning behavior
- [ ] Audio-visual coordination
- [ ] Wake word detection

### 8.6 Milestone 6: Voice & LLM Integration
- [ ] Speech-to-text implementation
- [ ] LLM API integration
- [ ] Text-to-speech output
- [ ] Voice command processing

### 8.7 Milestone 7: Emotion Display
- [ ] Display hardware setup
- [ ] Basic emotion expressions
- [ ] Emotion state integration
- [ ] Physical interaction detection (accelerometer)

## 9. Future Enhancements

### 9.1 Expressive Head Movement Upgrade
- Stewart platform (6-DOF) for highly expressive head movement
- Reachy Mini style motion capabilities
- Inverse kinematics for natural head positioning
- More nuanced emotional expressions through movement

### 9.2 Movement and Locomotion
- Wheeled base movement implementation
- Obstacle detection and avoidance
- Autonomous navigation capabilities
- Person following with movement
- Accelerometer-based movement feedback
- Balance and orientation detection

### 9.3 Advanced AI Features
- On-device model inference with Pi AI Camera
- Custom trained models for specific recognition tasks
- Edge AI optimization for real-time processing
- Object detection using existing YOLO11 model ?

### 9.4 Connectivity and Remote Control
- Web-based control interface

### 9.5 Backlog
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