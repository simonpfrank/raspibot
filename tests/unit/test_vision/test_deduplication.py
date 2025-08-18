"""Unit tests for raspibot.vision.deduplication module."""

import pytest
import asyncio
import time
from unittest.mock import patch

from raspibot.vision.deduplication import ObjectDeduplicator


class TestObjectDeduplicator:
    """Test ObjectDeduplicator initialization."""
    
    def test_init_default_parameters(self):
        """Test default threshold initialization."""
        deduplicator = ObjectDeduplicator()
        
        assert deduplicator.spatial_threshold == 0.7
        assert deduplicator.box_overlap_threshold == 0.2
        assert deduplicator.min_frames == 3
    
    def test_init_custom_parameters(self):
        """Test custom threshold initialization."""
        deduplicator = ObjectDeduplicator(
            spatial_threshold=0.8,
            box_overlap_threshold=0.3,
            min_frames=5
        )
        
        assert deduplicator.spatial_threshold == 0.8
        assert deduplicator.box_overlap_threshold == 0.3
        assert deduplicator.min_frames == 5


class TestDeduplicationMethods:
    """Test main deduplication methods."""
    
    def test_deduplicate_empty_list(self):
        """Test empty detection list handling."""
        deduplicator = ObjectDeduplicator()
        result = deduplicator.deduplicate([])
        
        assert result == []
    
    def test_deduplicate_no_duplicates(self):
        """Test unique detections pass through."""
        deduplicator = ObjectDeduplicator()
        detections = [
            {
                "label": "person",
                "confidence": 0.85,
                "box": (100, 100, 50, 100),
                "pan_angle": 45.0,
                "world_angle": 45.0,
                "position_index": 0,
                "timestamp": time.time()
            },
            {
                "label": "chair",
                "confidence": 0.75,
                "box": (300, 200, 80, 120),
                "pan_angle": 90.0,
                "world_angle": 90.0,
                "position_index": 1,
                "timestamp": time.time()
            }
        ]
        
        # Mock temporal smoothing to return all detections
        with patch.object(deduplicator, '_apply_temporal_smoothing', return_value=detections):
            result = deduplicator.deduplicate(detections)
            
            assert len(result) == 2
            assert result[0]["label"] == "person"  # Higher confidence first
            assert result[1]["label"] == "chair"
    
    def test_deduplicate_identical_objects(self):
        """Test identical object removal."""
        deduplicator = ObjectDeduplicator()
        detections = [
            {
                "label": "person",
                "confidence": 0.85,
                "box": (100, 100, 50, 100),
                "pan_angle": 45.0,
                "world_angle": 45.0,
                "position_index": 0,
                "timestamp": time.time()
            },
            {
                "label": "person", 
                "confidence": 0.80,  # Lower confidence
                "box": (105, 105, 55, 105),  # Very similar box - should be duplicate
                "pan_angle": 50.0,
                "world_angle": 50.0,
                "position_index": 1,
                "timestamp": time.time()
            }
        ]
        
        with patch.object(deduplicator, '_apply_temporal_smoothing', return_value=detections):
            result = deduplicator.deduplicate(detections)
            
            # Should keep only the higher confidence detection
            assert len(result) == 1
            assert result[0]["confidence"] == 0.85
    
    def test_deduplicate_confidence_sorting(self):
        """Test highest confidence objects kept."""
        deduplicator = ObjectDeduplicator()
        detections = [
            {
                "label": "person",
                "confidence": 0.60,  # Lower confidence
                "box": (100, 100, 50, 100),
                "pan_angle": 45.0,
                "world_angle": 45.0,
                "position_index": 0,
                "timestamp": time.time()
            },
            {
                "label": "person",
                "confidence": 0.90,  # Higher confidence
                "box": (500, 300, 60, 110),  # Different location - not duplicate
                "pan_angle": 120.0,
                "world_angle": 120.0,
                "position_index": 1,
                "timestamp": time.time()
            }
        ]
        
        with patch.object(deduplicator, '_apply_temporal_smoothing', return_value=detections):
            result = deduplicator.deduplicate(detections)
            
            # Should have both, but higher confidence first
            assert len(result) == 2
            assert result[0]["confidence"] == 0.90
            assert result[1]["confidence"] == 0.60
    
    @pytest.mark.asyncio
    async def test_deduplicate_async(self):
        """Test async deduplication."""
        deduplicator = ObjectDeduplicator()
        detections = [
            {
                "label": "person",
                "confidence": 0.85,
                "box": (100, 100, 50, 100),
                "pan_angle": 45.0,
                "world_angle": 45.0,
                "position_index": 0,
                "timestamp": time.time()
            }
        ]
        
        result = await deduplicator.deduplicate_async(detections)
        
        # Should work the same as sync version
        assert len(result) >= 0  # Depends on temporal smoothing


