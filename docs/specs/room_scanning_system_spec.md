# Room Scanning and Face Recognition System - Experimental Specification

## Overview
This document outlines the experimental development of a room scanning and face recognition system for the Raspberry Pi robot. The system will periodically scan the environment to detect and identify people, building a memory of individuals over time.

## Current State Analysis
From `experiments/room_scan.py`, we have:
- Basic 3-position scanning (0°, 90°, 180°) 
- Object detection integration with servo angle tracking
- Person centering calculation with FOV approximation
- Simple servo movement with fixed delays

## System Architecture

### Phase 1: Enhanced Room Scanning
**Goal**: Smooth horizontal scanning with comprehensive FOV coverage

**Features**:
- Dynamic scan positions based on camera FOV chunks
- Smooth servo movements (no jarring jumps)
- Object detection with precise pan angle correlation
- Detection confidence tracking across scan positions

**Technical Approach**:
- Calculate scan positions: `range(pan_min, pan_max, fov_chunk_size)`
- Smooth servo transitions with configurable step size and delay
- Capture multiple frames per position for detection stability
- Store detections with precise servo angles

### Phase 2: Object Detection and Tracking
**Goal**: Build comprehensive object catalog with spatial awareness

**Features**:
- Object list with pan angles for focusing
- Detection persistence across scan cycles
- Confidence-based object filtering
- Person object prioritization

**Data Structure**:
```python
{
    "id": "obj_001",
    "label": "person", 
    "confidence": 0.87,
    "pan_angle": 45,
    "tilt_angle": 90,
    "bounding_box": [x, y, w, h],
    "first_seen": timestamp,
    "last_seen": timestamp,
    "scan_count": 3
}
```

### Phase 3: Face Detection and Head Tracking
**Goal**: Detect faces within person objects, adjust tilt for optimal framing

**Features**:
- Face detection within person bounding boxes
- Automatic tilt adjustment if face not found
- Head-up detection (person top at frame edge)
- Multi-attempt face detection with tilt increments
- **Photograph filtering**: Distinguish real people from photographs/posters

**Algorithm**:
1. For each person object, extract bounding box region
2. Run face detection on extracted region
3. If no face and person top near frame edge, tilt up 10-15°
4. Retry face detection up to 3 attempts
5. **TODO**: Implement photograph detection (depth analysis, motion detection, or texture analysis)
6. Store successful face crops for recognition (real people only)

### Phase 4: Face Recognition Preparation
**Goal**: Capture and store face data for future recognition

**Features**:
- Face frame extraction and normalization. With default method and allow models e.g. data/models/face_detection_yunet_2023mar.onnx
- Multiple angle face capture per person
- Quality assessment (blur, lighting, angle)
- Face embedding generation (future: for recognition)

**Storage Strategy**:
- Temporary in-memory storage during scan
- Frame quality scoring
- Best N frames per detected person
- Unique person ID assignment

### Phase 5: Person Memory and Identity Management
**Goal**: Maintain persistent person records with unique identities

**Features**:
- Unique person ID generation
- Spatial consistency checking (same location = same person?)
- Person disappearance/reappearance handling
- Memory refresh strategies

**Identity Logic**:
- New person: assign new ID
- Similar location + timing: likely same person
- Face similarity: future enhancement
- Person timeout: remove from active memory

### Phase 6: Permission and Recognition Framework
**Goal**: Foundation for future face recognition and permission system

**Features**:
- Face data storage with consent framework
- Person recognition preparation
- Name association (future: voice input)
- Privacy and data management

## Technical Configuration

### Camera Settings
- FOV Horizontal: 60° (configurable, device-dependent)
- FOV Vertical: 45° (configurable, device-dependent)
- Scan overlap: 10° (ensure no gaps)

### Servo Movement
- Smooth movement: 2-5° steps with 100ms delays
- Settling time: 2-3 seconds per position
- Detection frames: 5-10 frames per position
- Confidence threshold: 0.6 for person detection

### Memory Management
- Active scan data: 10-minute retention
- Person records: session-based (future: persistent)
- Face frames: 5 best frames per person
- Cleanup: remove stale detections

## Experimental Development Process

### Step 1: Enhanced Scanning Engine
Create `room_scanner_v2.py` with:
- Smooth servo movement functions
- FOV-based position calculation
- Detection capture and correlation
- Real-time progress display

### Step 2: Object Catalog
Add to same file:
- Object storage and tracking
- Person filtering and prioritization
- Spatial relationship mapping

### Step 3: Face Detection Integration
Enhance with:
- OpenCV face detection
- Tilt adjustment logic
- Face quality assessment
- Frame capture system

### Step 4: Identity System
Add:
- Unique ID generation
- Person consistency logic
- Memory management
- Data structure refinement

## Success Criteria

### Functional Goals
1. **Smooth Scanning**: No jarring servo movements, professional appearance
2. **Complete Coverage**: No blind spots in horizontal sweep
3. **Reliable Detection**: Consistent person detection across positions
4. **Face Capture**: 80%+ success rate for face detection in person objects
5. **Identity Tracking**: Unique ID assignment with minimal duplicates

### Performance Targets
- Full room scan: < 2 minutes
- Face detection attempts: < 30 seconds per person
- Memory efficiency: < 100MB for typical room scan
- Detection accuracy: > 0.7 confidence for person objects

## Future Integration Points

### Hardware Expansion
- Directional microphone array integration
- Wake word detection correlation
- Voice command processing
- Audio-visual person association

### AI Enhancement
- Face recognition model integration
- Person re-identification across sessions
- Behavioral pattern learning
- Conversation context awareness

### Privacy and Ethics
- Consent management system
- Data retention policies
- Opt-out mechanisms
- Audit trails for face data usage

## Risk Mitigation

### Privacy Concerns
- Local processing only (no cloud face data)
- Clear consent mechanisms
- Data minimization principles
- Regular data purging

### Technical Risks
- Face detection accuracy in varying lighting
- Person identity confusion in groups
- Memory leaks in long-running scans
- Servo wear from frequent movement
- **Photograph false positives**: Photos/posters detected as real people

### Failure Modes
- Graceful degradation without face detection
- Recovery from servo movement failures
- Handling of detection system crashes
- Backup scanning modes

## Future Enhancements

### Photograph Detection (TODO - Post Phase 3)
**Problem**: AI detects people in photographs/posters as real people
**Potential Solutions**:
1. **Motion Analysis**: Real people move slightly, photographs don't
2. **Depth Analysis**: Use stereo vision or structured light for depth
3. **Texture Analysis**: Photos often have different texture/glare patterns
4. **Temporal Consistency**: Track movement over time
5. **Size Analysis**: Photos often have unusual perspective/sizing

**Implementation Priority**: Address after core face detection is working

---

**Document Status**: Draft v1.0
**Last Updated**: 2025-08-10
**Next Review**: After Phase 1 implementation