"""Hardware configuration constants and mappings.

This module defines hardware-specific constants including pin mappings,
device addresses, and operational limits for the Raspibot hardware.
"""
import os
from typing import Final, Dict,Tuple

# Application settings loaded from environment
DEBUG: Final[bool] = os.getenv('RASPIBOT_DEBUG', 'false').lower() == 'true'
LOG_LEVEL: Final[str] = os.getenv('RASPIBOT_LOG_LEVEL', 'INFO')
LOG_TO_FILE: Final[bool] = os.getenv('RASPIBOT_LOG_TO_FILE', 'true').lower() == 'true'
LOG_STACKTRACE: Final[bool] = os.getenv('RASPIBOT_LOG_STACKTRACE', 'false').lower() == 'true'
LOG_FILE_PATH: Final[str] = os.getenv('RASPIBOT_LOG_FILE_PATH', 'data/logs/raspibot.log') 

PI_DISPLAY_MODE: Final[str] = "connect" # screen, connect, ssh, none

# I2C Configuration
I2C_BUS: Final[int] = 1  # Standard I2C bus on Raspberry Pi
PCA9685_ADDRESS: Final[int] = 0x40  # Default PCA9685 I2C address

# Servo Configuration - Calibrated Values
# Pan servo: 0.4ms=0°, 1.47ms=90°, 2.52ms=180°, 2.7ms≈200°
# Tilt servo: 0.4ms=0°, 1.45ms=90°, 2.47ms=180°, 2.7ms≈200°
SERVO_MIN_ANGLE: Final[int] = 0
SERVO_MAX_ANGLE: Final[int] = 180  # Updated to match logical range; 2.7ms ≈ 200° is physical max
SERVO_DEFAULT_ANGLE: Final[int] = 90
SERVO_PAN_CHANNEL: Final[int] = 0
SERVO_TILT_CHANNEL: Final[int] = 1
SERVO_CHANNELS: Final[list[int]] = [0, 1]  # Channels used for servos
'''
# Pan servo pulse width calibration (ms)
SERVO_PAN_0_PULSE: Final[float] = 0.4    # 0°
SERVO_PAN_90_PULSE: Final[float] = 1.47  # 90°
SERVO_PAN_180_PULSE: Final[float] = 2.52 # 180°
SERVO_PAN_MAX_PULSE: Final[float] = 2.7  # ~200° (physical max)

# Tilt servo pulse width calibration (ms)
SERVO_TILT_0_PULSE: Final[float] = 0.4    # 0°
SERVO_TILT_90_PULSE: Final[float] = 1.4   # 90° (corrected)
SERVO_TILT_180_PULSE: Final[float] = 2.47 # 180°
SERVO_TILT_MAX_PULSE: Final[float] = 2.7  # ~200° (physical max)

# Calibrated Pulse Width Values (in milliseconds)
SERVO_MIN_PULSE: Final[float] = 0.4   # 0 degrees
SERVO_CENTER_PULSE: Final[float] = 1.45  # 90 degrees (tilt servo)
SERVO_MAX_PULSE: Final[float] = 2.7   # 200 degrees (maximum)

# Pan/Tilt Specific Configuration
SERVO_PAN_MIN_ANGLE: Final[int] = 0
SERVO_PAN_MAX_ANGLE: Final[int] = 200  # Updated to match actual range
SERVO_PAN_CENTER: Final[int] = 90

# Tilt Configuration - Using full calibrated range
SERVO_TILT_MIN_ANGLE: Final[int] = 0   # 0° = pointing down (0.4ms)
SERVO_TILT_MAX_ANGLE: Final[int] = 200  # 200° = pointing up (2.7ms)
SERVO_TILT_CENTER: Final[int] = 90     # 90° = center (1.45ms)
SERVO_TILT_UP_ANGLE: Final[int] = 200   # Pointing up (2.7ms)
SERVO_TILT_DOWN_ANGLE: Final[int] = 0   # Pointing down (0.4ms)'''

# PCA9685 Anti-Jitter Settings
PCA9685_DEADBAND: Final[float] = 0.5  # Reduced from 2.0 - minimum angle change to trigger movement (degrees)
PCA9685_STABILIZATION_DELAY: Final[float] = 0.02  # Reduced from 0.1 - delay after movement to stabilize (seconds)
PCA9685_MIN_STEP_SIZE: Final[float] = 0.5  # Reduced from 2.0 - minimum step size for smoother movement (degrees)
PCA9685_MAX_STEP_SIZE: Final[float] = 2.0  # Reduced from 5.0 - maximum step size for faster movement (degrees)
PCA9685_STEP_DELAY: Final[float] = 0.01  # Reduced from 0.02 - delay between steps for smoother movement (seconds)
PCA9685_PWM_PRECISION: Final[int] = 3  # Increased from 2 - PWM precision to minimize jitter

