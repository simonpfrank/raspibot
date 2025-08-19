# Face Detection Integration Plan

## Overview
This document details the complete integration plan for adding face detection functionality to the pyraspibot framework. The integration will enhance room scanning with face detection on person objects, provide visual feedback through display annotations, and calculate optimal camera angles to cover the most detected faces.

## Current System Analysis

### Existing Components
1. **Face Detection Module** (`raspibot/vision/face_detection.py`)
   - `FaceDetector` class with Haar cascade and ONNX model support
   - Methods: `detect_faces()`, `detect_faces_in_region()`
   - Returns face dictionaries with 'box' and 'confidence' keys
   - Full frame and region-based detection capabilities

2. **Room Scanner** (`raspibot/core/room_scan.py`)
   - `RoomScanner` class coordinates camera detection with servo movement
   - Already has `face_detection` parameter (currently unused)
   - Processes person detections at each scan position
   - Uses `ObjectDeduplicator` for duplicate removal

3. **Camera System** (`raspibot/hardware/cameras/camera.py`)
   - `Camera` class with AI detection capabilities
   - Has `annotate_screen()` method for drawing on display
   - Tracks objects in `tracked_objects` list
   - Uses green bounding boxes for object detection

4. **Object Deduplication** (`raspibot/vision/deduplication.py`)
   - `ObjectDeduplicator` handles duplicate removal across positions
   - Already supports temporal smoothing and spatial similarity
   - Can be extended to handle face data

## Integration Requirements

### 1. Face Detection on Person Objects
- When room scan is performed, detect faces within person bounding boxes
- Cache confirmed people (objects with detected faces)
- Store face detection results alongside object detection data

### 2. Visual Display Enhancement
- Draw white bounding boxes for detected faces
- Show face center points
- Maintain existing green boxes for general object detection

### 3. Optimal Camera Positioning
- Calculate best camera angle to cover the most detected faces
- Move to optimal position after room scan completion

## Detailed Implementation Plan

### Phase 1: Core Face Detection Integration

#### 1.1 Extend RoomScanner Class
**File**: `raspibot/core/room_scan.py`

**Changes Required**:
```python
# Add face detector initialization
def __init__(self, ...):
    # Existing initialization...
    if self.face_detection:
        from raspibot.vision.face_detection import FaceDetector
        self.face_detector = FaceDetector(confidence_threshold=0.6)
    else:
        self.face_detector = None
    
    # Add face tracking storage
    self.detected_faces = []  # Store all face detections
    self.confirmed_people = []  # People objects with detected faces
```

**New Methods to Add**:
```python
def _detect_faces_in_persons(self, detections: List[Dict], frame: np.ndarray) -> List[Dict]:
    """Detect faces within person bounding boxes and return face data."""
    
def _calculate_optimal_face_angle(self) -> float:
    """Calculate camera angle that covers the most detected faces."""
    
def move_to_optimal_face_position(self) -> None:
    """Move camera to optimal position for face coverage."""
```

#### 1.2 Modify Detection Capture Process
**File**: `raspibot/core/room_scan.py`

**Method**: `_capture_detections_at_position()` and `_capture_detections_at_position_async()`

**Changes**:
- Add face detection when `self.face_detection` is enabled
- Only perform face detection on "person" labeled objects
- Store face detection results in detection dictionaries
- Add face data to confirmed_people list

#### 1.3 Extend ObjectDeduplicator for Face Data
**File**: `raspibot/vision/deduplication.py`

**For now don't perform dedpuplication on face detection**

### Phase 2: Visual Display Integration

#### 2.1 Extend Camera Annotation System
**File**: `raspibot/hardware/cameras/camera.py`

**New Methods to Add**:
```python
def draw_faces(self, m: MappedArray, faces: List[Dict]) -> None:
    """Draw white bounding boxes and center points for faces."""
    
def draw_face_center_points(self, m: MappedArray, faces: List[Dict]) -> None:
    """Draw center points for detected faces."""
```

**Method to Modify**: `annotate_screen()`
- Add face drawing when face detection data is available
- Use white color (255, 255, 255) for face bounding boxes
- Draw center points as small circles

#### 2.2 Face Data Flow to Camera
**Approach**: Extend the existing detection data structure
- Add 'faces' key to detection dictionaries
- Pass face data through existing tracked_objects mechanism
- No changes to core camera tracking logic needed

### Phase 3: Optimal Positioning Algorithm

#### 3.1 Face Coverage Calculation
**File**: `raspibot/core/room_scan.py`

**New Algorithm**:
```python
def _calculate_optimal_face_angle(self) -> float:
    """
    Calculate camera angle that maximizes face coverage.
    
    Algorithm:
    1. Group all detected faces by their world angles
    2. Calculate field of view coverage for each potential camera angle
    3. Score each angle by number of faces within FOV
    4. Return angle with highest score
    """
```

#### 3.2 Post-Scan Positioning
**Integration Point**: End of `scan_room()` and `scan_room_async()` methods
- Calculate optimal angle after deduplication
- Move to optimal position before returning to center
- Log face coverage statistics

### Phase 4: Data Structure Extensions

