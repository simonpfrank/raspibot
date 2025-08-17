#!/usr/bin/env python3
"""Enhanced Room Scanner v3 - Configurable deduplication methods.

All deduplication approaches with on/off switches for experimentation.
Preserves v2 functionality while adding new clustering methods.
"""

import sys
import time
import math
from pathlib import Path
from threading import Thread
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from raspibot.hardware.cameras.camera import Camera
from raspibot.hardware.servos.controller_selector import get_servo_controller
from raspibot.settings.config import (
    SERVO_PAN_CHANNEL,
    SERVO_TILT_CHANNEL,
    SERVO_PAN_MIN_ANGLE,
    SERVO_PAN_MAX_ANGLE,
    SERVO_PAN_CENTER,
    SERVO_TILT_MIN_ANGLE,
    SERVO_TILT_MAX_ANGLE,
    SERVO_TILT_CENTER,
)


@dataclass
class DeduplicationConfig:
    """Configuration for deduplication methods - all can be turned on/off."""

    # Method 1: World Angle Clustering (existing v2)
    use_world_angle_clustering: bool = True
    world_angle_tolerance: float = 25.0

    # Method 2: Spatial Similarity (existing v2)
    use_spatial_similarity: bool = True
    spatial_similarity_threshold: float = 0.7

    # Method 3: Bounding Box Overlap (existing v2)
    use_box_overlap: bool = True
    box_overlap_threshold: float = 0.2

    # Method 4: Nearby Box Detection (existing v2)
    use_nearby_detection: bool = True
    nearby_box_multiplier: float = 2.0

    # Method 5: Edge-Based FOV Overlap (NEW)
    use_edge_detection: bool = True
    edge_boundary_threshold: float = 1200.0  # pixels from right edge
    edge_left_threshold: float = 80.0  # pixels from left edge

    # Method 6: Y-Coordinate Matching (NEW)
    use_y_coordinate_matching: bool = True
    y_position_tolerance: float = 50.0  # pixels

    # Method 7: Temporal Smoothing (NEW)
    use_temporal_smoothing: bool = True
    temporal_frames_required: int = 3  # min frames to consider stable

    # Method 8: Movement Analysis (NEW)
    use_movement_analysis: bool = False  # Experimental
    noise_threshold: float = 10.0  # pixels for noise vs movement


@dataclass
class ScanConfig:
    """Configuration for room scanning parameters."""

    # Camera FOV settings (IMX500 values)
    fov_horizontal: float = 66.3  # degrees
    fov_vertical: float = 55.0  # degrees
    scan_overlap: float = 10.0  # degrees overlap between positions

    # Servo movement settings
    smooth_step_size: float = 3.0  # degrees per step
    smooth_step_delay: float = 0.1  # seconds between steps
    settling_time: float = 1.0  # seconds to settle at position

    # Detection settings
    frames_per_position: int = 8  # frames to capture per position
    frame_delay: float = 0.2  # seconds between frames
    confidence_threshold: float = 0.6  # minimum detection confidence

    # Scan range
    scan_tilt: float = 90.0  # default tilt angle for scanning


@dataclass
class DetectionData:
    """Data structure for a single detection."""

    label: str
    confidence: float
    box: Tuple[int, int, int, int]  # x, y, w, h
    pan_angle: float
    tilt_angle: float
    world_angle: float  # Precise world angle calculated from pan + pixel offset
    timestamp: float
    frame_number: int
    position_index: int  # Which scan position this came from