# Camera Configuration
CAMERA_DEFAULT_WIDTH: Final[int] = 1280
CAMERA_DEFAULT_HEIGHT: Final[int] = 720
CAMERA_DEVICE_ID: Final[int] = 0

'''# Face Tracking Configuration  
FACE_MOVEMENT_THRESHOLD: Final[int] = 50   # pixels - minimum movement to trigger servo
FACE_MOVEMENT_SCALE: Final[float] = 0.3    # how much to move servo per pixel offset
FACE_STABILITY_THRESHOLD: Final[int] = 100 # pixels - max movement to be considered stable
FACE_STABILITY_FRAMES: Final[int] = 3      # frames needed to confirm stability
SLEEP_TIMEOUT: Final[int] = 300            # 5 minutes of no faces

# Search Pattern Configuration
SEARCH_PATTERN_ENABLED: Final[bool] = True  # Enable systematic search patterns
SEARCH_PAN_STEPS: Final[int] = 8           # Number of pan steps per tilt level
SEARCH_TILT_STEPS: Final[int] = 6          # Number of tilt levels to scan
SEARCH_MOVEMENT_SPEED: Final[float] = 0.3  # Slow movement speed for search (0.1-1.0)
SEARCH_STABILIZATION_DELAY: Final[float] = 0.5  # Delay after movement to stabilize (seconds)
SEARCH_FACE_DETECTION_DELAY: Final[float] = 0.2  # Delay for face detection at each position (seconds)
SEARCH_PATTERN_TIMEOUT: Final[int] = 60    # Timeout for complete search pattern (seconds)
SEARCH_RETURN_TO_CENTER: Final[bool] = True  # Return to center after search pattern

# GPIO Servo Configuration - Calibrated Values
GPIO_SERVO_MIN_ANGLE: Final[int] = 0
GPIO_SERVO_MAX_ANGLE: Final[int] = 200  # Updated to match actual servo range
GPIO_SERVO_DEFAULT_ANGLE: Final[int] = 90  # Center position (1.45ms)
GPIO_SERVO_FREQUENCY: Final[int] = 50  # PWM frequency in Hz
GPIO_SERVO_MIN_PULSE: Final[float] = 0.4  # Minimum pulse width in ms (0 degrees)
GPIO_SERVO_MAX_PULSE: Final[float] = 2.7  # Maximum pulse width in ms (200 degrees)

# GPIO Servo Anti-Jitter Settings
GPIO_SERVO_DEADBAND: Final[float] = 1.0  # Minimum angle change to trigger movement (degrees)
GPIO_SERVO_STABILIZATION_DELAY: Final[float] = 0.05  # Reduced delay after movement to stabilize (seconds)
GPIO_SERVO_MIN_STEP_SIZE: Final[float] = 1.0  # Increased minimum step size for smoother movement (degrees)
GPIO_SERVO_MAX_STEP_SIZE: Final[float] = 3.0  # Increased maximum step size for faster movement (degrees)
GPIO_SERVO_STEP_DELAY: Final[float] = 0.01  # Reduced delay between steps for smoother movement (seconds)
GPIO_SERVO_DUTY_CYCLE_PRECISION: Final[int] = 1  # Reduced precision to minimize PWM jitter

# GPIO Servo Pin Mappings
# Dictionary mapping servo channels to GPIO pins
# Format: {channel: gpio_pin}
GPIO_SERVO_PINS: Final[Dict[int, int]] = {
    0: 17,  # Pan servo on GPIO 17
    1: 18,  # Tilt servo on GPIO 18
}'''

# Pi AI Camera Configuration
AI_DEFAULT_VISION_MODEL: Final[str] = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
AI_CAMERA_RESOLUTION: Final[Tuple[int, int]] = (1280, 720)
CAMERA_DISPLAY_RESOLUTION: Final[Tuple[int, int]] = (1280, 720)
CAMERA_DISPLAY_POSITION: Final[Tuple[int, int]] = (5, 10)
AI_DETECTION_THRESHOLD: Final[float] = 0.4
AI_IOU_THRESHOLD: Final[float] = 0.65
AI_MAX_DETECTIONS: Final[int] = 20
AI_CAMERA_DEVICE_ID: Final[int] = 0
AI_INFERERENCE_FRAME_RATE: Final[int] = 30



