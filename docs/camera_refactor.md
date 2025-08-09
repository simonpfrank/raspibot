# Camera Refactor Design

## Goal: Simple, DRY Camera System for Hobbyists

### Current Issues
- 3+ separate camera files with duplicate code
- Repeated display_modes, initialization patterns, start/stop logic
- Complex inheritance patterns hard for hobbyists to understand
- DRY violations in hardware detection, preview management

### Proposed Solution: Single Camera Module

**File Structure:**
```
raspibot/hardware/cameras/
├── camera.py          # Single file containing all camera functionality
└── __init__.py        # Exports main Camera class
```

### Design: Single Camera Class with Auto-Detection

**Core Principle:** One class that automatically detects and handles any camera type.

```python
# camera.py
class Camera:
    """Universal camera class - auto-detects Pi AI, Pi, or USB cameras"""
    
    def __init__(self, 
                 camera_device_id=None,     # Auto-select if None
                 camera_resolution=None,    # From config if None  
                 display_resolution=None,   # From config if None
                 display_position=None,     # From config if None
                 display_mode=None):        # From config if None
        
        # Load defaults from config
        # Auto-detect camera type using _detect_camera_type()
        # Initialize hardware based on detected type
        # Set camera-specific capabilities
    
    def _detect_camera_type(self):
        """Single method to detect camera type from Picamera2.global_camera_info()"""
        # Returns: "pi_ai", "pi", or "usb"
        # Uses model names: "imx500" = pi_ai, "imx" = pi, "uvc" = usb
    
    def start(self):
        """Universal start method - works for all camera types"""
        # Start preview with display_modes[self.display_mode]
        # Configure camera based on self.camera_type
        # Handle AI-specific setup if pi_ai
    
    def detect(self, callback=None):
        """Universal detect loop with optional callback"""
        while self.is_detecting:
            if callback:
                callback(self)
            
            # AI-specific detection processing if pi_ai camera
            if self.camera_type == "pi_ai":
                # Process AI detections, NMS, tracking
                # Set self.detections for annotation callback
            
            # Preview closure detection
            # Sleep to prevent busy waiting
    
    def stop(self):
        """Universal stop method"""
    
    def shutdown(self):
        """Universal cleanup method"""

# AI Detection Methods (only active for pi_ai cameras)
def _setup_ai_detection(self):
    """Initialize IMX500 AI processing"""

def _process_ai_detections(self):
    """Process AI detections, apply NMS, update tracking"""

# Utility Methods
def _load_config_defaults(self):
    """Load settings from config.py"""

def _setup_display_environment(self):
    """Handle display environment variables"""
```

### Configuration Strategy

**Single config section:**
```python
# config.py
# Camera Configuration (unified)
CAMERA_RESOLUTION = (1280, 720)
CAMERA_DISPLAY_RESOLUTION = (1280, 720) 
CAMERA_DISPLAY_POSITION = (0, 0)
PI_DISPLAY_MODE = "screen"

# AI-specific settings (only used when AI camera detected)
AI_DETECTION_THRESHOLD = 0.55
AI_IOU_THRESHOLD = 0.65
AI_MAX_DETECTIONS = 10
AI_INFERENCE_FRAME_RATE = 30
```

### Usage Examples

**Basic usage (auto-detection):**
```python
from raspibot.hardware.cameras import Camera

# Auto-detects best available camera
camera = Camera()
camera.start()
camera.detect()  # Just display
```

**With callback for processing:**
```python
def face_detection_callback(camera):
    # Access camera.detections if AI camera
    # Do OpenCV processing for other cameras
    pass

camera = Camera()
camera.start()
camera.detect(callback=face_detection_callback)
```

**Explicit camera selection:**
```python
# Force specific camera device
camera = Camera(camera_device_id=1)
```

### Benefits

1. **Simplicity:** One import, one class, auto-detection
2. **DRY:** All common code in single location
3. **Hobbyist-friendly:** No need to understand different camera types
4. **Flexible:** Callback system allows custom processing
5. **Maintainable:** Changes in one place affect all camera types

### Implementation Plan

1. Create new `camera.py` with Camera class
2. Move display_modes, config loading to single location  
3. Implement `_detect_camera_type()` using Picamera2.global_camera_info()
4. Consolidate start/stop/shutdown logic
5. Move AI detection methods inside main class (conditional activation)
6. Update imports across codebase
7. Remove old camera files after testing

### Pseudo Code Structure

```python
class Camera:
    def __init__(self, **kwargs):
        self._load_config_defaults(**kwargs)
        self.camera_type = self._detect_camera_type() 
        self._initialize_hardware()
        if self.camera_type == "pi_ai":
            self._setup_ai_detection()
    
    def _detect_camera_type(self):
        for info in Picamera2.global_camera_info():
            model = info.get("Model", "").lower()
            if self.camera_device_id and info.get("Num") != self.camera_device_id:
                continue
            if "imx500" in model: return "pi_ai"
            elif "imx" in model and "uvc" not in model: return "pi" 
            elif "uvc" in model: return "usb"
        raise RuntimeError("No compatible camera found")
    
    def detect(self, callback=None):
        self.is_detecting = True
        while self.is_detecting:
            if callback: callback(self)
            if self.camera_type == "pi_ai": self._process_ai_detections()
            if not self.camera._preview: break
            time.sleep(0.1)
```

### Migration Strategy

- Keep existing files during transition
- Add deprecation warnings to old classes
- Update unified_camera.py to use new Camera class
- Test each camera type thoroughly
- Remove old files after full validation