class RoomScanner:
    """Enhanced room scanner with configurable deduplication methods."""

    def __init__(
        self, config: ScanConfig = None, dedup_config: DeduplicationConfig = None
    ):
        self.config = config or ScanConfig()
        self.dedup_config = dedup_config or DeduplicationConfig()
        self.camera = Camera()
        self.servo_controller = None
        self.scan_data: List[DetectionData] = []
        self.scan_positions: List[float] = []
        self.position_data: List[List[DetectionData]] = []  # Track per-position data

    def calculate_scan_positions(self) -> List[float]:
        """Calculate optimal scan positions based on FOV and overlap."""
        positions = []

        # Calculate effective FOV per position (accounting for overlap)
        effective_fov = self.config.fov_horizontal - self.config.scan_overlap

        # Calculate scan range
        scan_range = SERVO_PAN_MAX_ANGLE - SERVO_PAN_MIN_ANGLE

        # Calculate number of positions needed
        num_positions = int(scan_range / effective_fov) + 1

        # Generate evenly spaced positions
        for i in range(num_positions):
            position = SERVO_PAN_MIN_ANGLE + (i * effective_fov)
            if position <= SERVO_PAN_MAX_ANGLE:
                positions.append(position)

        # Ensure we cover the full range
        if positions[-1] < SERVO_PAN_MAX_ANGLE - 5:  # 5 degree tolerance
            positions.append(SERVO_PAN_MAX_ANGLE)

        print(
            f"Calculated {len(positions)} scan positions: {[f'{p:.1f}°' for p in positions]}"
        )
        return positions

    def start_camera(self):
        """Start camera in separate thread."""
        self.camera.start()
        self.camera.process()
        print("Camera started and detection enabled")

    def calculate_world_angle(
        self,
        bounding_box: Tuple[int, int, int, int],
        pan_angle: float,
        frame_width: int = 1280,
    ) -> float:
        """Calculate precise world angle for an object based on its position in frame."""
        x, y, w, h = bounding_box

        # Calculate person's center in frame
        person_center_x = x + w / 2
        frame_center_x = frame_width / 2
        pixel_offset = person_center_x - frame_center_x

        # Calculate focal length in pixels using FOV
        fov_horizontal_radians = math.radians(self.config.fov_horizontal)
        focal_length_pixels = frame_width / (2 * math.tan(fov_horizontal_radians / 2))

        # Calculate angle offset from pixel position
        angle_offset_radians = math.atan(pixel_offset / focal_length_pixels)
        angle_offset_degrees = math.degrees(angle_offset_radians)

        # World angle = servo pan angle + pixel-based offset
        world_angle = pan_angle + angle_offset_degrees

        return world_angle

    def capture_detections_at_position(
        self, pan_angle: float, tilt_angle: float, position_index: int
    ) -> List[DetectionData]:
        """Capture multiple detection frames at current position."""
        detections = []

        print(f"  Capturing {self.config.frames_per_position} frames...")

        for frame_num in range(self.config.frames_per_position):
            # Get current tracked objects
            tracked_objects = self.camera.tracked_objects

            if tracked_objects:
                for obj in tracked_objects:
                    last_detection = obj.get("last_detection")
                    if (
                        last_detection
                        and last_detection.get("score", 0)
                        >= self.config.confidence_threshold
                    ):

                        box = tuple(last_detection["box"])
                        world_angle = self.calculate_world_angle(box, pan_angle)

                        detection = DetectionData(
                            label=last_detection["label"],
                            confidence=last_detection["score"],
                            box=box,
                            pan_angle=pan_angle,
                            tilt_angle=tilt_angle,
                            world_angle=world_angle,
                            timestamp=time.time(),
                            frame_number=frame_num,
                            position_index=position_index,
                        )
                        detections.append(detection)

            time.sleep(self.config.frame_delay)
            print(
                f"    Frame {frame_num+1}: {len([d for d in detections if d.frame_number == frame_num])} detections"
            )

        return detections

    def scan_room(self) -> List[DetectionData]:
        """Perform complete room scan."""
        print("=== Enhanced Room Scanner v3 ===")
        print(f"FOV: {self.config.fov_horizontal}°H x {self.config.fov_vertical}°V")
        print(f"Overlap: {self.config.scan_overlap}°")
        print(
            f"Smooth movement: {self.config.smooth_step_size}° steps, {self.config.smooth_step_delay}s delay"
        )

        # Print active deduplication methods
        active_methods = []
        if self.dedup_config.use_world_angle_clustering:
            active_methods.append("WorldAngle")
        if self.dedup_config.use_spatial_similarity:
            active_methods.append("Spatial")
        if self.dedup_config.use_box_overlap:
            active_methods.append("BoxOverlap")
        if self.dedup_config.use_nearby_detection:
            active_methods.append("Nearby")
        if self.dedup_config.use_edge_detection:
            active_methods.append("EdgeFOV")
        if self.dedup_config.use_y_coordinate_matching:
            active_methods.append("YCoord")
        if self.dedup_config.use_temporal_smoothing:
            active_methods.append("Temporal")
        if self.dedup_config.use_movement_analysis:
            active_methods.append("Movement")
        print(f"Deduplication: {', '.join(active_methods)}")

        # Initialize hardware
        self.servo_controller = get_servo_controller()

        # Calculate scan positions
        self.scan_positions = self.calculate_scan_positions()

        # Start camera
        Thread(target=self.start_camera).start()
        time.sleep(3)  # Allow camera to initialize

        all_detections = []
        self.position_data = []

        try:
            print(f"\nStarting scan of {len(self.scan_positions)} positions...")

            for i, pan_angle in enumerate(self.scan_positions):
                print(
                    f"\n[{i+1}/{len(self.scan_positions)}] Scanning position: Pan={pan_angle:.1f}°"
                )

                # Move to position directly
                print(f"Moving to Pan={pan_angle:.1f}°, Tilt={self.config.scan_tilt:.1f}°")
                self.servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, pan_angle)
                self.servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, self.config.scan_tilt)

                # Wait for settling
                print(f"  Settling for {self.config.settling_time}s...")
                time.sleep(self.config.settling_time)

                # Clear tracked objects and wait for fresh detections
                print("  Clearing tracked objects...")
                self.camera.clear_tracked_objects()
                time.sleep(2.0)  # Wait for fresh detections

                # Capture detections
                position_detections = self.capture_detections_at_position(
                    pan_angle, self.config.scan_tilt, i
                )

                all_detections.extend(position_detections)
                self.position_data.append(position_detections)

                # Summary for this position (before deduplication)
                unique_objects = {}
                for det in position_detections:
                    key = f"{det.label}_{det.box}"
                    if (
                        key not in unique_objects
                        or det.confidence > unique_objects[key].confidence
                    ):
                        unique_objects[key] = det

                print(
                    f"  Position summary: {len(unique_objects)} unique objects detected"
                )
                for obj in unique_objects.values():
                    print(f"    {obj.label}: {obj.confidence:.2f}")

            # Return to center
            print(f"\nReturning to center position...")
            self.servo_controller.set_servo_angle(SERVO_PAN_CHANNEL, SERVO_PAN_CENTER)
            self.servo_controller.set_servo_angle(SERVO_TILT_CHANNEL, SERVO_TILT_CENTER)

        except KeyboardInterrupt:
            print("\nScan interrupted by user")
        except Exception as e:
            print(f"Error during scan: {e}")
        finally:
            # Cleanup
            self.camera.stop()
            self.camera.shutdown()

        return all_detections

    # ==================== DEDUPLICATION METHODS ====================

    def _deduplicate_detections(
        self, detections: List[DetectionData]
    ) -> List[DetectionData]:
        """Master deduplication using all configured methods."""
        if not detections:
            return []

        # Apply temporal smoothing first (if enabled)
        if self.dedup_config.use_temporal_smoothing:
            detections = self._apply_temporal_smoothing(detections)

        # Sort by confidence (highest first)
        sorted_detections = sorted(detections, key=lambda d: d.confidence, reverse=True)
        unique_objects = []

        for detection in sorted_detections:
            is_duplicate = False

            for existing in unique_objects:
                if self._is_duplicate_object(detection, existing):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_objects.append(detection)

        return unique_objects

    def _is_duplicate_object(self, det1: DetectionData, det2: DetectionData) -> bool:
        """Check if two detections are the same object using all enabled methods."""

        # Method 5: Edge-Based FOV Overlap (check first - most specific)
        if self.dedup_config.use_edge_detection:
            if self._is_edge_overlap_duplicate(det1, det2):
                return True

        # Method 1: World Angle Clustering
        if self.dedup_config.use_world_angle_clustering:
            world_angle_diff = abs(det1.world_angle - det2.world_angle)
            if world_angle_diff < self.dedup_config.world_angle_tolerance:

                # Method 6: Y-Coordinate Matching (enhance world angle)
                if self.dedup_config.use_y_coordinate_matching:
                    y_diff = abs(det1.box[1] - det2.box[1])
                    if y_diff < self.dedup_config.y_position_tolerance:
                        return True
                else:
                    return True  # World angle alone

        # Method 3: Bounding Box Overlap
        if self.dedup_config.use_box_overlap:
            overlap = self._calculate_box_overlap(det1.box, det2.box)
            if overlap > self.dedup_config.box_overlap_threshold:
                return True

        # Method 2: Spatial Similarity
        if self.dedup_config.use_spatial_similarity:
            similarity = self._calculate_spatial_similarity(det1.box, det2.box)
            if similarity > self.dedup_config.spatial_similarity_threshold:
                return True

        # Method 4: Nearby Box Detection
        if self.dedup_config.use_nearby_detection:
            if self._boxes_are_nearby(det1.box, det2.box):
                return True

        return False

    def _is_edge_overlap_duplicate(
        self, det1: DetectionData, det2: DetectionData
    ) -> bool:
        """NEW: Check if objects are FOV overlap duplicates using edge detection."""
        if det1.position_index == det2.position_index:
            return False  # Same position, not FOV overlap

        # Check if positions are adjacent
        pos_diff = abs(det1.position_index - det2.position_index)
        if pos_diff != 1:
            return False  # Not adjacent positions

        x1, y1, w1, h1 = det1.box
        x2, y2, w2, h2 = det2.box

        # Object near right edge of earlier position AND near left edge of later position
        earlier_det = det1 if det1.position_index < det2.position_index else det2
        later_det = det2 if det1.position_index < det2.position_index else det1

        earlier_x, earlier_y, earlier_w, earlier_h = earlier_det.box
        later_x, later_y, later_w, later_h = later_det.box

        # Check edge conditions
        is_right_edge = (
            earlier_x + earlier_w
        ) > self.dedup_config.edge_boundary_threshold
        is_left_edge = later_x < self.dedup_config.edge_left_threshold

        # Check Y similarity (same height in room)
        y_similar = abs(earlier_y - later_y) < self.dedup_config.y_position_tolerance

        return is_right_edge and is_left_edge and y_similar

    def _apply_temporal_smoothing(
        self, detections: List[DetectionData]
    ) -> List[DetectionData]:
        """NEW: Apply Weighted Box Fusion per position to smooth bounding boxes."""
        if not detections:
            return detections

        # Group by position and label
        position_groups = {}
        for det in detections:
            key = (det.position_index, det.label)
            if key not in position_groups:
                position_groups[key] = []
            position_groups[key].append(det)

        smoothed_detections = []

        for (pos_idx, label), group in position_groups.items():
            if len(group) >= self.dedup_config.temporal_frames_required:
                # Apply WBF - weighted average of boxes using confidence as weight
                total_weight = sum(d.confidence for d in group)

                if total_weight > 0:
                    # Weighted average bounding box
                    avg_x = sum(d.box[0] * d.confidence for d in group) / total_weight
                    avg_y = sum(d.box[1] * d.confidence for d in group) / total_weight
                    avg_w = sum(d.box[2] * d.confidence for d in group) / total_weight
                    avg_h = sum(d.box[3] * d.confidence for d in group) / total_weight

                    # Use highest confidence detection as base
                    best_det = max(group, key=lambda d: d.confidence)

                    # Create smoothed detection
                    smoothed_box = (int(avg_x), int(avg_y), int(avg_w), int(avg_h))
                    smoothed_world_angle = self.calculate_world_angle(
                        smoothed_box, best_det.pan_angle
                    )

                    smoothed_detection = DetectionData(
                        label=best_det.label,
                        confidence=best_det.confidence,
                        box=smoothed_box,
                        pan_angle=best_det.pan_angle,
                        tilt_angle=best_det.tilt_angle,
                        world_angle=smoothed_world_angle,
                        timestamp=best_det.timestamp,
                        frame_number=best_det.frame_number,
                        position_index=best_det.position_index,
                    )
                    smoothed_detections.append(smoothed_detection)
            else:
                # Not enough frames, keep best detection
                if group:
                    smoothed_detections.append(max(group, key=lambda d: d.confidence))

        return smoothed_detections

    # ==================== EXISTING v2 METHODS (preserved) ====================

    def _calculate_box_overlap(
        self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]
    ) -> float:
        """Calculate overlap ratio between two bounding boxes."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        # Calculate intersection
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)

        if left < right and top < bottom:
            intersection = (right - left) * (bottom - top)
            area1 = w1 * h1
            area2 = w2 * h2
            union = area1 + area2 - intersection
            return intersection / union if union > 0 else 0.0

        return 0.0

    def _calculate_spatial_similarity(
        self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]
    ) -> float:
        """Calculate spatial similarity based on center positions and size."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        # Calculate centers
        cx1, cy1 = x1 + w1 / 2, y1 + h1 / 2
        cx2, cy2 = x2 + w2 / 2, y2 + h2 / 2

        # Calculate normalized distance between centers (0-1 scale)
        max_distance = (640**2 + 480**2) ** 0.5  # Diagonal of typical frame
        center_distance = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
        normalized_distance = center_distance / max_distance

        # Calculate size similarity
        size1 = w1 * h1
        size2 = w2 * h2
        size_ratio = (
            min(size1, size2) / max(size1, size2) if max(size1, size2) > 0 else 0
        )

        # Combine metrics: closer centers + similar sizes = higher similarity
        similarity = (1 - normalized_distance) * 0.7 + size_ratio * 0.3
        return max(0, min(1, similarity))

    def _boxes_are_nearby(
        self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]
    ) -> bool:
        """Check if two boxes are nearby in the frame."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        # Calculate centers
        cx1, cy1 = x1 + w1 / 2, y1 + h1 / 2
        cx2, cy2 = x2 + w2 / 2, y2 + h2 / 2

        # Distance between centers
        center_distance = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5

        # Average box size (for scale-relative distance)
        avg_size = ((w1 * h1) ** 0.5 + (w2 * h2) ** 0.5) / 2

        # Nearby if center distance < multiplier * average box size
        return center_distance < (avg_size * self.dedup_config.nearby_box_multiplier)

    def _generate_csv_filename(self) -> str:
        """Generate CSV filename based on enabled deduplication methods."""
        method_codes = []

        if self.dedup_config.use_world_angle_clustering:
            method_codes.append("wac")
        if self.dedup_config.use_spatial_similarity:
            method_codes.append("ss")
        if self.dedup_config.use_box_overlap:
            method_codes.append("bo")
        if self.dedup_config.use_nearby_detection:
            method_codes.append("nd")
        if self.dedup_config.use_edge_detection:
            method_codes.append("ed")
        if self.dedup_config.use_y_coordinate_matching:
            method_codes.append("ycm")
        if self.dedup_config.use_temporal_smoothing:
            method_codes.append("ts")
        if self.dedup_config.use_movement_analysis:
            method_codes.append("ma")

        if not method_codes:
            return "no_dedup.csv"

        return "_".join(method_codes) + ".csv"

    def _save_detections_to_csv(self, detections: List[DetectionData]):
        """Save deduplicated detection results to CSV file."""
        import csv

        filename = self._generate_csv_filename()
        filepath = Path(__file__).parent / filename

        # Group by label and deduplicate
        by_label = {}
        for det in detections:
            if det.label not in by_label:
                by_label[det.label] = []
            by_label[det.label].append(det)

        # Prepare CSV data
        csv_rows = [
            [
                "pos",
                "label",
                "conf",
                "pan",
                "world",
                "left",
                "right",
                "top",
                "bottom",
            ]
        ]
        for label, label_detections in by_label.items():
            unique_objects = self._deduplicate_detections(label_detections)

            for obj in unique_objects:
                x, y, w, h = obj.box
                csv_rows.append(
                    [
                        f"{obj.position_index}",
                        label,
                        f"{obj.confidence:.2f}",
                        f"{obj.pan_angle:.1f}",
                        f"{obj.world_angle:.1f}",
                        f"{x}",
                        f"{x+w}",
                        f"{y}",
                        f"{y+h}",
                    ]
                )

        # Write CSV (no headers as requested)
        with open(filepath, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_rows)

        print(f"\n📄 Results saved to: {filename}")

    def print_scan_summary(self, detections: List[DetectionData]):
        """Print comprehensive scan summary with configurable deduplication."""
        if not detections:
            print("\nNo detections found during scan.")
            return

        print(f"\n=== SCAN COMPLETE: {len(detections)} raw detections ===")

        # Group by label
        by_label = {}
        for det in detections:
            if det.label not in by_label:
                by_label[det.label] = []
            by_label[det.label].append(det)

        # Print summary by object type with deduplication
        total_unique_objects = 0
        for label, label_detections in by_label.items():
            # Deduplicate using configured methods
            unique_objects = self._deduplicate_detections(label_detections)
            total_unique_objects += len(unique_objects)

            print(
                f"\n{label.upper()}: {len(label_detections)} raw → {len(unique_objects)} unique"
            )

            # Show unique objects with detailed position data
            for i, obj in enumerate(unique_objects, 1):
                x, y, w, h = obj.box
                print(
                    f"  #{i}: {obj.confidence:.2f} confidence at Pan={obj.pan_angle:.1f}° (World={obj.world_angle:.1f}°) x={x}-{x+w}"
                )

        print(f"\n🎯 SUMMARY: {total_unique_objects} unique objects total")

        # Show detailed people analysis
        people = [d for d in detections if d.label == "person"]
        if people:
            unique_people = self._deduplicate_detections(people)
            print(f"\n👥 PEOPLE ANALYSIS:")
            print(f"  Raw detections: {len(people)}")
            print(f"  Unique people: {len(unique_people)}")
            for i, person in enumerate(unique_people, 1):
                x, y, w, h = person.box
                print(
                    f"    Person #{i}: {person.confidence:.2f} at Pan={person.pan_angle:.1f}° (World={person.world_angle:.1f}°) x={x}-{x+w}"
                )

        # Save results to CSV
        self._save_detections_to_csv(detections)


def main():
    """Main experimental function with configurable deduplication."""

    # Test different deduplication combinations
    print("=== Testing Multiple Deduplication Approaches ===")

    # Configuration 1: Edge + Y-Coordinate (your theory)
    dedup_config = DeduplicationConfig(
        # Disable existing methods temporarily
        use_world_angle_clustering=False,
        use_spatial_similarity=True,
        use_box_overlap=True,
        use_nearby_detection=False,
        # Enable new methods
        use_edge_detection=False,
        use_y_coordinate_matching=False,
        use_temporal_smoothing=True,
        use_movement_analysis=False,
        # Aggressive parameters
        edge_boundary_threshold=1200.0,
        edge_left_threshold=80.0,
        y_position_tolerance=50.0,
    )

    # Scanner config
    config = ScanConfig(
        fov_horizontal=66.3,  # Updated FOV value
        fov_vertical=55.0,
        scan_overlap=15.0,
        smooth_step_size=2.0,
        smooth_step_delay=0.08,
        settling_time=1.0,
        frames_per_position=6,
        confidence_threshold=0.5,
    )

    scanner = RoomScanner(config, dedup_config)

    # Perform scan
    detections = scanner.scan_room()

    # Show results
    scanner.print_scan_summary(detections)

    print(f"\nv3 Experiment complete! Found {len(detections)} detections.")


if __name__ == "__main__":
    main()