'''PI_AI_CAMERA_CONFIG: Final[Dict] = {
    "default_model": "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk",
    "tensor_input_size": (320, 320),  # IMX500 fixed tensor size
    
    # Camera Mode Configurations
    "camera_modes": {
        # Normal video mode (camera & display)
        "normal_video": {
            "detection": {
                "resolution": (1280, 720),
                "format": "XBGR8888",
                "purpose": "Standard video capture and display"
            },
            "display": {
                "resolution": (1280, 720),
                "format": "BGR",
                "purpose": "Color display for user interface"
            },
            "memory_mb_per_frame": 3.52
        },
        
        # AI detection mode (YUV420 for detection, color for display)
        "ai_detection": {
            "detection": {
                "resolution": (1920, 1080),
                "format": "YUV420",
                "purpose": "High-resolution AI detection with 50% memory reduction"
            },
            "display": {
                "resolution": (1280, 720),
                "format": "BGR",
                "purpose": "Color display for user interface"
            },
            "memory_mb_per_frame": 2.64  # YUV420 is 1.5 bytes/pixel vs 3 bytes/pixel
        },
        
        # OpenCV detection mode (grayscale for detection, color for display)
        "opencv_detection": {
            "detection": {
                "resolution": (1280, 720),
                "format": "grayscale",
                "purpose": "Grayscale processing for OpenCV face detection"
            },
            "display": {
                "resolution": (1280, 720),
                "format": "BGR",
                "purpose": "Color display for user interface"
            },
            "memory_mb_per_frame": 0.88  # Grayscale is 1 byte/pixel
        }
    },
    
    # Legacy configurations (for backward compatibility)
    "display_optimal": {
        "resolution": (1280, 720),  # HD color for best visual quality
        "purpose": "Live video feed, user interface, monitoring",
        "memory_mb_per_frame": 3.52,
        "format": "color"
    },
    
    "detection_optimal": {
        "resolution": (640, 640),  # Higher effective resolution for grayscale
        "purpose": "Face detection, object recognition, tracking",
        "memory_mb_per_frame": 0.39,
        "format": "grayscale"
    },
    
    "hybrid_optimal": {
        "display_resolution": (1280, 720),  # Color for visual quality
        "detection_resolution": (640, 640),  # Grayscale for AI accuracy
        "total_memory_mb_per_frame": 3.91,
        "purpose": "Complete robot vision system"
    },
    
    # Performance targets
    "performance_targets": {
        "target_fps": 30,
        "max_memory_mb_per_sec": 100,
        "recommended_resolutions": [
            (640, 480),    # 35.2 MB/s - Safe
            (800, 600),    # 54.9 MB/s - Good
            (1024, 768),   # 90.0 MB/s - Optimal
            (1280, 720),   # 105.5 MB/s - High but usable
            (1920, 1080),  # 237.4 MB/s - High resolution (YUV420: 118.7 MB/s)
        ]
    },
    
    # Detection settings
    "people_detection": {
        "confidence_threshold": 0.55,
        "iou_threshold": 0.65,
        "max_detections": 10,
        "inference_rate": 30
    },
    "face_detection": {
        "confidence_threshold": 0.6,
        "iou_threshold": 0.3,
        "max_detections": 5,
        "inference_rate": 30
    },
    
    # Grayscale processing benefits
    "grayscale_processing": {
        "enabled": True,
        "memory_savings_percent": 75.0,
        "effective_resolution_benefit": 4.0,  # 4x more pixels for same memory
        "recommended_for_tensor": True,
        "fps_improvement": 1.22,  # 22% better FPS than color
        "memory_efficiency": 9.0   # 9x better memory efficiency
    },
    
    # YUV420 processing benefits
    "yuv420_processing": {
        "enabled": True,
        "memory_savings_percent": 50.0,  # 50% memory reduction vs color
        "ai_compatibility": True,  # AI detection works at ALL resolutions
        "color_preservation": True,  # Full color information preserved
        "fps_improvement": 1.15,  # 15% better FPS than color
        "memory_efficiency": 2.0   # 2x better memory efficiency
    }
}'''

'''# Search Pattern Configuration
SEARCH_PATTERN_CONFIG: Final[Dict] = {
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
}'''
