# Pi AI Camera Integration Specification

## Overview

This specification defines the integration of the Raspberry Pi AI Camera (IMX500) into the Raspibot vision system. The Pi AI camera provides hardware-accelerated AI inference capabilities, enabling real-time people and face detection with superior performance compared to software-based solutions.

## Key Objectives

1. **People Detection Priority**: Use the Pi AI camera's hardware acceleration to detect people first, which helps locate potential faces
2. **Face Detection Enhancement**: Leverage people detection results to focus face detection efforts
3. **Search Pattern Implementation**: Implement intelligent search patterns to find people/faces when none are currently visible
4. **Backward Compatibility**: Maintain support for regular webcams for users without Pi AI camera
5. **Performance Optimization**: Achieve real-time detection at 30+ FPS

## Architecture

### Camera Abstraction Layer

```python
class CameraTemplate(ABC):
    """Abstract base class for camera implementations."""
    
    @abstractmethod
    def start(self) -> bool:
        """Start camera capture."""
        pass
    
    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """Get a single frame."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop camera capture."""
        pass
    
    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """Get current resolution."""
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        """Get current FPS."""
        pass
```

### Pi AI Camera Implementation

```python
class PiAICamera(CameraTemplate):
    """Pi AI Camera implementation using IMX500 hardware acceleration."""
    
    def __init__(self, 
                 model_path: str = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk",
                 confidence_threshold: float = 0.55,
                 iou_threshold: float = 0.65,
                 max_detections: int = 10,
                 inference_rate: int = 30):
        """
        Initialize Pi AI camera.
        
        Args:
            model_path: Path to the IMX500 model file
            confidence_threshold: Detection confidence threshold
            iou_threshold: IoU threshold for NMS
            max_detections: Maximum number of detections
            inference_rate: Target inference FPS
        """
```

### Detection Classes

#### People Detector

```python
class PeopleDetector:
    """Hardware-accelerated people detection using Pi AI camera."""
    
    def __init__(self, camera: PiAICamera):
        """Initialize people detector with Pi AI camera."""
    
    def detect_people(self, frame: np.ndarray) -> List[PersonDetection]:
        """Detect people in frame using hardware acceleration."""
    
    def get_people_centers(self, detections: List[PersonDetection]) -> List[Tuple[int, int]]:
        """Get center points of detected people."""
    
    def filter_by_confidence(self, detections: List[PersonDetection], 
                           min_confidence: float = 0.6) -> List[PersonDetection]:
        """Filter detections by confidence threshold."""
```

#### Enhanced Face Detector

```python
class PiAIFaceDetector(FaceDetector):
    """Enhanced face detector using Pi AI camera with people detection assistance."""
    
    def __init__(self, camera: PiAICamera, people_detector: PeopleDetector):
        """Initialize enhanced face detector."""
    
    def detect_faces_with_people_assist(self, frame: np.ndarray) -> List[FaceDetection]:
        """Detect faces using people detection to guide search areas."""
    
    def detect_faces_in_people_regions(self, frame: np.ndarray, 
                                     people: List[PersonDetection]) -> List[FaceDetection]:
        """Detect faces specifically in regions where people are detected."""
```

### Search Pattern System

```python
class SearchPattern:
    """Intelligent search pattern for finding people/faces."""
    
    def __init__(self, pan_tilt: PanTiltSystem, camera: CameraTemplate):
        """Initialize search pattern system."""
    
    def spiral_search(self, center_pan: float = 0.0, center_tilt: float = 0.0, 
                     radius: float = 0.3, steps: int = 20) -> Generator[Tuple[float, float], None, None]:
        """Generate spiral search pattern coordinates."""
    
    def grid_search(self, pan_range: Tuple[float, float] = (-0.4, 0.4),
                   tilt_range: Tuple[float, float] = (-0.3, 0.3),
                   pan_steps: int = 8, tilt_steps: int = 6) -> Generator[Tuple[float, float], None, None]:
        """Generate grid search pattern coordinates."""
    
    def adaptive_search(self, last_detection_position: Optional[Tuple[float, float]] = None,
                       search_radius: float = 0.2) -> Generator[Tuple[float, float], None, None]:
        """Generate adaptive search pattern based on last detection."""
```

### Detection Data Structures

```python
@dataclass
class PersonDetection:
    """Person detection result."""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    category: str = "person"
    center: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.center is None:
            x, y, w, h = self.bbox
            self.center = (x + w // 2, y + h // 2)

@dataclass
class FaceDetection:
    """Face detection result with additional metadata."""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    landmarks: Optional[List[Tuple[int, int]]] = None
    person_association: Optional[PersonDetection] = None
    center: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.center is None:
            x, y, w, h = self.bbox
            self.center = (x + w // 2, y + h // 2)
```

## Implementation Phases

### Phase 1: Basic Pi AI Camera Integration
- [ ] Create `PiAICamera` class implementing `CameraTemplate`
- [ ] Implement basic frame capture and metadata extraction
- [ ] Add hardware detection parsing for COCO dataset objects
- [ ] Create unit tests for Pi AI camera functionality
- [ ] Add configuration options for model selection

