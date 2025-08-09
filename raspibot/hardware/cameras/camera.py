"""Universal Camera implementation using Picamera2 - auto-detects Pi AI, Pi, or USB cameras."""

import os
import time
from typing import Optional, Tuple, List, Dict, Any
from functools import lru_cache
import cv2

try:
    from picamera2 import Picamera2, Preview, MappedArray
    from picamera2.devices import IMX500
    from picamera2.devices.imx500 import (
        NetworkIntrinsics,
        postprocess_nanodet_detection,
    )

    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from raspibot.settings.config import *
from raspibot.utils.logging_config import setup_logging

display_modes = {
    "screen": Preview.QTGL,  # hardware accelerated
    "connect": Preview.QT,  # slow
    "ssh": Preview.DRM,  # no desktop running
    "none": Preview.NULL,
}


class Camera:
    """Universal camera class - auto-detects Pi AI, Pi, or USB cameras."""

    def __init__(
        self,
        camera_device_id: Optional[int] = None,
        camera_resolution: Optional[Tuple[int, int]] = None,
        display_resolution: Optional[Tuple[int, int]] = None,
        display_position: Optional[Tuple[int, int]] = None,
        display_mode: Optional[str] = None,
    ) -> None:
        """
        Initialize Universal Camera.

        Args:
            camera_device_id: Camera device ID (auto-select if None)
            camera_resolution: Camera resolution (from config if None)
            display_resolution: Display resolution (from config if None)
            display_position: Display position (from config if None)
            display_mode: Display mode ("screen", "connect", "ssh", "none")
        """
        if not PICAMERA2_AVAILABLE:
            raise ImportError(
                "picamera2 not available. Camera requires picamera2 library."
            )

        self.logger = setup_logging(__name__)

        # Load defaults from config
        self._load_config_defaults(
            camera_device_id,
            camera_resolution,
            display_resolution,
            display_position,
            display_mode,
        )

        # Auto-detect camera type and initialize
        self.camera_type = self._detect_camera_type()
        self.camera: Optional[Picamera2] = None
        self.is_running = False
        self.is_detecting = False

        # Initialize hardware based on detected type
        self._initialize_hardware()

        # Setup AI detection if pi_ai camera
        if self.camera_type == "pi_ai":
            self._setup_ai_detection()

        self.logger.info(
            f"Camera initialized: {self.camera_type} camera {self.camera_device_id}"
        )

    def _load_config_defaults(
        self,
        camera_device_id,
        camera_resolution,
        display_resolution,
        display_position,
        display_mode,
    ) -> None:
        """Load settings from config.py."""
        self.camera_resolution = camera_resolution or CAMERA_RESOLUTION
        self.display_resolution = display_resolution or CAMERA_DISPLAY_RESOLUTION
        self.display_position = display_position or CAMERA_DISPLAY_POSITION
        self.display_mode = display_mode or PI_DISPLAY_MODE
        self.camera_device_id = camera_device_id

        # AI-specific settings (only used if AI camera detected)
        self.confidence_threshold = AI_DETECTION_THRESHOLD
        self.iou_threshold = AI_IOU_THRESHOLD
        self.max_detections = AI_MAX_DETECTIONS
        self.inference_frame_rate = AI_INFERERENCE_FRAME_RATE

        # Setup display environment
        self._setup_display_environment()

        self.logger.info(f"Camera resolution: {self.camera_resolution}")
        self.logger.info(f"Display: {self.display_resolution}")

    def _setup_display_environment(self) -> None:
        """Handle display environment variables."""
        if self.display_mode == "connect":
            os.environ["DISPLAY"] = ":0"  # for headless displays
            os.environ["QT_QPA_PLATFORM"] = "wayland"

    def _detect_camera_type(self) -> str:
        """Single method to detect camera type from Picamera2.global_camera_info()."""
        camera_info = Picamera2.global_camera_info()

        target_camera = None
        first_pi_ai = None
        first_pi = None
        first_usb = None

        # Single pass to find cameras by priority: pi_ai > pi > usb
        for info in camera_info:
            model = info.get("Model", "").lower()
            camera_id = info.get("Id", "").lower()

            # Check for specific camera ID match
            if (
                self.camera_device_id is not None
                and info.get("Num") == self.camera_device_id
            ):
                target_camera = info
                break

            # Categorize cameras by type for auto-selection
            if "imx500" in model:
                if first_pi_ai is None:
                    first_pi_ai = info
            elif (
                ("imx" in model or "pi" in model)
                and "uvc" not in model
                and "usb" not in camera_id
            ):
                if first_pi is None:
                    first_pi = info
            elif "uvc" in model or "usb" in camera_id:
                if first_usb is None:
                    first_usb = info

        # Select camera based on what we found
        if target_camera:
            selected_camera = target_camera
            self.camera_device_id = selected_camera.get("Num")
        else:
            # Auto-select by priority: pi_ai > pi > usb
            if first_pi_ai:
                selected_camera = first_pi_ai
            elif first_pi:
                selected_camera = first_pi
            elif first_usb:
                selected_camera = first_usb
            else:
                raise RuntimeError("No compatible cameras found")

            self.camera_device_id = selected_camera.get("Num")

        # Determine camera type from selected camera
        model = selected_camera.get("Model", "").lower()
        camera_id = selected_camera.get("Id", "").lower()

        if "imx500" in model:
            camera_type = "pi_ai"
        elif (
            ("imx" in model or "pi" in model)
            and "uvc" not in model
            and "usb" not in camera_id
        ):
            camera_type = "pi"
        elif "uvc" in model or "usb" in camera_id:
            camera_type = "usb"

        else:
            raise RuntimeError(f"Unknown camera type: {model}")

        self.logger.info(
            f"Detected {camera_type} camera: {selected_camera.get('Model', 'Unknown')}"
        )
        return camera_type

    def _initialize_hardware(self) -> None:
        """Initialize camera hardware based on detected type."""
        try:
            self.camera = Picamera2(self.camera_device_id)
            self.logger.info(
                f"{self.camera_type.title()} Camera hardware initialized successfully"
            )
        except Exception as e:
            self.logger.error(
                f"Camera._initialize_hardware failed: {type(e).__name__}: {e}"
            )
            raise

    def _setup_ai_detection(self) -> None:
        """Initialize IMX500 AI processing (only for pi_ai cameras)."""
        try:
            self.imx500 = IMX500(AI_DEFAULT_VISION_MODEL)
            self.intrinsics = self.imx500.network_intrinsics

            if not self.intrinsics:
                self.intrinsics = NetworkIntrinsics()
                self.intrinsics.task = "object detection"

            self.intrinsics.confidence_threshold = self.confidence_threshold
            self.intrinsics.iou_threshold = self.iou_threshold
            self.intrinsics.max_detections = self.max_detections
            self.intrinsics.inference_rate = self.inference_frame_rate

            # Initialize detection tracking
            self.detections = []
            self.tracked_objects = []
            self.fps = 0.0

            self.logger.info("AI detection initialized successfully")
        except Exception as e:
            self.logger.error(
                f"Camera._setup_ai_detection failed: {type(e).__name__}: {e}"
            )
            raise

    def start(self) -> bool:
        """Universal start method - works for all camera types."""
        try:
            self.camera.post_callback = self.annotate_screen
            self.logger.info("Starting Preview")
            self.camera.start_preview(
                display_modes[self.display_mode],
                x=self.display_position[0],
                y=self.display_position[1],
                width=self.display_resolution[0],
                height=self.display_resolution[1],
            )

            self.logger.info("Starting Camera")

            # Configure camera based on type
            if self.camera_type == "pi_ai":
                self.config = self.camera.create_preview_configuration(
                    controls={"FrameRate": self.intrinsics.inference_rate},
                    buffer_count=12,
                )
                self.config["main"]["size"] = self.camera_resolution
                self.imx500.show_network_fw_progress_bar()
            else:
                self.config = self.camera.create_preview_configuration(
                    main={"size": self.camera_resolution}
                )

            self.camera.start(self.config)

            # AI-specific setup
            if self.camera_type == "pi_ai" and self.intrinsics.preserve_aspect_ratio:
                self.imx500.set_auto_aspect_ratio()

            self.is_running = True
            self.logger.info(f"{self.camera_type.title()} Camera started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Camera.start failed: {type(e).__name__}: {e}")
            return False

    def detect(self, callback=None):
        """Universal detect loop with optional callback.

        Args:
            callback: Optional function to call in the loop for processing
        """
        self.is_detecting = True
        tracked_objects = []

        while self.is_detecting:
            # Call optional callback for processing
            if callback:
                callback(self)

            # AI-specific detection processing
            if self.camera_type == "pi_ai":
                self._process_ai_detections(tracked_objects)

            # Small delay to prevent busy waiting
            time.sleep(0.1)

            # Stop if preview object no longer exists (e.g when closed)
            if not self.camera._preview:
                self.is_detecting = False
                self.logger.info("Preview closed")
                break

        self.stop()

    def _process_ai_detections(self, tracked_objects):
        """Process AI detections, apply NMS, update tracking (only for pi_ai cameras)."""
        try:
            metadata = self.camera.capture_metadata()
            self.fps = self._calculate_fps(metadata)
            boxes, scores, classes = self._get_detections(metadata)

            if boxes is None:
                return

            # Convert raw detections to dictionaries
            raw_detections = self._convert_detection_to_dict(
                boxes, scores, classes, metadata
            )
            if not raw_detections:
                return

            # Filter by confidence threshold
            confidence_filtered = [
                d for d in raw_detections if d["score"] > self.confidence_threshold
            ]
            if not confidence_filtered:
                return

            # Apply NMS and update tracking
            self.detections = self._apply_nms(
                confidence_filtered, iou_threshold=NMS_IOU_THRESHOLD
            )
            self.tracked_objects = self._associate_detections_to_tracks(
                self.detections, tracked_objects, iou_threshold=TRACKING_IOU_THRESHOLD
            )

        except Exception as e:
            self.logger.error(f"AI detection processing failed: {e}")

    def stop(self):
        """Universal stop method."""
        if self.camera is not None and self.is_running:
            self.is_detecting = False
            self.camera.stop()

    def shutdown(self) -> None:
        """Universal cleanup method."""
        try:
            if self.camera is not None:
                self.is_detecting = False
                self.camera.stop()
                self.camera.close()

                self.is_running = False
                self.camera = None

            self.logger.info(f"{self.camera_type.title()} Camera stopped")

        except Exception as e:
            self.logger.error(f"Camera.shutdown failed: {type(e).__name__}: {e}")

    # AI Detection Helper Methods (only used for pi_ai cameras)

    @lru_cache
    def _get_labels(self) -> List[str]:
        """Get detection labels for AI camera."""
        if self.intrinsics.labels is None:
            return ["person"]

        if self.intrinsics.ignore_dash_labels:
            return [label for label in self.intrinsics.labels if label and label != "-"]

        return self.intrinsics.labels

    def _calculate_fps(self, metadata: Dict[str, Any]) -> float:
        """Calculate FPS from metadata."""
        return 1000000 / (metadata["FrameDuration"])

    def _get_detections(self, metadata: Dict[str, Any]) -> Tuple:
        """Get detections from AI camera."""
        np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
        input_w, input_h = self.imx500.get_input_size()

        if np_outputs is None:
            return None, None, None

        if self.intrinsics.postprocess == "nanodet":
            boxes, scores, classes = postprocess_nanodet_detection(
                outputs=np_outputs[0],
                conf=self.confidence_threshold,
                iou_thres=self.iou_threshold,
                max_out_dets=self.max_detections,
            )
            from picamera2.devices.imx500.postprocess import scale_boxes

            boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
        else:
            boxes, scores, classes = (
                np_outputs[0][0],
                np_outputs[1][0],
                np_outputs[2][0],
            )
            if self.intrinsics.bbox_normalization:
                boxes = boxes / input_h
            if self.intrinsics.bbox_order == "xy":
                boxes = boxes[:, [1, 0, 3, 2]]
            boxes = list(zip(*[boxes[:, i] for i in range(4)]))

        return boxes, scores, classes

    def _convert_detection_to_dict(
        self, boxes, scores, classes, metadata
    ) -> List[Dict[str, Any]]:
        """Convert detection data to dictionaries."""
        detections = []
        for i, (box, score, category) in enumerate(zip(boxes, scores, classes)):
            converted_box = self.imx500.convert_inference_coords(
                box, metadata, self.camera
            )
            detection_dict = {
                "detection_index": i,
                "box": converted_box,
                "score": score,
                "category": category,
                "label": self._get_labels()[int(category)],
            }
            detections.append(detection_dict)
        return detections

    def _calculate_iou(self, box1: List[int], box2: List[int]) -> float:
        """Calculate Intersection over Union."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)

        if left >= right or top >= bottom:
            return 0.0

        intersection_area = (right - left) * (bottom - top)
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0

    def _filter_valid_boxes(
        self, detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter out boxes that are too large or too small."""
        if not detections:
            return []

        camera_width, camera_height = self.camera_resolution
        total_area = camera_width * camera_height
        max_area = total_area * 0.8
        min_area = 100

        valid_detections = []
        for detection in detections:
            x, y, w, h = detection["box"]
            area = w * h

            if min_area <= area <= max_area:
                aspect_ratio = w / h if h > 0 else 0
                if 0.1 <= aspect_ratio <= 10.0:
                    valid_detections.append(detection)

        return valid_detections

    def _apply_nms(
        self, detections: List[Dict[str, Any]], iou_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Apply Non-Maximum Suppression."""
        if not detections:
            return []

        valid_detections = self._filter_valid_boxes(detections)
        if not valid_detections:
            return []

        # Group by label and apply NMS
        label_groups = {}
        for detection in valid_detections:
            label = detection["label"]
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(detection)

        result = []
        for label, group_detections in label_groups.items():
            if len(group_detections) == 1:
                result.append(group_detections[0])
                continue

            # Sort by confidence and apply greedy NMS
            sorted_detections = sorted(
                group_detections, key=lambda d: d["score"], reverse=True
            )
            kept_detections = []

            while sorted_detections:
                current = sorted_detections.pop(0)
                kept_detections.append(current)

                remaining = []
                for detection in sorted_detections:
                    if (
                        self._calculate_iou(current["box"], detection["box"])
                        < iou_threshold
                    ):
                        remaining.append(detection)

                sorted_detections = remaining

            result.extend(kept_detections)

        return result

    def _associate_detections_to_tracks(
        self,
        detections: List[Dict[str, Any]],
        tracked_objects: List[Dict[str, Any]],
        iou_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Associate current detections with existing tracked objects."""
        # Mark all tracked objects as not seen
        for tracked_object in tracked_objects:
            tracked_object["seen_this_frame"] = False

        unmatched_detections = []

        # Try to match detections with existing tracks
        for detection in detections:
            best_match = None
            best_iou = 0.0

            for tracked_object in tracked_objects:
                if (
                    not tracked_object.get("last_detection")
                    or tracked_object["label"] != detection["label"]
                    or tracked_object["seen_this_frame"]
                ):
                    continue

                iou = self._calculate_iou(
                    detection["box"], tracked_object["last_detection"]["box"]
                )
                if iou > iou_threshold and iou > best_iou:
                    best_match = tracked_object
                    best_iou = iou

            if best_match:
                best_match["last_detection"] = detection
                best_match["seen_this_frame"] = True
                best_match["seen_count"] = best_match.get("seen_count", 0) + 1
                best_match["frames_missing"] = 0
            else:
                unmatched_detections.append(detection)

        # Create new tracks for unmatched detections
        for detection in unmatched_detections:
            new_track = {
                "id": len(tracked_objects),
                "last_detection": detection,
                "label": detection["label"],
                "seen_this_frame": True,
                "seen_count": 1,
                "frames_missing": 0,
            }
            tracked_objects.append(new_track)

        # Remove old tracks that haven't been seen for too long
        max_frames_missing = 25
        updated_tracks = []

        for tracked_object in tracked_objects:
            if tracked_object["seen_this_frame"]:
                # Keep tracks that were seen this frame
                updated_tracks.append(tracked_object)
            elif tracked_object["frames_missing"] < max_frames_missing:
                # Keep tracks that are still within the missing frame limit
                tracked_object["frames_missing"] += 1
                updated_tracks.append(tracked_object)
            # else: drop tracks that have been missing too long

        return updated_tracks

    def add_screen_text(
        self, m: MappedArray, text: str, x: int, y: int
    ) -> Tuple[int, int, int, int]:
        """add test to screen and return new x and y position
        - m is the mapped array
        - text is the text to add
        - x is the x position
        - y is the y position
        - returns new x and y position and text width and height
        """
        (text_width, text_height), baseline = cv2.getTextSize(
            text,
            DEFAULT_SCREEN_FONT,
            DEFAULT_SCREEN_FONT_SIZE,
            DEFAULT_SCREEN_FONT_THIKCNESS,
        )
        cv2.putText(
            m.array,
            text,
            (x, y),
            DEFAULT_SCREEN_FONT,
            DEFAULT_SCREEN_FONT_SIZE,
            DEFAULT_SCREEN_FONT_COLOUR,
            DEFAULT_SCREEN_FONT_THIKCNESS,
        )
        new_x = x + text_width + 10
        new_y = y + text_height + 10
        return new_x, new_y, text_width, text_height

    def draw_objects(self, m: MappedArray, detections: List[Dict[str, Any]]) -> None:
        """draw objects on screen
        - m is the mapped array
        - detections is the list of detections
        """
        for index, detection in enumerate(detections):
            x, y, w, h = detection["box"]
            label = f"{index}: {detection['label']} ({detection['score']:.2f})"
            # Create a copy of the array to draw the background with opacity
            overlay = m.array.copy()
            # Draw the background rectangle on the overlay
            (text_width, text_height), baseline = cv2.getTextSize(
                label,
                DEFAULT_SCREEN_FONT,
                DEFAULT_SCREEN_FONT_SIZE,
                DEFAULT_SCREEN_FONT_THIKCNESS,
            )
            text_x = x + 5
            text_y = y + 10
            cv2.rectangle(
                overlay,
                (text_x, text_y + 10 - text_height),
                (text_x + text_width, text_y + baseline),
                (0, 0, 0),
                cv2.FILLED,
            )
            alpha = 0.6
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)
            self.add_screen_text(m, label, x + 5, y + 15)
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)

    def annotate_screen(
        self, request, stream: str = "main", start_x: int = 10, start_y: int = 30
    ) -> None:
        """annotate screen. The overall annotation of any screen items.
        - request is the request object
        - stream is the stream name
        - start_x is the x position
        - start_y is the y position
        """
        with MappedArray(request, stream) as m:
            new_x, new_y, text_width, text_height = self.add_screen_text(
                m, f"FPS: {self.fps:.2f}", start_x, start_y
            )
            if self.camera == "pi_ai":
                start_x, new_y, text_width, text_height = self.add_screen_text(
                    m, f"Detections: {len(self.detections)}", new_x, new_y
                )
                self.draw_objects(m, self.detections)


if __name__ == "__main__":
    try:
        # Initialize camera in AI mode (auto-detects best available)
        camera = Camera()

        # Start the camera
        if camera.start():
            print(
                f"{camera.camera_type.title()} camera started successfully. Close the preview window to stop."
            )

            # Run the detect loop
            if camera.camera_type == "pi_ai":
                print("Running in AI detection mode...")
            else:
                print("Running in display-only mode...")

            camera.detect()

        else:
            print("Failed to start camera")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Cleanup
        if "camera" in locals():
            camera.shutdown()
            print("Camera stopped")
