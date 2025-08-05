"""Pi AI Camera implementation using IMX500 hardware acceleration.

This class is used to capture images from the camera and perform object detection.
It uses the IMX500 hardware acceleration to perform the detection.
It uses the Picamera2 library to capture the images and perform the detection.
It uses the OpenCV library to draw the detections on the screen.
Based on the Sony IMX500 camera example code .
"""

from socket import AI_ADDRCONFIG
import time
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from functools import lru_cache
from enum import Enum
from collections import Counter
import cv2


try:
    from picamera2 import Picamera2, Preview, MappedArray
    from picamera2.devices import IMX500
    from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from .camera_template import CameraTemplate
from raspibot.settings.config import *
from raspibot.utils.logging_config import setup_logging

display_modes = {
    "screen": Preview.QTGL, # hardware accelerated
    "connect": Preview.QT, # slow
    "ssh": Preview.DRM, # no desktop running
    "none": Preview.NULL,
}


class PiAICamera(CameraTemplate):
    """Pi AI Camera implementation using IMX500 hardware acceleration. 
    Based on the Sony IMX500 camera example code. 
    https://github.com/raspberrypi/picamera2/blob/main/examples/imx500/imx500_object_detection_demo.py

    Core changes:
    - breking up opencv display annotation
    - Dependant on cam_obj.post_callback to annotate to screen
    - deopendant on _init_ kwargs or config.py to set constants
    """
    
    def __init__(self, 
                camera_device_id: Optional[int] = None,
                camera_resolution: Optional[Tuple[int, int]] = None,
                display_resolution: Optional[Tuple[int, int]] = None,
                display_position: Optional[Tuple[int, int]] = None,
                model_path: Optional[str] = None,
                confidence_threshold: Optional[float] = None,
                iou_threshold: Optional[float] = None,
                max_detections: Optional[int] = None,
                inference_frame_rate: Optional[int] = None,
                display_mode: Optional[str] = None, # in case, change config to set default
                )->None:


        """
        Initialize Pi AI Camera.
        
        Args:
        -   camera_device_id: (int) Camera device ID
        -   camera_resolution: (Tuple[int, int]) Camera resolution
        -   display_resolution: (Tuple[int, int]) Display resolution
        -   display_position: (Tuple[int, int]) Display position
        -   model_path: (str) Model path
        -   confidence_threshold: (float) Detection confidence threshold (0.0-1.0)
        -   iou_threshold: (float) IoU threshold for NMS (0.0-1.0)
        -   max_detections: (int) Maximum number of detections to return
        -   inference_framerate: (int) Inference rate in FPS
        -   display_mode: (str) Display mode ("screen", "connect", "ssh", "none")
        """
        
        if not PICAMERA2_AVAILABLE:
            raise ImportError("picamera2 not available. Pi AI camera requires picamera2 library.")
        
        self.logger = setup_logging(__name__)

        
        # a kwarg overrides the default settings in config.py
        self.model_path = model_path or AI_DEFAULT_VISION_MODEL
        self.confidence_threshold = confidence_threshold or AI_DETECTION_THRESHOLD
        self.iou_threshold = iou_threshold or AI_IOU_THRESHOLD
        self.max_detections = max_detections or AI_MAX_DETECTIONS
        self.inference_frame_rate = inference_frame_rate or AI_INFERERENCE_FRAME_RATE
        self.camera_resolution = camera_resolution or AI_CAMERA_RESOLUTION
        self.display_resolution = display_resolution or CAMERA_DISPLAY_RESOLUTION
        self.display_position = display_position or CAMERA_DISPLAY_POSITION
        self.camera_device_id = camera_device_id or AI_CAMERA_DEVICE_ID
        self.display_mode = display_mode or PI_DISPLAY_MODE
        self.detections = []
        self.is_detecting = False
        self.is_running = False
        self.tracked_objects = []

        print(PI_DISPLAY_MODE)
        print(display_mode)
        print(self.display_mode)

        # The camera preview uses QT which needs the correct settings for non direct connected screens
        if self.display_mode == "connect":
            # This may need adjusting for different displays other than direct
            os.environ['DISPLAY'] = ':0' # for headles displays
            os.environ['QT_QPA_PLATFORM'] = 'wayland'
        
        self.logger.info(f"Camera resolution: {self.camera_resolution}")
        self.logger.info(f"Display: {self.display_resolution}")
        
        self.fps = 0.0
        
        # Initialize hardware
        self._initialize_hardware()
    
    def _initialize_hardware(self) -> None:
        """Initialize IMX500 hardware and camera.
        - https://github.com/raspberrypi/imx500-models for models choice
        - creates three properties containing the camera, intrinsics, and imx500
        - configures camera
        """
        try:
            # https://github.com/raspberrypi/imx500-models to choose models
            self.imx500 = IMX500(self.model_path)
            self.intrinsics = self.imx500.network_intrinsics
            
            if not self.intrinsics:
                self.intrinsics = NetworkIntrinsics()
                self.intrinsics.task = "object detection"
            
            self.intrinsics.confidence_threshold = self.confidence_threshold
            self.intrinsics.iou_threshold = self.iou_threshold
            self.intrinsics.max_detections = self.max_detections
            self.intrinsics.inference_rate = self.inference_frame_rate
            
            self.camera = Picamera2(self.camera_device_id)
            self.logger.info("Pi AI Camera hardware initialized successfully")
            self.logger.info(f"Starting Pi AI Camera Configuring")
            
            self.config = self.camera.create_preview_configuration(controls={"FrameRate": self.intrinsics.inference_rate}, buffer_count=12)
            self.config['main']['size'] = self.camera_resolution
            self.imx500.show_network_fw_progress_bar()
        
            self.logger.info("Pi AI Camera hardware initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Pi AI Camera hardware: {e}")
            raise
    
    def start(self) -> bool:
        """
        Start camera capture.
        - Uses the seperate command to start preview instead of cam_obj.start(show_preview=True)
        
        Returns:
            True if camera started successfully, False otherwise.
        """
        try:
            print(self.display_mode)
            print(display_modes[self.display_mode])
            self.logger.info(f"Starting Preview")
            self.camera.start_preview(display_modes[self.display_mode],x=self.display_position[0],y=self.display_position[1],width=self.display_resolution[0],height=self.display_resolution[1]) 
            self.logger.info(f"Starting Camera")
            self.camera.start(self.config)
            if self.intrinsics.preserve_aspect_ratio:
                self.imx500.set_auto_aspect_ratio()
            
            # Log the actual configuration being applied
            self.logger.info(f"Camera config main size: {self.config['main']['size']}")
            self.logger.info(f"Camera config main format: {self.config['main']['format']}")
            self.logger.info(f"Camera resolution: {self.camera_resolution}")
            self.logger.info(f"Display resolution: {self.display_resolution}")
            
            # Log actual camera configuration after start
            try:
                actual_config = self.camera.camera_configuration()
                self.logger.info(f"Actual camera size after start: {actual_config['main']['size']}")
                self.logger.info(f"Actual camera format after start: {actual_config['main']['format']}")
            except Exception as e:
                self.logger.warning(f"Could not get actual camera config: {e}")
            
            self.is_running = True
            self.logger.info("Pi AI Camera started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting Pi AI Camera: {e}")
            return False

    def stop(self):
        if self.camera is not None and self.is_running:
            self.is_detecting = False
            self.camera.stop()


    def shutdown(self) -> None:
        """Stop camera capture and release resources.
        - ensures detection thread is stopped by setting self.dectecting to False
        """
        try:
            if self.camera is not None:
                self.is_detecting = False
                self.camera.stop()
                self.camera.close()
                
                self.is_running = False
                self.camera = None
            
            self.logger.info("Pi AI Camera stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Pi AI Camera: {e}")
    
    @lru_cache
    def get_labels(self) -> List[str]:
        """Get detection labels. So they can be used in detectiosn and display
        Labels can be loaded into intrinsics from external files. They often have dashes
        to denote groups. These will be ignored by default.

        """
        if self.intrinsics.labels is None:
            return ["person"]
        
        if self.intrinsics.ignore_dash_labels:
            return [label for label in self.intrinsics.labels if label and label != "-"]
        
        return self.intrinsics.labels

    def calculate_fps(self,metadata:Dict[str, Any]) -> float:   
        """Calculate FPS from metadata.
        - metadata is a dict containing the frame duration
        - FrameDuration is in microseconds
        - is cahcached as will not change in most uses
        """
        return 1000000/(metadata['FrameDuration'])

    def get_detections(self, metadata:Dict[str, Any]) -> Tuple[List[Tuple[int, int, int, int]], List[float], List[int]]:
        """Get detections from the camera. Returns boxes, scores, and classes.
        - meatadata comes from cam_obj.capture_metadata()
        - returns boxes, scores, and classes
        """
        np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
        input_w, input_h = self.imx500.get_input_size()
        if np_outputs is None:
            return None, None,None
        
        if self.intrinsics.postprocess == "nanodet":
            boxes, scores, classes = \
                postprocess_nanodet_detection(outputs=np_outputs[0], conf=self.confidence_threshold, iou_thres=self.iou_threshold,
                                            max_out_dets=self.max_detections)
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
        return boxes, scores, classes   

    def convert_detection_to_dict(self,boxes:List[Tuple[int, int, int, int]], scores:List[float], classes:List[int], metadata:Dict[str, Any]) -> List[Dict[str, Any]]:
        """ Converts the boxes, scores, and classes to a list of dictionaries.
        Uses zip to loop through as each key variable is a list and the list items from each for each element belong
        to the same element.
        """
        detections = []
        counter = 0 # enumerate fails when using zip so use counter
        for box, score, category in zip(boxes, scores, classes):
            converted_box = self.imx500.convert_inference_coords(box, metadata, self.camera)
            detection_dict = {
                'detection_index': counter,
                'box': converted_box,
                'score': score,
                'category': category,
                'label': self.get_labels()[int(category)]
            }
            detections.append(detection_dict)
            counter += 1
        return detections
        
    def is_similar(self,detection1:Dict[str, Any], detection2:Dict[str, Any], position_threshold:int=100, size_threshold:float=0.3)->bool:
        """
        Check if two face detections are similar enough to be considered the same person.
        """
        # Safety checks for None or invalid objects
        if detection1 is None or detection2 is None:
            #raise ValueError('one of the detections is none')
            return False
        
        # Check if objects have required properties
        required_keys = ['x', 'y', 'w', 'h']
        if not (len(detection1['box'])==4) or not (len(detection2['box'])==4):
            return False
        
        # Check for valid numeric values
        try:
            x_difference = max(int(detection1['box'][0]), int(detection2['box'][0])) -  min(int(detection1['box'][0]), int(detection2['box'][0]))
            y_difference = max(int(detection1['box'][1]), int(detection2['box'][1])) -  min(int(detection1['box'][1]), int(detection2['box'][1]))
        except (TypeError, ValueError) as e:
            return False
        
        size_similarity = min(detection1['box'][2], detection2['box'][2]) / max(detection1['box'][2], detection2['box'][2])
       
        result =  detection1['label'] == detection2['label'] and x_difference < position_threshold and y_difference < position_threshold and size_similarity > size_threshold
        if detection1['label'] == detection2['label'] and detection1['label'] == 'cat':
            #print(f"{detection1['label']},{detection2['label']},{x_difference},{y_difference},{size_similarity}",flush=True)
            #print(result,flush=True)
            pass
        return result
    
    def deduplicate_detections(self, detections: List[Dict[str, Any]], 
                          overlap_threshold: float = DETECTION_OVERLAP_THRESHOLD) -> List[Dict[str, Any]]:
        """Deduplicate object detections by removing contained boxes and high-overlap boxes.
        
        Args:
            detections: List of detection dicts with 'box' key containing [x, y, w, h]
            overlap_threshold: Overlap percentage threshold (0.0-1.0) for considering duplicates
            
        Returns:
            Filtered list of detections with duplicates removed
        """
        if not detections:
            return []
        
        # Group detections by label
        label_groups = {}
        for detection in detections:
            label = detection['label']
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(detection)
        
        # Process each label group separately
        result = []
        for label, group_detections in label_groups.items():
            if len(group_detections) == 1:
                result.append(group_detections[0])
                continue
                
            # Sort by area (smallest first) to prioritize smaller detections
            sorted_group = sorted(group_detections, key=lambda d: d['box'][2] * d['box'][3])
            kept_in_group = []
            
            for current in sorted_group:
                should_keep = True
                current_box = current['box']
                
                for kept in kept_in_group:
                    kept_box = kept['box']
                    
                    # Check containment
                    if self._is_contained(current_box, kept_box) or self._is_contained(kept_box, current_box):
                        should_keep = False
                        break
                    
                    # Check overlap
                    if self._overlap_percentage(current_box, kept_box) >= overlap_threshold:
                        should_keep = False
                        break
                
                if should_keep:
                    kept_in_group.append(current)
            
            result.extend(kept_in_group)
        
        return result


    def _is_contained(self, box1: List[int], box2: List[int]) -> bool:
        """Check if box1 is completely contained within box2."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        return (x1 >= x2 and y1 >= y2 and 
                x1 + w1 <= x2 + w2 and y1 + h1 <= y2 + h2)


    def _overlap_percentage(self, box1: List[int], box2: List[int]) -> float:
        """Calculate overlap percentage between two bounding boxes."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left >= right or top >= bottom:
            return 0.0
        
        intersection_area = (right - left) * (bottom - top)
        smaller_area = min(w1 * h1, w2 * h2)
        
        return intersection_area / smaller_area if smaller_area > 0 else 0.0

    def _clamp_box_to_frame1(self, box: List[int]) -> List[int]:
        """Clamp box coordinates to ensure they don't exceed frame boundaries.
        
        Args:
            box: [x, y, width, height] bounding box
            
        Returns:
            Clamped box coordinates that fit within display frame
        """
        x, y, w, h = box
        display_width, display_height = self.display_resolution  # 1280x720
        
        # Clamp x and y to frame boundaries
        x = max(0, min(x, display_width - 1))
        y = max(0, min(y, display_height - 1))
        
        # Clamp width and height to ensure box doesn't extend beyond frame
        w = min(w, display_width - x)
        h = min(h, display_height - y)
        
        return [x, y, w, h]

    def _is_contained1(self, box1: List[int], box2: List[int]) -> bool:
        """Check if box1 is completely contained within box2 with boundary clamping."""
        # Clamp both boxes to frame boundaries first
        x1, y1, w1, h1 = self._clamp_box_to_frame1(box1)
        x2, y2, w2, h2 = self._clamp_box_to_frame1(box2)
        
        # Now check containment with properly clamped boxes
        return (x1 >= x2 and y1 >= y2 and 
                x1 + w1 <= x2 + w2 and y1 + h1 <= y2 + h2)

    def _overlap_percentage1(self, box1: List[int], box2: List[int]) -> float:
        """Calculate overlap percentage using IoU (Intersection over Union) with boundary clamping."""
        # Clamp both boxes to frame boundaries first
        x1, y1, w1, h1 = self._clamp_box_to_frame1(box1)
        x2, y2, w2, h2 = self._clamp_box_to_frame1(box2)
        
        # Calculate intersection with clamped boxes
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

    def deduplicate_detections1(self, detections: List[Dict[str, Any]], 
                              overlap_threshold: float = 0.66) -> List[Dict[str, Any]]:
        """Deduplicate object detections using boundary clamping and IoU overlap calculation.
        
        Args:
            detections: List of detection dicts with 'box' key containing [x, y, w, h]
            overlap_threshold: IoU threshold (0.0-1.0) for considering duplicates
            
        Returns:
            Filtered list of detections with duplicates removed
        """
        if not detections:
            return []
        
        # Group detections by label
        label_groups = {}
        for detection in detections:
            label = detection['label']
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(detection)
        
        # Process each label group separately
        result = []
        for label, group_detections in label_groups.items():
            if len(group_detections) == 1:
                result.append(group_detections[0])
                continue
                
            # Sort by area (smallest first) to prioritize smaller detections
            sorted_group = sorted(group_detections, key=lambda d: d['box'][2] * d['box'][3])
            kept_in_group = []
            
            for current in sorted_group:
                should_keep = True
                current_box = current['box']
                
                for kept in kept_in_group:
                    kept_box = kept['box']
                    
                    # Check containment with boundary clamping
                    if self._is_contained1(current_box, kept_box) or self._is_contained1(kept_box, current_box):
                        should_keep = False
                        break
                    
                    # Check overlap using IoU
                    if self._overlap_percentage1(current_box, kept_box) >= overlap_threshold:
                        should_keep = False
                        break
                
                if should_keep:
                    kept_in_group.append(current)
            
            result.extend(kept_in_group)
        
        return result

    def track_detections(self,detections:List[Dict[str, Any]], tracked_objects:List[Dict[str, Any]], max_frames_missing:int=25, max_history:int=10)->List[Dict[str, Any]]:
        """
        Track detections across frames and assign IDs to similar objects.
        
        Args:
            detections: List of Detection objects from current frame
            tracked_objects: List of tracked objects from previous frames
            max_frames_missing: How many frames an object can be missing before being removed
            max_history: Maximum number of detections to store per tracked object
        
        Returns:
            Updated list of tracked objects
        """
        # Mark all tracked objects as not seen in this frame
        for tracked_object in tracked_objects:
            tracked_object['seen_this_frame'] = False

        detections = self.deduplicate_detections1(detections)
        
        # Try to match current detections to existing tracked objects
        for detection in detections:
            if detection is None:
                continue
                
            matched = False
            for tracked_object in tracked_objects:
                # Safety check for empty detection list
                if tracked_object.get('last_detection',False):
                    
                    if self.is_similar(detection, tracked_object['last_detection']):
                        # Convert detection to dict and add to history
                        tracked_object['last_detection'] = detection
                        
                        tracked_object['seen_this_frame'] = True
                        tracked_object['seen_count'] = tracked_object.get('seen_count',0)+1
                        matched = True
                        continue
            
            # If no match found, create new tracked object
            if not matched:
                new_object = {
                    'id': len(tracked_objects),
                    'last_detection': detection,
                    'label': detection['label'],
                    'seen_this_frame': True,
                    'seen_count':1,
                    'frames_missing': 0
                }
                tracked_objects.append(new_object)
        
        # Update missing frames count and remove old objects
        tracked_objects = [
            tracked_object for tracked_object in tracked_objects 
            if tracked_object['seen_this_frame'] or tracked_object['frames_missing'] < max_frames_missing
        ]
        
        # Increment missing frames for objects not seen
        for tracked_object in tracked_objects:
            if not tracked_object['seen_this_frame']:
                tracked_object['frames_missing'] += 1
        
        return tracked_objects

    def detect(self):
        """Main detection which will run as long as self.is_detecting is True.
        """
        self.is_detecting = True
        tracked_objects = []
        
        while self.is_detecting:
            metadata = self.camera.capture_metadata()
            self.fps = self.calculate_fps(metadata)
            boxes, scores, classes = self.get_detections(metadata)
            if boxes is None:
                continue
            detections = self.convert_detection_to_dict(boxes, scores, classes, metadata)
            if not detections:
                continue
            # Filter out detections below the confidence threshold
            self.detections =[detection for detection in detections if detection['score'] > self.confidence_threshold]
            # Pass to tracked objects to compare simnialrity between frames and identify objects
            # from frame to frame and also cache for a few frames to allow for tracking
            self.tracked_objects = self.track_detections(self.detections, tracked_objects)
            
            # Stop if preview object no longer exists (e.g when closed)
            if  not self.camera._preview:
                self.is_detecting = False
                self.logger.info('Preview closed')
                break
        self.stop()
    
    # Screen annotation functions that will be called by cam_objpost_callback

    def add_screen_text(self,m:MappedArray, text:str, x:int, y:int)->Tuple[int, int, int, int]: 
        """ add test to screen and return new x and y position
        - m is the mapped array
        - text is the text to add
        - x is the x position
        - y is the y position
        - returns new x and y position and text width and height
        """
        (text_width, text_height), baseline = cv2.getTextSize(text, DEFAULT_SCREEN_FONT, DEFAULT_SCREEN_FONT_SIZE, DEFAULT_SCREEN_FONT_THIKCNESS)
        cv2.putText(m.array, text, (x, y), DEFAULT_SCREEN_FONT, DEFAULT_SCREEN_FONT_SIZE, DEFAULT_SCREEN_FONT_COLOUR, DEFAULT_SCREEN_FONT_THIKCNESS)
        new_x = x + text_width + 10
        new_y = y + text_height + 10
        return new_x, new_y,text_width,text_height

    def draw_objects(self,m:MappedArray,detections:List[Dict[str, Any]])->None:
        """ draw objects on screen
        - m is the mapped array
        - detections is the list of detections
        """
        for index,detection in enumerate(detections):
            x, y, w, h = detection['box']
            label = f"{index}: {detection['label']} ({detection['score']:.2f})"
            # Create a copy of the array to draw the background with opacity
            overlay = m.array.copy()
            # Draw the background rectangle on the overlay
            (text_width, text_height), baseline = cv2.getTextSize(label, DEFAULT_SCREEN_FONT, DEFAULT_SCREEN_FONT_SIZE, DEFAULT_SCREEN_FONT_THIKCNESS)
            text_x = x+5
            text_y = y+10
            cv2.rectangle(overlay,(text_x, text_y+10 - text_height),(text_x + text_width, text_y + baseline),(0, 0, 0),  cv2.FILLED)
            alpha = 0.6
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)
            self.add_screen_text(m, label, x+5, y+15)
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)

    def annotate_screen(self, request, stream:str="main",start_x:int=10, start_y:int=30)->None:
        """ annotate screen. The overall annotation of any screen items.
        - request is the request object
        - stream is the stream name
        - start_x is the x position
        - start_y is the y position
        """
        with MappedArray(request, stream) as m:
            new_x, new_y,text_width,text_height = self.add_screen_text(m, f"FPS: {self.fps:.2f}", start_x, start_y)
            start_x, new_y,text_width,text_height = self.add_screen_text(m, f"Detections: {len(self.detections)}", new_x, new_y)
            self.draw_objects(m,self.detections)
