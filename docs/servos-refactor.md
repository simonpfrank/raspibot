# Servo Module Refactoring Analysis

## Current Architecture Issues

### 1. Template Class Pattern (Against CLAUDE.md Guidelines)
- `ServoInterface` is essentially an abstract base class using `NotImplementedError`
- Goes against "concrete classes > abstract" principle
- Adds unnecessary complexity for hobbyist code

### 2. Code Duplication
- Jitter workaround (90-100° ban) duplicated across multiple methods in both controllers
- Angle validation logic duplicated
- Smooth movement logic nearly identical in both controllers
- Calibration offset logic duplicated

### 3. Overly Complex Structure
```
servos/
├── servo_template.py        # Template class with 9 abstract methods
├── servo_controller.py      # 440 lines, two controller implementations
├── servo_selector.py        # 113 lines, factory pattern with enums
└── __init__.py             # Imports all classes
```

### 4. Legacy Compatibility Layer
- `PCA9685ServoController` is just a wrapper around `SimplePCA9685ServoController`
- Adds confusion without benefit

### 5. Heavy Dependencies
- Current PCA9685 implementation imports 6 external modules
- ABC imports despite not using abstract base classes properly

## Current Working Functionality (DO NOT BREAK)

### ✅ Core Features That Work
1. **PCA9685 servo control** via Adafruit libraries
2. **GPIO PWM servo control** with calibrated pulse widths
3. **Smooth movement** with configurable speed
4. **Calibration offsets** per channel
5. **Angle validation** and range limiting
6. **Jitter workaround** (90-100° exclusion zone)
7. **Auto-selection** between PCA9685 and GPIO
8. **Pan/tilt integration** via existing interfaces

### ✅ Integration Points (DO NOT CHANGE)
- `raspibot.movement.pan_tilt.PanTiltSystem` uses `ServoInterface` type hints
- `raspibot.core.face_tracking_robot.FaceTrackingRobot` uses factory function
- All test files expect current public API

## Proposed Simplified Architecture

### Target Structure
```
servos/
├── servo.py                 # Single unified controller
├── controller_selector.py   # Simple controller selection
└── __init__.py             # Minimal exports
```

### Design Principles
1. **One controller class per hardware type** (PCA9685, GPIO)
2. **Shared utility functions** for common operations
3. **Composition over inheritance** - no base classes
4. **Simple factory function** instead of enum-based selector

## Simplification Plan

### Phase 1: Consolidate Controllers
- Merge `SimplePCA9685ServoController` and `GPIOServoController` into single file
- Extract shared utilities (angle validation, smooth movement, jitter handling)
- Remove template class entirely
- Keep all existing public methods for compatibility

### Phase 2: Simplify Selection
- Replace enum-based selector with simple function
- Remove complex availability checking
- Keep auto-selection functionality

### Phase 3: Clean Architecture
- Single servo controller file (~200 lines vs current 440)
- Simple selector (~50 lines vs current 113)
- Remove template file entirely

## Compatibility Strategy

### Public API Preservation
```python
# These imports must continue to work:
from raspibot.hardware.servos import PCA9685ServoController, GPIOServoController
from raspibot.hardware.servos import get_servo_controller

# These method signatures must remain identical:
controller.set_servo_angle(channel, angle)
controller.smooth_move_to_angle(channel, angle, speed)
controller.get_servo_angle(channel)
# ... all other public methods
```

### Type Hints Strategy
- Remove `ServoInterface` base class
- Use union types where needed: `Union[PCA9685ServoController, GPIOServoController]`
- Or use protocol for type checking if needed

## Benefits of Simplification

### 1. Reduced Complexity
- From 3 files (566 lines) to 2 files (~250 lines) 
- No abstract base classes or template patterns
- Clearer code flow

### 2. Easier Maintenance
- Single place for shared logic
- Less duplication
- Easier to add new controller types

### 3. Hobbyist-Friendly
- Concrete classes only
- Simple function-based selection
- Clear, direct code patterns

### 4. Preserved Functionality
- All existing features maintained
- Same public API
- No breaking changes

## Implementation Notes

### Jitter Issue Handling
The current 90-100° exclusion zone should remain as a temporary workaround. It's implemented consistently across both controllers and effectively prevents servo jitter in that range.

### New Controller Template
For adding new servo controllers, provide this empty template:

```python
class NewServoController:
    """Template for new servo controller implementation."""
    
    def __init__(self, **kwargs):
        self.current_angles = {}
        self.calibration_offsets = {}
        # Initialize hardware here
        pass
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle on specified channel."""
        # Validate angle with _validate_angle()
        # Apply calibration with _apply_calibration()  
        # Handle jitter with _handle_jitter_zone()
        # Set hardware angle
        pass
    
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle."""
        return self.current_angles.get(channel, 90.0)
    
    def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Move servo smoothly to target angle."""
        # Use _smooth_move_implementation() utility
        pass
    
    # Implement remaining methods: emergency_stop, shutdown, 
    # set_calibration_offset, get_calibration_offset,
    # get_controller_type, get_available_channels
```

## Risk Assessment

### Low Risk
- Consolidating duplicate code
- Removing unused template class
- Simplifying selector logic

### Medium Risk  
- Changing import structure (but maintaining compatibility)
- Removing abstract base class pattern

### High Risk
- None - all public interfaces preserved

## Success Criteria

1. ✅ All existing tests pass without modification
2. ✅ Same public API maintained  
3. ✅ All functionality preserved
4. ✅ Reduced code complexity (50%+ reduction in lines)
5. ✅ Hobbyist-friendly code patterns
6. ✅ Working jitter prevention maintained