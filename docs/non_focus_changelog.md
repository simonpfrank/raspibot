# Non-Focus Changes Log

This file tracks changes made to existing modules while working on other tasks.

## Template Format
```
## [Date] - Main Task: [Description]

### Unexpected Changes Made
- **File**: path/to/file.py, **Line**: 123, **Reason**: Brief explanation
- **File**: path/to/file.py, **Line**: 456, **Reason**: Brief explanation

### Summary
Brief description of why these changes were necessary.
```

---

## 2025-08-07 - Main Task: Create CLAUDE.md file

### Unexpected Changes Made
*No unexpected changes - only created new files as requested*

### Summary
Initial setup of development documentation and change tracking system.

---

## 2025-08-07 - Main Task: Camera Module Cleanup and Refactoring

### Unexpected Changes Made
- **File**: raspibot/hardware/cameras/pi_ai_camera.py, **Lines**: 523-793, **Reason**: Removed 270+ lines of deprecated code (deduplicate_detections, track_detections, and helper methods marked as DEPRECATED)
- **File**: raspibot/hardware/cameras/pi_ai_camera.py, **Line**: 10, **Reason**: Fixed import - replaced unused socket.AI_ADDRCONFIG with os import
- **File**: raspibot/hardware/cameras/pi_camera.py, **Lines**: multiple, **Reason**: Standardized error logging format to include class.method and exception type
- **File**: raspibot/hardware/cameras/usb_camera.py, **Lines**: multiple, **Reason**: Standardized error logging format to include class.method and exception type
- **File**: raspibot/hardware/cameras/usb_camera.py, **Line**: 444, **Reason**: Fixed method call from stop() to shutdown() in context manager

### Summary
Cleaned up camera module following review recommendations. Removed 270+ lines of deprecated code from PiAICamera and standardized error handling patterns across all camera classes. All changes tested successfully with existing experiment scripts.