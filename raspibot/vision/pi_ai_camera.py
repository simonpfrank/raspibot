"""Pi AI Camera implementation using IMX500 hardware acceleration."""

import time
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from functools import lru_cache

try:
    from picamera2 import Picamera2
    from picamera2.devices import IMX500
    from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from .camera_interface import CameraInterface
from .detection_models import PersonDetection, DetectionResult
from ..config.hardware_config import PI_AI_CAMERA_CONFIG
from ..utils.logging_config import setup_logging


class PiAICamera(CameraInterface):
    """Pi AI Camera implementation using IMX500 hardware acceleration."""
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 confidence_threshold: Optional[float] = None,
                 iou_threshold: Optional[float] = None,
                 max_detections: Optional[int] = None,
                 inference_rate: Optional[int] = None,
                 camera_mode: str = "normal_video"):
        """
        Initialize Pi AI Camera.
        
        Args:
            model_path: Path to IMX500 model file
            confidence_threshold: Detection confidence threshold (0.0-1.0)
            iou_threshold: IoU threshold for NMS (0.0-1.0)
            max_detections: Maximum number of detections to return
            inference_rate: Inference rate in FPS
            camera_mode: Camera mode ("normal_video", "ai_detection", "opencv_detection")
        """
        if not PICAMERA2_AVAILABLE:
            raise ImportError("picamera2 not available. Pi AI camera requires picamera2 library.")
        
        self.logger = setup_logging(__name__)
        
        # Model configuration - optimized for 25-30fps performance
        self.model_path = model_path or PI_AI_CAMERA_CONFIG["default_model"]
        self.confidence_threshold = confidence_threshold or PI_AI_CAMERA_CONFIG["people_detection"]["confidence_threshold"]
        self.iou_threshold = iou_threshold or PI_AI_CAMERA_CONFIG["people_detection"]["iou_threshold"]
        self.max_detections = max_detections or PI_AI_CAMERA_CONFIG["people_detection"]["max_detections"]
        self.inference_rate = inference_rate or PI_AI_CAMERA_CONFIG["people_detection"]["inference_rate"]
        
        # Camera mode configuration
        self.camera_mode = camera_mode
        if camera_mode not in PI_AI_CAMERA_CONFIG["camera_modes"]:
            raise ValueError(f"Invalid camera mode: {camera_mode}. Must be one of: {list(PI_AI_CAMERA_CONFIG['camera_modes'].keys())}")
        
        mode_config = PI_AI_CAMERA_CONFIG["camera_modes"][camera_mode]
        self.detection_resolution = mode_config["detection"]["resolution"]
        self.detection_format = mode_config["detection"]["format"]
        self.display_resolution = mode_config["display"]["resolution"]
        self.display_format = mode_config["display"]["format"]
        self.target_resolution = self.display_resolution  # For backward compatibility
        
        self.logger.info(f"Pi AI Camera initialized in {camera_mode} mode")
        self.logger.info(f"Detection: {self.detection_resolution} {self.detection_format}")
        self.logger.info(f"Display: {self.display_resolution} {self.display_format}")
        
        # Camera state
        self.picam2 = None
        self.imx500 = None
        self.is_running = False
        self.last_metadata = None
        self.last_detections = []
        
        # Performance tracking
        self.fps_start_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0.0
        
        # Initialize hardware
        self._initialize_hardware()
    
    def _initialize_hardware(self) -> None:
        """Initialize IMX500 hardware and camera."""
        try:
            # Initialize IMX500 with model
            self.imx500 = IMX500(self.model_path)
            self.intrinsics = self.imx500.network_intrinsics
            
            # Log IMX500 input size requirements
            try:
                input_w, input_h = self.imx500.get_input_size()
                self.logger.info(f"IMX500 neural network requires input size: {input_w}x{input_h}")
            except Exception as e:
                self.logger.warning(f"Could not get IMX500 input size: {e}")
            
            if not self.intrinsics:
                self.intrinsics = NetworkIntrinsics()
                self.intrinsics.task = "object detection"
            elif self.intrinsics.task != "object detection":
                raise ValueError("Network is not an object detection task")
            
            # Override intrinsics with our settings
            self.intrinsics.confidence_threshold = self.confidence_threshold
            self.intrinsics.iou_threshold = self.iou_threshold
            self.intrinsics.max_detections = self.max_detections
            self.intrinsics.inference_rate = self.inference_rate
            
            # Set defaults if not present
            if self.intrinsics.labels is None:
                # Use COCO labels for people detection
                self.intrinsics.labels = ["person"]  # Simplified for people detection
            self.intrinsics.update_with_defaults()
            
            # Initialize Picamera2
            self.picam2 = Picamera2(self.imx500.camera_num)
            
            self.logger.info("Pi AI Camera hardware initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Pi AI Camera hardware: {e}")
            raise
    
    def start(self) -> bool:
        """
        Start camera capture.
        
        Returns:
            True if camera started successfully, False otherwise
        """
        try:
            if self.picam2 is None:
                self.logger.error("Pi AI Camera not initialized")
                return False
            
            self.logger.info(f"Starting Pi AI Camera capture in {self.camera_mode} mode")
            
            # Create configuration based on camera mode
            if self.camera_mode == "ai_detection":
                # AI detection mode: use YUV420 format for detection
                config = self.picam2.create_preview_configuration(
                    main={"size": self.detection_resolution, "format": "YUV420"},
                    encode="main",
                    buffer_count=4
                )
            elif self.camera_mode == "opencv_detection":
                # OpenCV detection mode: use grayscale format
                config = self.picam2.create_preview_configuration(
                    main={"size": self.detection_resolution, "format": "XBGR8888"},
                    buffer_count=4
                )
            else:
                # Normal video mode: use standard color format
                config = self.picam2.create_preview_configuration(
                    main={"size": self.display_resolution, "format": "XBGR8888"},
                    controls={"FrameRate": self.inference_rate}, 
                    buffer_count=12
                )
            
            # Log the actual configuration being applied
            self.logger.info(f"Camera config main size: {config['main']['size']}")
            self.logger.info(f"Camera config main format: {config['main']['format']}")
            self.logger.info(f"Detection resolution: {self.detection_resolution}")
            self.logger.info(f"Display resolution: {self.display_resolution}")
            
            # Show network firmware progress
            self.imx500.show_network_fw_progress_bar()
            
            # Start camera (disable preview for headless operation)
            self.picam2.start(config, show_preview=False)
            
            # Log actual camera configuration after start
            try:
                actual_config = self.picam2.camera_configuration()
                self.logger.info(f"Actual camera size after start: {actual_config['main']['size']}")
                self.logger.info(f"Actual camera format after start: {actual_config['main']['format']}")
            except Exception as e:
                self.logger.warning(f"Could not get actual camera config: {e}")
            
            # Set aspect ratio if needed
            if self.intrinsics.preserve_aspect_ratio:
                self.imx500.set_auto_aspect_ratio()
            
            self.is_running = True
            self.fps_start_time = time.time()
            self.fps_counter = 0
            
            self.logger.info("Pi AI Camera started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting Pi AI Camera: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera in the appropriate format for the current mode.
        
        Returns:
            Frame as numpy array in BGR format for display, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame and metadata
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            
            if frame is not None:
                self._update_fps()
                
                # Convert to BGR format for display based on camera mode
                import cv2
                if self.camera_mode == "ai_detection":
                    # YUV420 format - convert to BGR
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        # YUV420 format, convert to BGR
                        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                    else:
                        # Fallback to direct conversion
                        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                elif self.camera_mode == "opencv_detection":
                    # XBGR8888 format - convert to BGR
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        # XBGR format, convert to BGR
                        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    else:
                        # Already BGR
                        bgr_frame = frame
                else:
                    # Normal video mode - XBGR8888 format
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        # XBGR format, convert to BGR
                        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    else:
                        # Already BGR
                        bgr_frame = frame
                
                # Resize to display resolution if different from detection resolution
                if self.camera_mode == "ai_detection" and bgr_frame.shape[:2] != self.display_resolution[::-1]:
                    bgr_frame = cv2.resize(bgr_frame, self.display_resolution, interpolation=cv2.INTER_AREA)
                
                return bgr_frame
            else:
                self.logger.warning("Failed to capture frame from Pi AI Camera")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def get_frame_grayscale(self) -> Optional[np.ndarray]:
        """
        Get a single grayscale frame from the camera.
        
        Returns:
            Grayscale frame as numpy array, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame and metadata
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            
            if frame is not None:
                self._update_fps()
                
                # Convert to grayscale based on camera mode
                import cv2
                if self.camera_mode == "ai_detection":
                    # YUV420 format - convert to BGR then to grayscale
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                        gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
                    else:
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                elif self.camera_mode == "opencv_detection":
                    # XBGR8888 format - convert to grayscale
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    else:
                        gray_frame = frame
                else:
                    # Normal video mode - XBGR8888 format
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    else:
                        gray_frame = frame
                
                return gray_frame
            else:
                self.logger.warning("Failed to capture grayscale frame from Pi AI Camera")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing grayscale frame: {e}")
            return None

    def get_detection_frame(self) -> Optional[np.ndarray]:
        """
        Get a frame in the appropriate format for detection (AI or OpenCV).
        
        Returns:
            Frame in detection format (YUV420 for AI, grayscale for OpenCV), or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame and metadata
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            
            if frame is not None:
                self._update_fps()
                
                # Return frame in detection format
                if self.camera_mode == "ai_detection":
                    # Return YUV420 frame for AI detection
                    return frame
                elif self.camera_mode == "opencv_detection":
                    # Convert to grayscale for OpenCV detection
                    import cv2
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                    elif len(frame.shape) == 3 and frame.shape[2] == 3:
                        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    else:
                        return frame
                else:
                    # Normal video mode - return BGR for general use
                    import cv2
                    if len(frame.shape) == 3 and frame.shape[2] == 4:
                        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    else:
                        return frame
            else:
                self.logger.warning("Failed to capture detection frame from Pi AI Camera")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing detection frame: {e}")
            return None
    
    def get_frame_grayscale_high_res(self, target_resolution: Optional[Tuple[int, int]] = None) -> Optional[np.ndarray]:
        """
        Get a high-resolution grayscale frame from the camera.
        
        This method temporarily switches to a higher resolution for grayscale capture,
        then converts to grayscale. This provides better detail for tensor/neural network
        processing while still being memory efficient.
        
        Args:
            target_resolution: Target resolution (width, height). If None, uses 1280x960.
        
        Returns:
            High-resolution grayscale frame as numpy array, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        if target_resolution is None:
            target_resolution = (1280, 960)  # 2x the current resolution
        
        try:
            # Store current resolution
            current_resolution = self.target_resolution
            
            # Temporarily set higher resolution
            self.logger.info(f"Temporarily switching to high-res grayscale: {target_resolution[0]}x{target_resolution[1]}")
            
            # Create high-res configuration
            config = self.picam2.create_preview_configuration(
                main={"size": target_resolution},
                controls={"FrameRate": self.intrinsics.inference_rate}, 
                buffer_count=12
            )
            
            # Restart camera with high-res config
            self.picam2.stop()
            self.picam2.start(config, show_preview=False)  # No preview for performance
            
            # Capture high-res frame
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            
            if frame is not None:
                self._update_fps()
                
                # Convert to grayscale
                import cv2
                if len(frame.shape) == 3:
                    if frame.shape[2] == 4:  # XBGR (Pi AI camera format)
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                    elif frame.shape[2] == 3:  # BGR
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    else:
                        gray_frame = frame[:, :, 0]
                else:
                    gray_frame = frame
                
                # Restore original resolution
                self.logger.info(f"Restoring original resolution: {current_resolution[0]}x{current_resolution[1]}")
                original_config = self.picam2.create_preview_configuration(
                    main={"size": current_resolution},
                    controls={"FrameRate": self.intrinsics.inference_rate}, 
                    buffer_count=12
                )
                
                self.picam2.stop()
                self.picam2.start(original_config, show_preview=True)
                
                return gray_frame
            else:
                self.logger.warning("Failed to capture high-res grayscale frame")
                # Restore original resolution even on failure
                original_config = self.picam2.create_preview_configuration(
                    main={"size": current_resolution},
                    controls={"FrameRate": self.intrinsics.inference_rate}, 
                    buffer_count=12
                )
                self.picam2.stop()
                self.picam2.start(original_config, show_preview=True)
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing high-res grayscale frame: {e}")
            # Try to restore original resolution on error
            try:
                original_config = self.picam2.create_preview_configuration(
                    main={"size": current_resolution},
                    controls={"FrameRate": self.intrinsics.inference_rate}, 
                    buffer_count=12
                )
                self.picam2.stop()
                self.picam2.start(original_config, show_preview=True)
            except Exception as restore_error:
                self.logger.error(f"Failed to restore original resolution: {restore_error}")
            return None
    
    def get_frame_grayscale_high_res_display(self, target_resolution: Optional[Tuple[int, int]] = None) -> Optional[np.ndarray]:
        """
        Get a high-resolution grayscale frame from the camera for display purposes.
        
        This method temporarily switches to high resolution, captures a frame,
        and keeps the camera at high resolution for display.
        
        Args:
            target_resolution: Target resolution (width, height). If None, uses 1280x960.
            
        Returns:
            Grayscale frame at high resolution, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        if target_resolution is None:
            target_resolution = (1280, 960)  # Default to 2x resolution
            
        try:
            self.logger.info(f"Switching to high-res grayscale display: {target_resolution[0]}x{target_resolution[1]}")
            config = self.picam2.create_preview_configuration(
                main={"size": target_resolution},
                controls={"FrameRate": self.inference_rate},
                buffer_count=12
            )
            self.picam2.stop()
            self.picam2.start(config, show_preview=True)
            
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            if frame is not None:
                self._update_fps()
                import cv2
                if len(frame.shape) == 3:
                    if frame.shape[2] == 4:  # XBGR (Pi AI camera format)
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                    elif frame.shape[2] == 3:  # BGR
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    else:
                        gray_frame = frame[:, :, 0]
                else:
                    gray_frame = frame
                
                # Update the display resolution
                self.display_resolution = target_resolution
                self.logger.info(f"High-res grayscale display active: {target_resolution[0]}x{target_resolution[1]}")
                return gray_frame
            else:
                self.logger.warning("Failed to capture high-res grayscale display frame")
                return None
        except Exception as e:
            self.logger.error(f"Error capturing high-res grayscale display frame: {e}")
            return None
    
    def get_detections(self) -> List[PersonDetection]:
        """
        Get current detections from the last frame.
        
        Returns:
            List of PersonDetection objects
        """
        if self.last_metadata is None:
            return []
        
        try:
            detections = self._parse_detections(self.last_metadata)
            return detections
        except Exception as e:
            self.logger.error(f"Error parsing detections: {e}")
            return []
    
    def _parse_detections(self, metadata: Dict[str, Any]) -> List[PersonDetection]:
        """Parse detection results from metadata."""
        try:
            # Get outputs from IMX500
            np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
            if np_outputs is None:
                return self.last_detections
            
            input_w, input_h = self.imx500.get_input_size()
            
            # Parse based on postprocessing type
            if self.intrinsics.postprocess == "nanodet":
                boxes, scores, classes = postprocess_nanodet_detection(
                    outputs=np_outputs[0], 
                    conf=self.confidence_threshold, 
                    iou_thres=self.iou_threshold,
                    max_out_dets=self.max_detections
                )[0]
                
                from picamera2.devices.imx500.postprocess import scale_boxes
                boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
            else:
                boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
                
                if self.intrinsics.bbox_normalization:
                    boxes = boxes / input_h
                
                if self.intrinsics.bbox_order == "xy":
                    boxes = boxes[:, [1, 0, 3, 2]]
                
                boxes = np.array_split(boxes, 4, axis=1)
                boxes = zip(*boxes)
            
            # Convert to PersonDetection objects
            detections = []
            labels = self._get_labels()
            
            for box, score, category in zip(boxes, scores, classes):
                if score > self.confidence_threshold:
                    # Convert box to (x, y, w, h) format
                    if isinstance(box, (list, tuple)):
                        x, y, w, h = box
                    else:
                        x, y, w, h = box[0], box[1], box[2] - box[0], box[3] - box[1]
                    
                    # Ensure positive dimensions
                    x, y = max(0, int(x)), max(0, int(y))
                    w, h = max(1, int(w)), max(1, int(h))
                    
                    category_name = labels[int(category)] if int(category) < len(labels) else "unknown"
                    
                    detection = PersonDetection(
                        bbox=(x, y, w, h),
                        confidence=float(score),
                        category=category_name
                    )
                    detections.append(detection)
            
            self.last_detections = detections
            return detections
            
        except Exception as e:
            self.logger.error(f"Error parsing detections: {e}")
            return self.last_detections
    
    @lru_cache
    def _get_labels(self) -> List[str]:
        """Get detection labels."""
        if self.intrinsics.labels is None:
            return ["person"]
        
        if self.intrinsics.ignore_dash_labels:
            return [label for label in self.intrinsics.labels if label and label != "-"]
        
        return self.intrinsics.labels
    
    def set_resolution(self, width: int, height: int) -> None:
        """
        Set target resolution for camera.
        
        Args:
            width: Target width in pixels
            height: Target height in pixels
        """
        if self.is_running:
            self.logger.warning("Cannot change resolution while camera is running")
            return
        
        # Validate resolution
        supported_resolutions = [
            (640, 480),    # Standard
            (1280, 720),   # HD
            (2028, 1520),  # IMX500 30fps mode
        ]
        
        if (width, height) not in supported_resolutions:
            self.logger.warning(f"Resolution {width}x{height} may not be supported")
        
        self.target_resolution = (width, height)
        self.logger.info(f"Resolution set to {width}x{height}")
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current camera resolution.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        if self.picam2 is None:
            return self.target_resolution  # Return target resolution
        
        try:
            # Get actual resolution from camera
            width = self.picam2.camera_configuration()["main"]["size"][0]
            height = self.picam2.camera_configuration()["main"]["size"][1]
            return (width, height)
        except Exception:
            return self.target_resolution  # Return target resolution
    
    def get_fps(self) -> float:
        """
        Get current camera FPS.
        
        Returns:
            Current FPS as float
        """
        return self.current_fps
    
    def is_available(self) -> bool:
        """
        Check if camera is available and working.
        
        Returns:
            True if camera is available, False otherwise
        """
        return (PICAMERA2_AVAILABLE and 
                self.picam2 is not None and 
                self.is_running)
    
    def stop(self) -> None:
        """Stop camera capture and release resources."""
        try:
            if self.picam2 is not None:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
            
            self.is_running = False
            self.logger.info("Pi AI Camera stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Pi AI Camera: {e}")
    
    def _update_fps(self) -> None:
        """Update FPS calculation."""
        self.fps_counter += 1
        current_time = time.time()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:  # Update FPS every second
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        if self.intrinsics is None:
            return {}
        
        return {
            "model_path": self.model_path,
            "task": self.intrinsics.task,
            "labels": self.intrinsics.labels,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "max_detections": self.max_detections,
            "inference_rate": self.inference_rate
        }

    def get_camera_mode_info(self) -> Dict[str, Any]:
        """
        Get information about the current camera mode.
        
        Returns:
            Dictionary with camera mode information
        """
        if self.camera_mode not in PI_AI_CAMERA_CONFIG["camera_modes"]:
            return {}
        
        mode_config = PI_AI_CAMERA_CONFIG["camera_modes"][self.camera_mode]
        return {
            "camera_mode": self.camera_mode,
            "detection": {
                "resolution": self.detection_resolution,
                "format": self.detection_format,
                "purpose": mode_config["detection"]["purpose"]
            },
            "display": {
                "resolution": self.display_resolution,
                "format": self.display_format,
                "purpose": mode_config["display"]["purpose"]
            },
            "memory_mb_per_frame": mode_config["memory_mb_per_frame"]
        }
    
    def get_optimal_detection_frame(self) -> Optional[np.ndarray]:
        """
        Get the optimal frame for AI detection (grayscale at detection resolution).
        
        Returns:
            Optimal detection frame as numpy array, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Use detection optimal resolution for best AI performance
            return self.get_frame_grayscale_high_res(target_resolution=self.detection_resolution)
            
        except Exception as e:
            self.logger.error(f"Error getting optimal detection frame: {e}")
            return None
    
    def get_optimal_display_frame(self) -> Optional[np.ndarray]:
        """
        Get the optimal frame for display (color at display resolution).
        
        Returns:
            Optimal display frame as numpy array, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Use display optimal resolution for best visual quality
            return self.get_frame()
            
        except Exception as e:
            self.logger.error(f"Error getting optimal display frame: {e}")
            return None 