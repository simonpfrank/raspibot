# Room Scan System Specification

## Overview
The room scan system combines camera detection with servo movement to systematically scan and identify objects in a room. It provides robust deduplication to ensure each physical object is counted only once, despite being detected across multiple camera positions.

## Core Requirements
- **Simple**: Minimal code, maximum readability for hobbyist programmers  
- **Flexible**: Works with or without asyncio for future robot integration
- **Modular**: Split across vision/movement/core following existing architecture
- **Extensible**: Built to add OpenCV face detection later
- **Robust**: Proven deduplication methods from experiments

## Architecture

### Module Structure
```
raspibot/
├── vision/
│   └── deduplication.py      # Object deduplication logic
├── movement/
│   └── scanner.py           # Servo movement patterns  
└── core/
    └── room_scan.py         # Main room scan orchestrator
```

### Key Classes
- `ObjectDeduplicator` - Handles duplicate detection removal
- `ScanPattern` - Manages servo movement for room scanning  
- `RoomScanner` - Main class that coordinates vision + movement

## Detailed Design

### 1. Object Deduplication (`raspibot/vision/deduplication.py`)

**Purpose**: Remove duplicate detections of the same physical object across camera positions

**Core Methods**: Spatial similarity, bounding box overlap, temporal smoothing

```python
class ObjectDeduplicator:
    """Removes duplicate object detections across camera positions."""
    
    def __init__(self, 
                 spatial_threshold: float = 0.7,
                 box_overlap_threshold: float = 0.2, 
                 min_frames: int = 3):
        # Simple constructor with proven thresholds
        
    def deduplicate(self, detections: List[Dict]) -> List[Dict]:
        """Remove duplicates using configured methods."""
        # Apply temporal smoothing first
        # Then spatial + box overlap deduplication
        # Return unique objects only
        
    async def deduplicate_async(self, detections: List[Dict]) -> List[Dict]:
        """Async version for robot integration."""
```

**Detection Format** (simple dict, no dataclasses):
```python
{
    'label': 'person',
    'confidence': 0.85,
    'box': (x, y, w, h),
    'pan_angle': 45.0,
    'world_angle': 47.3,  # Calculated from pan + pixel offset
    'position_index': 2,
    'timestamp': 1234567890.5
}
```

### 2. Scan Movement (`raspibot/movement/scanner.py`)

**Purpose**: Handle servo movement patterns for systematic room scanning

```python
class ScanPattern:
    """Manages servo movement for room scanning."""
    
    def __init__(self, fov_degrees: float = 66.3, overlap_degrees: float = 10.0):
        # Use camera FOV to calculate optimal positions
        
    def calculate_positions(self) -> List[float]:
        """Calculate pan angles for complete room coverage."""
        # Return list of pan angles: [0, 45, 90, 135, 180]
        
    def move_to_position(self, servo_controller, pan_angle: float, tilt_angle: float):
        """Move servos to scan position (direct, no smooth movement)."""
        
    async def move_to_position_async(self, servo_controller, pan_angle: float, tilt_angle: float):
        """Async version using servo smooth_move_to_angle if needed."""
```

### 3. Room Scanner (`raspibot/core/room_scan.py`)

**Purpose**: Main orchestrator that combines camera detection with servo movement

```python
class RoomScanner:
    """Main room scanning system."""
    
    def __init__(self, 
                 camera=None,           # Use existing Camera class
                 servo_controller=None, # Use existing servo system
                 face_detection=False,  # Enable face validation
                 frames_per_position=6, # Proven from experiments
                 settling_time=1.0):
        
    def scan_room(self) -> List[Dict]:
        """Perform complete room scan and return unique objects."""
        # 1. Calculate scan positions
        # 2. For each position:
        #    - Move servos
        #    - Wait for settling
        #    - Capture multiple frames
        #    - Extract detections
        # 3. Deduplicate all detections
        # 4. Return to center
        # 5. Return unique objects
        
    async def scan_room_async(self) -> List[Dict]:
        """Async version for robot integration."""
        
    def enable_face_detection(self, enabled: bool):
        """Toggle face detection validation for person objects."""
        
    def get_scan_summary(self) -> Dict:
        """Return summary statistics from last scan."""
```

## Implementation Plan

### Phase 1: Core Functionality
1. **Create ObjectDeduplicator** (`vision/deduplication.py`)
   - Implement 3 proven methods: spatial similarity, box overlap, temporal smoothing
   - Simple dict-based detection format
   - Both sync/async versions

2. **Create ScanPattern** (`movement/scanner.py`)  
   - Calculate optimal positions based on camera FOV
   - Direct servo movement (no smooth wrapper)
   - Both sync/async versions

3. **Create RoomScanner** (`core/room_scan.py`)
   - Orchestrate camera + servo coordination
   - Use existing Camera and servo classes
   - Return simple detection list
   - Both sync/async versions

### Phase 2: Face Detection Integration
4. **Add face validation to ObjectDeduplicator**
   - Optional OpenCV face detection on person objects
   - Configurable on/off via RoomScanner constructor
   - Validate person detections have faces

5. **Extend RoomScanner for face detection**
   - `face_detection=True` parameter
   - Works with AI camera's person detection + OpenCV validation

## Pseudo Code Example

```python
# Usage example
from raspibot.core.room_scan import RoomScanner
from raspibot.hardware.cameras.camera import Camera
from raspibot.hardware.servos.controller_selector import get_servo_controller

# Setup
camera = Camera()
servo_controller = get_servo_controller()
scanner = RoomScanner(camera, servo_controller, face_detection=False)

# Scan room
objects = scanner.scan_room()

# Results
for obj in objects:
    print(f"Found {obj['label']} at {obj['world_angle']:.1f}° with confidence {obj['confidence']:.2f}")
    
# Example output:
# Found person at 45.3° with confidence 0.87
# Found person at 134.7° with confidence 0.92  
# Found bottle at 12.1° with confidence 0.75
```

## Testing Strategy
- Unit tests for each deduplication method
- Integration tests with mock camera/servo
- Hardware tests on actual robot setup
- Compare results with experimental v3 scanner

## Future Extensions
- OpenCV face detection validation
- Additional object types beyond person
- Export to CSV/JSON for analysis
- Integration with main robot control system

## Success Criteria
- ✅ Scan complete room systematically
- ✅ Identify unique objects (no duplicates)  
- ✅ Work with existing camera/servo classes
- ✅ Support both sync and async operation
- ✅ Simple, readable code for hobbyist programmers
- ✅ Extensible for future face detection