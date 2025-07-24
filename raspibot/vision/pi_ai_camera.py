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
                 inference_rate: Optional[int] = None):
        """
        Initialize Pi AI camera.
        
        Args:
            model_path: Path to the IMX500 model file
            confidence_threshold: Detection confidence threshold
            iou_threshold: IoU threshold for NMS
            max_detections: Maximum number of detections
            inference_rate: Target inference FPS
        """
        if not PICAMERA2_AVAILABLE:
            raise ImportError("picamera2 not available. Pi AI camera requires picamera2 library.")
        
        self.logger = setup_logging(__name__)
        
        # Use configuration defaults if not provided
        config = PI_AI_CAMERA_CONFIG
        self.model_path = model_path or config["default_model"]
        self.confidence_threshold = confidence_threshold or config["people_detection"]["confidence_threshold"]
        self.iou_threshold = iou_threshold or config["people_detection"]["iou_threshold"]
        self.max_detections = max_detections or config["people_detection"]["max_detections"]
        self.inference_rate = inference_rate or config["people_detection"]["inference_rate"]
        
        # Initialize components
        self.imx500 = None
        self.picam2 = None
        self.intrinsics = None
        self.is_running = False
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        
        # Detection tracking
        self.last_detections: List[PersonDetection] = []
        self.last_metadata = None
        
        self.logger.info(f"Initializing Pi AI Camera with model: {self.model_path}")
        self._initialize_hardware()
    
    def _initialize_hardware(self) -> None:
        """Initialize IMX500 hardware and camera."""
        try:
            # Initialize IMX500 with model
            self.imx500 = IMX500(self.model_path)
            self.intrinsics = self.imx500.network_intrinsics
            
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
            
            self.logger.info("Starting Pi AI Camera capture")
            
            # Create preview configuration
            config = self.picam2.create_preview_configuration(
                controls={"FrameRate": self.intrinsics.inference_rate}, 
                buffer_count=12
            )
            
            # Show network firmware progress
            self.imx500.show_network_fw_progress_bar()
            
            # Start camera
            self.picam2.start(config, show_preview=True)
            
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
        Get a single frame from the camera.
        
        Returns:
            Frame as numpy array, or None if failed
        """
        if not self.is_running or self.picam2 is None:
            return None
        
        try:
            # Capture frame and metadata
            frame = self.picam2.capture_array()
            self.last_metadata = self.picam2.capture_metadata()
            
            if frame is not None:
                self._update_fps()
                return frame
            else:
                self.logger.warning("Failed to capture frame from Pi AI Camera")
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
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
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get current camera resolution.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        if self.picam2 is None:
            return (640, 480)  # Default resolution
        
        try:
            # Get actual resolution from camera
            width = self.picam2.camera_configuration()["main"]["size"][0]
            height = self.picam2.camera_configuration()["main"]["size"][1]
            return (width, height)
        except Exception:
            return (640, 480)  # Fallback resolution
    
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