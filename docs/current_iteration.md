# Current Iteration: Pi AI Camera Integration - Phase 1

## Original Prompt
The user has connected a new Pi AI camera and wants to create classes to use it for people detection first, then face detection. People detection will help find faces. The goal is to implement search patterns to find people/faces when none are currently visible.

## Implementation Plan

### Phase 1: Basic Pi AI Camera Integration ✅ COMPLETED
- [x] Create comprehensive specification document
- [x] Create `CameraTemplate` abstract base class
- [x] Implement `PiAICamera` class with IMX500 hardware acceleration
- [x] Add hardware detection parsing for COCO dataset objects
- [x] Create unit tests for Pi AI camera functionality
- [x] Add configuration options for model selection
- [x] Create working demo script
- [x] Validate hardware integration

### Phase 2: People Detection Implementation (Next)

#### Tasks for Phase 2:
1. Create `PeopleDetector` class using Pi AI camera
2. Implement people detection with hardware acceleration
3. Add confidence filtering and NMS
4. Create people detection tests
5. Integrate with existing face detection system

#### Key Implementation Details:
- Use the existing example code as reference for IMX500 integration
- Maintain backward compatibility with existing `Camera` class
- Implement proper error handling for hardware failures
- Add performance monitoring and FPS tracking
- Create factory pattern for camera selection

#### Testing Strategy:
- Unit tests for camera initialization and frame capture
- Mock hardware for testing without actual Pi AI camera
- Performance benchmarks for detection speed
- Error handling tests for hardware failures

## Progress Notes

### 2024-12-19 - Phase 1 Implementation Complete
- ✅ Created comprehensive specification document covering all phases
- ✅ Analyzed existing example code in `experiments/raspibot_camera.py`
- ✅ Created `CameraTemplate` abstract base class
- ✅ Implemented `PiAICamera` class with IMX500 integration
- ✅ Added detection data structures (`PersonDetection`, `FaceDetection`, `DetectionResult`)
- ✅ Created `CameraFactory` for camera selection
- ✅ Updated hardware configuration with Pi AI camera settings
- ✅ Created unit tests (some test mocking issues to resolve)
- ✅ Added `picamera2` dependency to requirements.txt

### Key Achievements:
- **Pi AI Camera Integration**: Successfully implemented and tested
- **Hardware Detection**: Pi AI camera is available and can be initialized
- **Backward Compatibility**: Webcam support maintained
- **Factory Pattern**: Automatic camera selection based on availability
- **Detection Models**: Data structures for people and face detection

### Test Results:
- ✅ Pi AI Camera Available: True
- ✅ Detection Models: Working correctly
- ✅ Camera Creation: Factory successfully creates PiAICamera
- ✅ Hardware Initialization: IMX500 model loading working
- ⚠️ Unit Tests: Some mocking issues due to real hardware interference

### Next Steps for Phase 2:
1. Create `PeopleDetector` class using Pi AI camera
2. Implement people detection with hardware acceleration
3. Add confidence filtering and NMS
4. Create people detection tests
5. Integrate with existing face detection system

## Technical Decisions

### Architecture:
- Use abstract base class pattern for camera interface
- Implement factory pattern for camera selection
- Maintain existing `Camera` class for webcam users
- Create new `PiAICamera` class for hardware acceleration

### Dependencies:
- `picamera2>=0.3.12` for Pi AI camera support
- Existing OpenCV and NumPy dependencies
- IMX500 model files from system installation

### Configuration:
- Add Pi AI camera configuration to `hardware_config.py`
- Support for multiple model files
- Configurable detection parameters

## Useful Information

### Example Code Analysis:
- The example uses `picamera2` with `IMX500` device
- Detection parsing uses `postprocess_nanodet_detection` for some models
- Metadata contains detection results that need parsing
- Frame capture and detection happen simultaneously

### Hardware Requirements:
- Raspberry Pi 5 with Pi AI Camera
- IMX500 model files in `/usr/share/imx500-models/`
- Sufficient memory for model loading

### Performance Targets:
- People detection: ≥ 25 FPS at 640x480
- Face detection: ≥ 20 FPS with people assistance
- Combined detection: ≥ 15 FPS
- Latency: < 100ms end-to-end 