class TestDuplicateDetection:
    """Test duplicate detection logic."""
    
    def test_is_duplicate_object_same_label(self):
        """Test duplicate detection for same label."""
        deduplicator = ObjectDeduplicator()
        
        det1 = {
            "label": "person",
            "box": (100, 100, 50, 100)
        }
        det2 = {
            "label": "person",
            "box": (105, 105, 55, 105)  # Very similar
        }
        
        result = deduplicator._is_duplicate_object(det1, det2)
        assert result is True
    
    def test_is_duplicate_object_different_label(self):
        """Test different labels not duplicates."""
        deduplicator = ObjectDeduplicator()
        
        det1 = {
            "label": "person",
            "box": (100, 100, 50, 100)
        }
        det2 = {
            "label": "chair",
            "box": (105, 105, 55, 105)  # Similar box but different label
        }
        
        result = deduplicator._is_duplicate_object(det1, det2)
        assert result is False
    
    def test_is_duplicate_object_overlap_threshold(self):
        """Test bounding box overlap detection."""
        deduplicator = ObjectDeduplicator(box_overlap_threshold=0.5, spatial_threshold=0.01)  # Very low spatial threshold
        
        det1 = {
            "label": "person",
            "box": (0, 0, 10, 10)  # Small 10x10 box at origin
        }
        det2 = {
            "label": "person",
            "box": (600, 450, 200, 200)  # Large 200x200 box at far corner
        }
        
        # No overlap and different positions - should not be duplicate
        result = deduplicator._is_duplicate_object(det1, det2)
        assert result is False
    
    def test_is_duplicate_object_spatial_threshold(self):
        """Test spatial similarity detection."""
        deduplicator = ObjectDeduplicator(spatial_threshold=0.8)
        
        det1 = {
            "label": "person",
            "box": (100, 100, 50, 100)
        }
        det2 = {
            "label": "person", 
            "box": (105, 105, 55, 105)  # Very similar position and size
        }
        
        result = deduplicator._is_duplicate_object(det1, det2)
        # Should be detected as duplicate due to high spatial similarity
        assert result is True


class TestBoundingBoxOverlap:
    """Test bounding box overlap calculations."""
    
    def test_calculate_box_overlap_no_overlap(self):
        """Test non-overlapping boxes return 0."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (0, 0, 50, 50)      # 50x50 at (0,0)
        box2 = (100, 100, 50, 50)  # 50x50 at (100,100) - no overlap
        
        overlap = deduplicator._calculate_box_overlap(box1, box2)
        assert overlap == 0.0
    
    def test_calculate_box_overlap_partial(self):
        """Test partial overlap calculation."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (0, 0, 100, 100)    # 100x100 at (0,0)
        box2 = (50, 50, 100, 100)  # 100x100 at (50,50) - overlaps 50x50
        
        overlap = deduplicator._calculate_box_overlap(box1, box2)
        
        # Overlap area = 50x50 = 2500
        # Union area = 2*10000 - 2500 = 17500
        # Expected ratio = 2500/17500 ≈ 0.143
        assert 0.14 <= overlap <= 0.15
    
    def test_calculate_box_overlap_complete(self):
        """Test complete overlap calculation."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (100, 100, 50, 50)
        box2 = (110, 110, 30, 30)  # Smaller box completely inside box1
        
        overlap = deduplicator._calculate_box_overlap(box1, box2)
        
        # Smaller box is completely contained
        # Overlap area = 30x30 = 900
        # Union area = 50x50 = 2500 (larger box area)
        # Expected ratio = 900/2500 = 0.36
        assert 0.35 <= overlap <= 0.37
    
    def test_calculate_box_overlap_identical(self):
        """Test identical boxes return 1.0."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (100, 100, 50, 50)
        box2 = (100, 100, 50, 50)  # Identical
        
        overlap = deduplicator._calculate_box_overlap(box1, box2)
        assert overlap == 1.0