### Phase 2: People Detection Implementation
- [ ] Create `PeopleDetector` class
- [ ] Implement people detection using IMX500 hardware
- [ ] Add confidence filtering and NMS
- [ ] Create detection result data structures
- [ ] Add people detection tests

### Phase 3: Enhanced Face Detection
- [ ] Extend `FaceDetector` to work with Pi AI camera
- [ ] Implement people-assisted face detection
- [ ] Add face detection within people regions
- [ ] Optimize detection parameters for real-time performance
- [ ] Create integration tests

### Phase 4: Search Pattern System
- [ ] Implement `SearchPattern` class
- [ ] Add spiral, grid, and adaptive search patterns
- [ ] Create search pattern coordination with pan/tilt system
- [ ] Add search pattern tests
- [ ] Implement search state management

### Phase 5: Integration and Optimization
- [ ] Integrate all components into main robot system
- [ ] Optimize performance and memory usage
- [ ] Add fallback to software detection when needed
- [ ] Create comprehensive integration tests
- [ ] Add performance benchmarks

## Configuration

### Hardware Configuration

```python
# raspibot/config/hardware_config.py additions

# Pi AI Camera Configuration
PI_AI_CAMERA_CONFIG = {
    "default_model": "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk",
    "people_detection": {
        "confidence_threshold": 0.55,
        "iou_threshold": 0.65,
        "max_detections": 10,
        "inference_rate": 30
    },
    "face_detection": {
        "confidence_threshold": 0.6,
        "iou_threshold": 0.3,
        "max_detections": 5
    }
}

# Search Pattern Configuration
SEARCH_PATTERN_CONFIG = {
    "spiral_search": {
        "default_radius": 0.3,
        "default_steps": 20,
        "step_delay": 0.5
    },
    "grid_search": {
        "pan_range": (-0.4, 0.4),
        "tilt_range": (-0.3, 0.3),
        "pan_steps": 8,
        "tilt_steps": 6,
        "step_delay": 0.3
    },
    "adaptive_search": {
        "search_radius": 0.2,
        "max_search_time": 10.0
    }
}
```

## Performance Requirements

### Detection Performance
- **People Detection**: ≥ 25 FPS at 640x480 resolution
- **Face Detection**: ≥ 20 FPS with people assistance
- **Combined Detection**: ≥ 15 FPS for both people and faces
- **Latency**: < 100ms end-to-end detection time

### Search Pattern Performance
- **Spiral Search**: Complete 360° search in < 30 seconds
- **Grid Search**: Complete full range search in < 45 seconds
- **Adaptive Search**: Respond to new detections within 2 seconds

### Memory Usage
- **Peak Memory**: < 512MB for detection pipeline
- **Model Loading**: < 100MB additional memory
- **Detection Results**: < 10MB for result storage

## Error Handling

### Hardware Failures
- Graceful fallback to software detection when Pi AI camera unavailable
- Automatic retry mechanisms for hardware initialization
- Clear error messages for hardware-specific issues

### Model Failures
- Fallback to default models when custom models fail to load
- Validation of model compatibility before initialization
- Graceful degradation when detection fails

### Performance Degradation
- Automatic adjustment of detection parameters based on performance
- Dynamic FPS adjustment to maintain real-time operation
- Memory usage monitoring and cleanup

## Testing Strategy

### Unit Tests
- Pi AI camera initialization and frame capture
- People detection accuracy and performance
- Face detection with people assistance
- Search pattern generation and execution

### Integration Tests
- Full detection pipeline performance
- Pan/tilt system coordination
- Memory usage and cleanup
- Error handling and recovery

### Hardware Tests
- Real-world detection accuracy
- Performance under various lighting conditions
- Search pattern effectiveness
- System stability over extended periods

## Dependencies

### Required Packages
```python
# requirements.txt additions
picamera2>=0.3.12
numpy>=1.24.0
opencv-python>=4.8.0
```

### System Requirements
- Raspberry Pi 5 with Pi AI Camera
- IMX500 model files installed in `/usr/share/imx500-models/`
- Sufficient memory for model loading and inference
- Real-time kernel recommended for optimal performance

## Migration Strategy

### Backward Compatibility
- Maintain existing `Camera` class for webcam users
- Factory pattern for camera selection based on hardware availability
- Graceful fallback when Pi AI camera not available

### Configuration Migration
- Automatic detection of Pi AI camera availability
- Configuration file updates for new camera options
- Preserve existing webcam settings

### Testing Migration
- Update existing tests to work with both camera types
- Add hardware-specific test markers
- Maintain test coverage for both implementations

## Future Enhancements

### Advanced Features
- Multi-person tracking across frames
- Person re-identification
- Emotion detection on detected faces
- Gesture recognition
- Activity recognition

### Performance Optimizations
- Model quantization for faster inference
- Batch processing for multiple detections
- GPU acceleration when available
- Adaptive resolution based on detection needs

### Integration Enhancements
- Integration with voice commands for search control
- Machine learning-based search pattern optimization
- Integration with navigation system for autonomous search
- Cloud-based model updates and improvements 