#### 4.1 Enhanced Detection Dictionary
**Current Structure**:
```python
{
    "label": "person",
    "confidence": 0.85,
    "box": (x, y, w, h),
    "pan_angle": 45.0,
    "world_angle": 47.3,
    "position_index": 2,
    "timestamp": 1234567890.0
}
```

**Extended Structure**:
```python
{
    "label": "person",
    "confidence": 0.85,
    "box": (x, y, w, h),
    "pan_angle": 45.0,
    "world_angle": 47.3,
    "position_index": 2,
    "timestamp": 1234567890.0,
    "faces": [  # New field
        {
            "box": (face_x, face_y, face_w, face_h),
            "confidence": 0.75,
            "center": (center_x, center_y)
        }
    ],
    "is_confirmed_person": True  # New field
}
```

#### 4.2 Face Tracking State
**New Attributes for RoomScanner**:
```python
self.detected_faces = []  # All face detections across scan
self.confirmed_people = []  # Person objects with detected faces
self.face_coverage_stats = {}  # Statistics for optimal positioning
```

## Implementation Safety Measures

### Backward Compatibility
- All changes are additive - no existing functionality removed
- Face detection is optional (controlled by `face_detection` parameter)
- Existing API signatures unchanged
- Default behavior unchanged when face detection disabled

### Error Handling
- Graceful fallback if face detection fails
- Continue room scan even if face detection encounters errors
- Log warnings for face detection issues without stopping scan

### Performance Considerations
- Face detection only on "person" objects (not all detections)
- Reuse existing frame data where possible
- Minimal additional memory overhead
- Optional feature can be disabled for performance

## Testing Strategy

### Unit Tests Required
1. **Face Detection Integration Tests**
   - Test face detection on person objects
   - Test handling of person objects without faces
   - Test face data structure integration

2. **Display Integration Tests**
   - Test white bounding box drawing for faces
   - Test center point drawing
   - Test coordinate mapping

3. **Optimal Positioning Tests**
   - Test face coverage calculation
   - Test optimal angle selection
   - Test edge cases (no faces, single face, multiple faces)

### Integration Tests
1. **End-to-End Room Scan with Face Detection**
   - Complete scan with face detection enabled
   - Verify face data in final results
   - Test optimal positioning movement

2. **Backward Compatibility Tests**
   - Ensure existing functionality unchanged
   - Test with face detection disabled
   - Verify no performance regression

## Configuration Integration

### New Configuration Options
**File**: `raspibot/settings/config.py`

```python
# Face Detection Settings
FACE_DETECTION_CONFIDENCE_THRESHOLD = 0.6
FACE_DETECTION_MODEL_PATH = None  # None for Haar cascade, path for ONNX
FACE_BOX_COLOR = (255, 255, 255)  # White
FACE_CENTER_POINT_RADIUS = 3
FACE_CENTER_POINT_COLOR = (255, 255, 255)  # White
```

## File Modification Summary

### Files to Modify
1. **`raspibot/core/room_scan.py`** - Major changes
   - Add face detector initialization
   - Modify detection capture methods
   - Add optimal positioning methods
   - Extend data structures

2. **`raspibot/hardware/cameras/camera.py`** - Minor changes
   - Add face drawing methods
   - Extend annotate_screen method

3. **`raspibot/vision/deduplication.py`** - Minor changes
   - Handle face data in deduplication
   - Extend temporal smoothing for faces

4. **`raspibot/settings/config.py`** - Minor additions
   - Add face detection configuration options

### Files to Create
- None (all functionality integrated into existing files)

### Dependencies
- No new external dependencies required
- Existing face detection module already available
- All required imports already in place

## Risk Assessment

### Low Risk Changes
- Display enhancements (additive only)
- Configuration additions
- New optional methods

### Medium Risk Changes
- Room scanner detection flow modifications
- Data structure extensions

### Mitigation Strategies
- Comprehensive unit testing before integration
- Feature flag for easy disable
- Backup branch creation before changes
- Incremental integration approach

## Success Criteria

### Functional Requirements Met
1. ✅ Face detection integrated into room scan process
2. ✅ Person objects with faces cached as confirmed people
3. ✅ White bounding boxes displayed for detected faces
4. ✅ Face center points shown on display
5. ✅ Optimal camera angle calculated and applied
6. ✅ Backward compatibility maintained

### Quality Requirements Met
1. ✅ All existing tests continue to pass
2. ✅ New functionality covered by unit tests
3. ✅ No performance regression
4. ✅ Error handling maintains system stability
5. ✅ Code follows existing patterns and conventions

## Implementation Order

### Phase 1: Foundation (Files: room_scan.py)
1. Add face detector initialization
2. Create basic face detection methods
3. Add unit tests for new methods

### Phase 2: Detection Integration (Files: room_scan.py)
1. Modify detection capture to include faces
2. Update data structures
3. Test face detection in person objects

### Phase 3: Display Integration (Files: camera.py)
1. Add face drawing methods
2. Extend annotation system
3. Test visual display

### Phase 4: Optimal Positioning (Files: room_scan.py)
1. Implement face coverage algorithm
2. Add post-scan positioning
3. Test optimal angle calculation

### Phase 5: Final Integration
1. End-to-end testing
2. Performance validation
3. Documentation updates

This plan ensures a safe, incremental approach to integrating face detection while preserving all existing functionality and maintaining the hobbyist-friendly design principles of the codebase.