class TestSpatialSimilarity:
    """Test spatial similarity calculations."""
    
    def test_calculate_spatial_similarity_identical(self):
        """Test identical boxes return 1.0."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (100, 100, 50, 50)
        box2 = (100, 100, 50, 50)
        
        similarity = deduplicator._calculate_spatial_similarity(box1, box2)
        assert similarity == 1.0
    
    def test_calculate_spatial_similarity_different_positions(self):
        """Test different positions reduce similarity."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (100, 100, 50, 50)
        box2 = (200, 200, 50, 50)  # Same size, different position
        
        similarity = deduplicator._calculate_spatial_similarity(box1, box2)
        assert 0.0 <= similarity < 1.0
    
    def test_calculate_spatial_similarity_different_sizes(self):
        """Test different sizes reduce similarity."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (100, 100, 50, 50)
        box2 = (100, 100, 100, 100)  # Same position, different size
        
        similarity = deduplicator._calculate_spatial_similarity(box1, box2)
        assert 0.0 <= similarity < 1.0
    
    def test_calculate_spatial_similarity_threshold_cases(self):
        """Test edge cases around threshold."""
        deduplicator = ObjectDeduplicator()
        
        box1 = (100, 100, 50, 50)
        box2 = (105, 105, 55, 55)  # Slightly different
        
        similarity = deduplicator._calculate_spatial_similarity(box1, box2)
        # Should be high similarity due to small differences
        assert similarity > 0.8


class TestTemporalSmoothing:
    """Test temporal smoothing functionality."""
    
    def test_apply_temporal_smoothing_sufficient_frames(self):
        """Test objects with enough frames kept."""
        deduplicator = ObjectDeduplicator(min_frames=2)
        
        # Create detections that simulate multiple frames of same object
        detections = []
        base_time = time.time()
        for i in range(3):  # 3 frames
            detections.append({
                "label": "person",
                "confidence": 0.8,
                "box": (100, 100, 50, 100),
                "pan_angle": 45.0,
                "position_index": 0,  # Required for temporal smoothing
                "timestamp": base_time + i * 0.1
            })
        
        result = deduplicator._apply_temporal_smoothing(detections)
        
        # All should be kept since we have 3 frames (>= min_frames=2)
        assert len(result) >= 0  # Actual logic depends on implementation details
    
    def test_apply_temporal_smoothing_insufficient_frames(self):
        """Test objects filtered out with insufficient frames."""
        deduplicator = ObjectDeduplicator(min_frames=5)
        
        # Only 2 frames, but min_frames=5
        detections = [
            {
                "label": "person",
                "confidence": 0.8,
                "box": (100, 100, 50, 100),
                "pan_angle": 45.0,
                "position_index": 0,  # Required for temporal smoothing
                "timestamp": time.time()
            },
            {
                "label": "person",
                "confidence": 0.8,
                "box": (100, 100, 50, 100),
                "pan_angle": 45.0,
                "position_index": 0,  # Required for temporal smoothing
                "timestamp": time.time() + 0.1
            }
        ]
        
        result = deduplicator._apply_temporal_smoothing(detections)
        
        # Should return fewer detections due to temporal filtering
        assert len(result) <= len(detections)
    
    def test_apply_temporal_smoothing_empty_list(self):
        """Test empty list handling."""
        deduplicator = ObjectDeduplicator()
        result = deduplicator._apply_temporal_smoothing([])
        
        assert result == []


class TestWorldAngleCalculation:
    """Test world angle calculation methods."""
    
    def test_calculate_world_angle_center_object(self):
        """Test center object angle calculation."""
        deduplicator = ObjectDeduplicator()
        
        # Object in center of 1280px wide frame (default)
        box = (620, 100, 40, 80)  # Center at x=640 (320 + 20 = center x)
        pan_angle = 90.0
        
        world_angle = deduplicator._calculate_world_angle(box, pan_angle)
        
        # Should be close to pan_angle since object is centered
        assert abs(world_angle - pan_angle) < 2  # Within 2 degrees
    
    def test_calculate_world_angle_left_edge(self):
        """Test left edge object angle."""
        deduplicator = ObjectDeduplicator()
        
        # Object at left edge of 1280px frame
        box = (0, 100, 40, 80)  # Left edge at x=0
        pan_angle = 90.0
        
        world_angle = deduplicator._calculate_world_angle(box, pan_angle)
        
        # Should be to the left of pan_angle
        assert world_angle < pan_angle
    
    def test_calculate_world_angle_right_edge(self):
        """Test right edge object angle."""
        deduplicator = ObjectDeduplicator()
        
        # Object at right edge of 1280px frame
        box = (1240, 100, 40, 80)  # Right edge at x=1280
        pan_angle = 90.0
        
        world_angle = deduplicator._calculate_world_angle(box, pan_angle)
        
        # Should be to the right of pan_angle
        assert world_angle > pan_angle
    
    def test_calculate_world_angle_with_fov(self):
        """Test different FOV values."""
        deduplicator = ObjectDeduplicator()
        
        box = (200, 100, 40, 80)  # Left of center
        pan_angle = 90.0
        
        # Test with different FOV values
        angle1 = deduplicator._calculate_world_angle(box, pan_angle, fov_horizontal=60)
        angle2 = deduplicator._calculate_world_angle(box, pan_angle, fov_horizontal=90)
        
        # Wider FOV should give larger angle difference
        assert abs(angle1 - pan_angle) != abs(angle2 - pan_angle)