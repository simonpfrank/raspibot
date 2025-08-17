#!/usr/bin/env python3
"""Object deduplication for room scanning.

Removes duplicate detections of the same physical object across camera positions
using proven methods: spatial similarity, bounding box overlap, temporal smoothing.
"""

import asyncio
import math
from typing import List, Dict, Tuple


class ObjectDeduplicator:
    """Removes duplicate object detections across camera positions."""

    def __init__(
        self,
        spatial_threshold: float = 0.7,
        box_overlap_threshold: float = 0.2,
        min_frames: int = 3,
    ):
        """Initialize deduplicator with proven thresholds from experiments."""
        self.spatial_threshold = spatial_threshold
        self.box_overlap_threshold = box_overlap_threshold
        self.min_frames = min_frames

    def deduplicate(self, detections: List[Dict]) -> List[Dict]:
        """Remove duplicates using configured methods."""
        if not detections:
            return []

        # Apply temporal smoothing first
        smoothed = self._apply_temporal_smoothing(detections)

        # Sort by confidence (highest first)
        sorted_detections = sorted(smoothed, key=lambda d: d["confidence"], reverse=True)
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

    async def deduplicate_async(self, detections: List[Dict]) -> List[Dict]:
        """Async version for robot integration."""
        # Run in executor to avoid blocking
        return await asyncio.to_thread(self.deduplicate, detections)

    def _is_duplicate_object(self, det1: Dict, det2: Dict) -> bool:
        """Check if two detections are the same object using all enabled methods."""
        # Must be same label
        if det1["label"] != det2["label"]:
            return False

        # Method 1: Bounding Box Overlap
        overlap = self._calculate_box_overlap(det1["box"], det2["box"])
        if overlap > self.box_overlap_threshold:
            return True

        # Method 2: Spatial Similarity
        similarity = self._calculate_spatial_similarity(det1["box"], det2["box"])
        if similarity > self.spatial_threshold:
            return True

        return False

    def _calculate_box_overlap(self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
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

    def _calculate_spatial_similarity(self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """Calculate spatial similarity based on center positions and size."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        # Calculate centers
        cx1, cy1 = x1 + w1 / 2, y1 + h1 / 2
        cx2, cy2 = x2 + w2 / 2, y2 + h2 / 2

        # Calculate normalized distance between centers
        max_distance = (640**2 + 480**2) ** 0.5  # Diagonal of typical frame
        center_distance = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
        normalized_distance = center_distance / max_distance

        # Calculate size similarity
        size1 = w1 * h1
        size2 = w2 * h2
        size_ratio = min(size1, size2) / max(size1, size2) if max(size1, size2) > 0 else 0

        # Combine metrics: closer centers + similar sizes = higher similarity
        similarity = (1 - normalized_distance) * 0.7 + size_ratio * 0.3
        return max(0, min(1, similarity))

    def _apply_temporal_smoothing(self, detections: List[Dict]) -> List[Dict]:
        """Apply temporal smoothing per position to reduce noise."""
        if not detections:
            return detections

        # Group by position and label
        position_groups = {}
        for det in detections:
            key = (det["position_index"], det["label"])
            if key not in position_groups:
                position_groups[key] = []
            position_groups[key].append(det)

        smoothed_detections = []

        for group in position_groups.values():
            if len(group) >= self.min_frames:
                # Apply weighted averaging using confidence
                total_weight = sum(d["confidence"] for d in group)

                if total_weight > 0:
                    # Weighted average bounding box
                    avg_x = sum(d["box"][0] * d["confidence"] for d in group) / total_weight
                    avg_y = sum(d["box"][1] * d["confidence"] for d in group) / total_weight
                    avg_w = sum(d["box"][2] * d["confidence"] for d in group) / total_weight
                    avg_h = sum(d["box"][3] * d["confidence"] for d in group) / total_weight

                    # Use highest confidence detection as base
                    best_det = max(group, key=lambda d: d["confidence"])

                    # Create smoothed detection
                    smoothed_box = (int(avg_x), int(avg_y), int(avg_w), int(avg_h))
                    smoothed_world_angle = self._calculate_world_angle(smoothed_box, best_det["pan_angle"])

                    smoothed_detection = {
                        "label": best_det["label"],
                        "confidence": best_det["confidence"],
                        "box": smoothed_box,
                        "pan_angle": best_det["pan_angle"],
                        "world_angle": smoothed_world_angle,
                        "position_index": best_det["position_index"],
                        "timestamp": best_det["timestamp"],
                    }
                    smoothed_detections.append(smoothed_detection)
            else:
                # Not enough frames, keep best detection
                if group:
                    smoothed_detections.append(max(group, key=lambda d: d["confidence"]))

        return smoothed_detections

    def _calculate_world_angle(self, bounding_box: Tuple[int, int, int, int], pan_angle: float, frame_width: int = 1280, fov_horizontal: float = 66.3) -> float:
        """Calculate precise world angle for an object based on its position in frame."""
        x, y, w, h = bounding_box

        # Calculate person's center in frame
        person_center_x = x + w / 2
        frame_center_x = frame_width / 2
        pixel_offset = person_center_x - frame_center_x

        # Calculate focal length in pixels using FOV
        fov_horizontal_radians = math.radians(fov_horizontal)
        focal_length_pixels = frame_width / (2 * math.tan(fov_horizontal_radians / 2))

        # Calculate angle offset from pixel position
        angle_offset_radians = math.atan(pixel_offset / focal_length_pixels)
        angle_offset_degrees = math.degrees(angle_offset_radians)

        # World angle = servo pan angle + pixel-based offset
        world_angle = pan_angle + angle_offset_degrees

        return world_angle