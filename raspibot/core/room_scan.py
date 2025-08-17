#!/usr/bin/env python3
"""Room scanning system that coordinates camera detection with servo movement.

Main orchestrator that combines camera detection with servo movement to
systematically scan and identify objects in a room with deduplication.
"""

import asyncio
import time
import logging
from typing import List, Dict, Optional
from raspibot.hardware.cameras.camera import Camera
from raspibot.hardware.servos.controller_selector import get_servo_controller
from raspibot.vision.deduplication import ObjectDeduplicator
from raspibot.movement.scanner import ScanPattern
from raspibot.settings.config import (
    SERVO_PAN_CENTER,
    SERVO_TILT_CENTER,
)


class RoomScanner:
    """Main room scanning system."""

    def __init__(
        self,
        camera: Optional[Camera] = None,
        servo_controller=None,
        face_detection: bool = False,
        frames_per_position: int = 6,
        settling_time: float = 1.0,
        confidence_threshold: float = 0.6,
        scan_tilt: float = 90.0,
        fov_degrees: float = 66.3,
        overlap_degrees: float = 10.0,
    ):
        """Initialize room scanner with configurable parameters."""
        self.logger = logging.getLogger(__name__)
        
        # Hardware
        self.camera = camera or Camera()
        self.servo_controller = servo_controller or get_servo_controller()
        
        # Configuration
        self.face_detection = face_detection
        self.frames_per_position = frames_per_position
        self.settling_time = settling_time
        self.confidence_threshold = confidence_threshold
        self.scan_tilt = scan_tilt
        
        # Components
        self.deduplicator = ObjectDeduplicator()
        self.scan_pattern = ScanPattern(fov_degrees, overlap_degrees)
        
        # Results
        self.last_scan_data = []
        self.scan_positions = []

    def scan_room(self) -> List[Dict]:
        """Perform complete room scan and return unique objects."""
        self.logger.info("Starting room scan")
        
        # Calculate scan positions
        self.scan_positions = self.scan_pattern.calculate_positions()
        self.logger.info(f"Scanning {len(self.scan_positions)} positions: {[f'{p:.1f}°' for p in self.scan_positions]}")
        
        # Start camera if not already running
        if not hasattr(self.camera, '_running') or not self.camera._running:
            self.camera.start()
            # Start detection in separate thread
            from threading import Thread
            detection_thread = Thread(target=self.camera.process)
            detection_thread.daemon = True
            detection_thread.start()
            time.sleep(3.0)  # Allow camera to initialize and start detecting
            self.logger.info("Camera started and detection enabled")

        all_detections = []

        try:
            for i, pan_angle in enumerate(self.scan_positions):
                self.logger.info(f"[{i+1}/{len(self.scan_positions)}] Scanning position: Pan={pan_angle:.1f}°")
                
                # Move to position
                self.scan_pattern.move_to_position(self.servo_controller, pan_angle, self.scan_tilt)
                self.logger.debug(f"Moved to Pan={pan_angle:.1f}°, Tilt={self.scan_tilt:.1f}°")
                
                # Wait for settling
                self.logger.debug(f"Settling for {self.settling_time}s...")
                time.sleep(self.settling_time)
                
                # Clear tracked objects for fresh detections
                self.camera.clear_tracked_objects()
                time.sleep(1.0)  # Wait for fresh detections
                
                # Capture detections at this position
                position_detections = self._capture_detections_at_position(pan_angle, self.scan_tilt, i)
                all_detections.extend(position_detections)
                
                self.logger.info(f"Position {i+1} captured {len(position_detections)} detections")

            # Return to center
            self.logger.info("Returning to center position")
            self.scan_pattern.move_to_position(self.servo_controller, SERVO_PAN_CENTER, SERVO_TILT_CENTER)
            
        except KeyboardInterrupt:
            self.logger.warning("Scan interrupted by user")
        except Exception as e:
            self.logger.error(f"Error during scan: {e}")
            raise
        
        # Deduplicate all detections
        self.logger.info(f"Deduplicating {len(all_detections)} raw detections")
        unique_objects = self.deduplicator.deduplicate(all_detections)
        
        self.last_scan_data = unique_objects
        self.logger.info(f"Room scan complete: {len(unique_objects)} unique objects found")
        
        return unique_objects

    async def scan_room_async(self) -> List[Dict]:
        """Async version for robot integration."""
        self.logger.info("Starting async room scan")
        
        # Calculate scan positions
        self.scan_positions = self.scan_pattern.calculate_positions()
        self.logger.info(f"Scanning {len(self.scan_positions)} positions: {[f'{p:.1f}°' for p in self.scan_positions]}")
        
        # Start camera if not already running
        if not hasattr(self.camera, '_running') or not self.camera._running:
            self.camera.start()
            # Start detection in separate thread
            from threading import Thread
            detection_thread = Thread(target=self.camera.process)
            detection_thread.daemon = True
            detection_thread.start()
            await asyncio.sleep(3.0)  # Allow camera to initialize and start detecting
            self.logger.info("Camera started and detection enabled")

        all_detections = []

        try:
            for i, pan_angle in enumerate(self.scan_positions):
                self.logger.info(f"[{i+1}/{len(self.scan_positions)}] Scanning position: Pan={pan_angle:.1f}°")
                
                # Move to position (async)
                await self.scan_pattern.move_to_position_async(self.servo_controller, pan_angle, self.scan_tilt)
                self.logger.debug(f"Moved to Pan={pan_angle:.1f}°, Tilt={self.scan_tilt:.1f}°")
                
                # Wait for settling
                self.logger.debug(f"Settling for {self.settling_time}s...")
                await asyncio.sleep(self.settling_time)
                
                # Clear tracked objects for fresh detections
                await asyncio.to_thread(self.camera.clear_tracked_objects)
                await asyncio.sleep(1.0)  # Wait for fresh detections
                
                # Capture detections at this position
                position_detections = await self._capture_detections_at_position_async(pan_angle, self.scan_tilt, i)
                all_detections.extend(position_detections)
                
                self.logger.info(f"Position {i+1} captured {len(position_detections)} detections")

            # Return to center
            self.logger.info("Returning to center position")
            await self.scan_pattern.move_to_position_async(self.servo_controller, SERVO_PAN_CENTER, SERVO_TILT_CENTER)
            
        except KeyboardInterrupt:
            self.logger.warning("Scan interrupted by user")
        except Exception as e:
            self.logger.error(f"Error during scan: {e}")
            raise
        
        # Deduplicate all detections
        self.logger.info(f"Deduplicating {len(all_detections)} raw detections")
        unique_objects = await self.deduplicator.deduplicate_async(all_detections)
        
        self.last_scan_data = unique_objects
        self.logger.info(f"Async room scan complete: {len(unique_objects)} unique objects found")
        
        return unique_objects

    def enable_face_detection(self, enabled: bool):
        """Toggle face detection validation for person objects."""
        self.face_detection = enabled
        self.logger.info(f"Face detection {'enabled' if enabled else 'disabled'}")

    def get_scan_summary(self) -> Dict:
        """Return summary statistics from last scan."""
        if not self.last_scan_data:
            return {"error": "No scan data available"}
        
        # Count objects by label
        by_label = {}
        for obj in self.last_scan_data:
            label = obj["label"]
            if label not in by_label:
                by_label[label] = []
            by_label[label].append(obj)
        
        summary = {
            "total_objects": len(self.last_scan_data),
            "scan_positions": len(self.scan_positions),
            "objects_by_type": {label: len(objects) for label, objects in by_label.items()},
            "position_angles": self.scan_positions,
        }
        
        return summary

    def _capture_detections_at_position(self, pan_angle: float, tilt_angle: float, position_index: int) -> List[Dict]:
        """Capture multiple detection frames at current position."""
        detections = []
        
        self.logger.debug(f"Capturing {self.frames_per_position} frames at position {position_index}")
        
        for frame_num in range(self.frames_per_position):
            # Get current tracked objects
            tracked_objects = self.camera.tracked_objects
            
            if tracked_objects:
                for obj in tracked_objects:
                    last_detection = obj.get("last_detection")
                    if (
                        last_detection
                        and last_detection.get("score", 0) >= self.confidence_threshold
                    ):
                        box = tuple(last_detection["box"])
                        world_angle = self.deduplicator._calculate_world_angle(box, pan_angle)
                        
                        detection = {
                            "label": last_detection["label"],
                            "confidence": last_detection["score"],
                            "box": box,
                            "pan_angle": pan_angle,
                            "world_angle": world_angle,
                            "position_index": position_index,
                            "timestamp": time.time(),
                        }
                        detections.append(detection)
            
            time.sleep(0.2)  # Frame delay
            
        self.logger.debug(f"Position {position_index} captured {len(detections)} raw detections")
        return detections

    async def _capture_detections_at_position_async(self, pan_angle: float, tilt_angle: float, position_index: int) -> List[Dict]:
        """Async version of detection capture."""
        detections = []
        
        self.logger.debug(f"Capturing {self.frames_per_position} frames at position {position_index}")
        
        for frame_num in range(self.frames_per_position):
            # Get current tracked objects
            tracked_objects = await asyncio.to_thread(lambda: self.camera.tracked_objects)
            
            if tracked_objects:
                for obj in tracked_objects:
                    last_detection = obj.get("last_detection")
                    if (
                        last_detection
                        and last_detection.get("score", 0) >= self.confidence_threshold
                    ):
                        box = tuple(last_detection["box"])
                        world_angle = self.deduplicator._calculate_world_angle(box, pan_angle)
                        
                        detection = {
                            "label": last_detection["label"],
                            "confidence": last_detection["score"],
                            "box": box,
                            "pan_angle": pan_angle,
                            "world_angle": world_angle,
                            "position_index": position_index,
                            "timestamp": time.time(),
                        }
                        detections.append(detection)
            
            await asyncio.sleep(0.2)  # Frame delay
            
        self.logger.debug(f"Position {position_index} captured {len(detections)} raw detections")
        return detections


if __name__ == "__main__":
    """Demo room scan functionality."""
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # Create scanner
    scanner = RoomScanner(
        frames_per_position=4,
        settling_time=1.0,
        confidence_threshold=0.6
    )
    
    print("=== Room Scanner Demo ===")
    print(f"Scan positions: {[f'{p:.1f}°' for p in scanner.scan_pattern.calculate_positions()]}")
    
    try:
        # Perform scan
        objects = scanner.scan_room()
        
        # Display results
        print(f"\n=== RESULTS ===")
        print(f"Found {len(objects)} unique objects:")
        
        for i, obj in enumerate(objects, 1):
            print(f"  {i}. {obj['label']}: {obj['confidence']:.2f} confidence at {obj['world_angle']:.1f}°")
        
        # Show summary
        summary = scanner.get_scan_summary()
        print(f"\nSummary: {summary}")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()