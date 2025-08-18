"""Unit tests for raspibot.core.room_scan module."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from raspibot.core.room_scan import RoomScanner


class TestRoomScannerInitialization:
    """Test RoomScanner initialization."""
    
    def test_init_default_parameters(self):
        """Test default parameter initialization."""
        with patch('raspibot.core.room_scan.Camera') as mock_camera_class:
            with patch('raspibot.core.room_scan.get_servo_controller') as mock_servo_func:
                mock_camera_class.return_value = Mock()
                mock_servo_func.return_value = Mock()
                
                scanner = RoomScanner()
                
                assert scanner.face_detection is False
                assert scanner.frames_per_position == 6
                assert scanner.settling_time == 1.0
                assert scanner.confidence_threshold == 0.6
                assert scanner.scan_tilt == 90.0
                assert scanner.last_scan_data == []
                assert scanner.scan_positions == []
    
    def test_init_custom_parameters(self):
        """Test custom parameter setup."""
        with patch('raspibot.core.room_scan.Camera') as mock_camera_class:
            with patch('raspibot.core.room_scan.get_servo_controller') as mock_servo_func:
                mock_camera = Mock()
                mock_servo = Mock()
                mock_camera_class.return_value = mock_camera
                mock_servo_func.return_value = mock_servo
                
                scanner = RoomScanner(
                    camera=mock_camera,
                    servo_controller=mock_servo,
                    face_detection=True,
                    frames_per_position=10,
                    settling_time=2.0,
                    confidence_threshold=0.8,
                    scan_tilt=45.0,
                    fov_degrees=90.0,
                    overlap_degrees=15.0
                )
                
                assert scanner.camera is mock_camera
                assert scanner.servo_controller is mock_servo
                assert scanner.face_detection is True
                assert scanner.frames_per_position == 10
                assert scanner.settling_time == 2.0
                assert scanner.confidence_threshold == 0.8
                assert scanner.scan_tilt == 45.0
    
    def test_init_with_mocked_hardware(self):
        """Test initialization with mocked hardware."""
        mock_camera = Mock()
        mock_servo = Mock()
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner()
                
                assert scanner.camera is mock_camera
                assert scanner.servo_controller is mock_servo
                assert hasattr(scanner, 'deduplicator')
                assert hasattr(scanner, 'scan_pattern')


class TestScanProcess:
    """Test room scanning process."""
    
    def test_scan_room_empty_environment(self):
        """Test scan with no objects detected."""
        mock_camera = Mock()
        mock_servo = Mock()
        mock_camera.tracked_objects = []
        mock_camera._running = False
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=2, settling_time=0.1)
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=[45.0, 90.0, 135.0]):
                    with patch('time.sleep'):  # Mock sleep to speed up test
                        with patch('threading.Thread'):  # Mock threading
                            result = scanner.scan_room()
                
                assert isinstance(result, list)
                assert len(result) == 0  # No objects detected
                assert scanner.last_scan_data == result
    
    def test_scan_room_with_objects(self, sample_detections):
        """Test scan with detected objects."""
        mock_camera = Mock()
        mock_servo = Mock()
        
        # Mock tracked objects
        mock_tracked_obj = {
            "last_detection": {
                "label": "person",
                "score": 0.8,
                "box": [100, 100, 50, 100]
            }
        }
        mock_camera.tracked_objects = [mock_tracked_obj]
        mock_camera._running = False
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=1, settling_time=0.1)
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=[90.0]):
                    with patch.object(scanner.deduplicator, 'deduplicate', return_value=sample_detections[:1]):
                        with patch('time.sleep'):
                            with patch('threading.Thread'):
                                result = scanner.scan_room()
                
                assert len(result) == 1
                assert result[0]["label"] == "person"
                assert scanner.last_scan_data == result
    
    def test_scan_room_camera_startup(self):
        """Test camera initialization during scan."""
        mock_camera = Mock()
        mock_servo = Mock()
        mock_camera._running = False  # Camera not running initially
        mock_camera.tracked_objects = []
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=1, settling_time=0.1)
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=[90.0]):
                    with patch('time.sleep'):
                        with patch('threading.Thread'):
                            scanner.scan_room()
                
                # Should start camera and create detection thread
                mock_camera.start.assert_called_once()
    
    def test_scan_room_position_movement(self):
        """Test servo movement through positions."""
        mock_camera = Mock()
        mock_servo = Mock()
        mock_camera.tracked_objects = []
        mock_camera._running = True  # Camera already running
        
        positions = [30.0, 90.0, 150.0]
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=1, settling_time=0.1)
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=positions):
                    with patch.object(scanner.scan_pattern, 'move_to_position') as mock_move:
                        with patch('time.sleep'):
                            scanner.scan_room()
                
                # Should move to each position plus return to center
                assert mock_move.call_count == len(positions) + 1
                
                # Check specific position calls
                position_calls = mock_move.call_args_list[:-1]  # Exclude return to center
                for i, call in enumerate(position_calls):
                    assert call[0][1] == positions[i]  # Pan angle
                    assert call[0][2] == scanner.scan_tilt  # Tilt angle
    
    def test_scan_room_detection_capture(self):
        """Test detection capture at each position."""
        mock_camera = Mock()
        mock_servo = Mock()
        
        # Mock detection data
        mock_detection = {
            "label": "chair",
            "score": 0.7,
            "box": [200, 150, 80, 120]
        }
        mock_tracked_obj = {"last_detection": mock_detection}
        mock_camera.tracked_objects = [mock_tracked_obj]
        mock_camera._running = True
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=2, settling_time=0.1)
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=[90.0]):
                    with patch('time.sleep'):
                        result = scanner.scan_room()
                
                # Should have captured detections
                mock_camera.clear_tracked_objects.assert_called()
    
    def test_scan_room_return_to_center(self):
        """Test return to center after scan."""
        mock_camera = Mock()
        mock_servo = Mock()
        mock_camera.tracked_objects = []
        mock_camera._running = True
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner()
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=[45.0, 135.0]):
                    with patch.object(scanner.scan_pattern, 'move_to_position') as mock_move:
                        with patch('time.sleep'):
                            scanner.scan_room()
                
                # Last call should be return to center
                last_call = mock_move.call_args_list[-1]
                assert last_call[0][1] == 90  # SERVO_PAN_CENTER
                assert last_call[0][2] == 90  # SERVO_TILT_CENTER


class TestAsyncScanning:
    """Test async scanning functionality."""
    
    @pytest.mark.asyncio
    async def test_scan_room_async_empty(self):
        """Test async scan with no objects."""
        mock_camera = Mock()
        mock_servo = Mock()
        mock_camera.tracked_objects = []
        mock_camera._running = False
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=1, settling_time=0.1)
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=[90.0]):
                    with patch.object(scanner.scan_pattern, 'move_to_position_async', new_callable=AsyncMock):
                        with patch.object(scanner.deduplicator, 'deduplicate_async', new_callable=AsyncMock, return_value=[]):
                            with patch('asyncio.sleep', new_callable=AsyncMock):
                                with patch('asyncio.to_thread', new_callable=AsyncMock):
                                    result = await scanner.scan_room_async()
                
                assert isinstance(result, list)
                assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_scan_room_async_with_objects(self, sample_detections):
        """Test async scan with objects."""
        mock_camera = Mock()
        mock_servo = Mock()
        
        mock_tracked_obj = {
            "last_detection": {
                "label": "person",
                "score": 0.85,
                "box": [100, 100, 50, 100]
            }
        }
        mock_camera.tracked_objects = [mock_tracked_obj]
        mock_camera._running = True
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=1, settling_time=0.1)
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', return_value=[90.0]):
                    with patch.object(scanner.deduplicator, 'deduplicate_async', new_callable=AsyncMock, return_value=sample_detections[:1]):
                        with patch.object(scanner.scan_pattern, 'move_to_position_async', new_callable=AsyncMock):
                            with patch('asyncio.sleep', new_callable=AsyncMock):
                                with patch('asyncio.to_thread', new_callable=AsyncMock):
                                    result = await scanner.scan_room_async()
                
                assert len(result) == 1
                assert result[0]["label"] == "person"
    
    @pytest.mark.asyncio 
    async def test_scan_room_async_error_handling(self):
        """Test async error handling."""
        mock_camera = Mock()
        mock_servo = Mock()
        mock_camera._running = True
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner()
                
                with patch.object(scanner.scan_pattern, 'calculate_positions', side_effect=Exception("Test error")):
                    with pytest.raises(Exception, match="Test error"):
                        await scanner.scan_room_async()


class TestConfigurationMethods:
    """Test scanner configuration methods."""
    
    def test_enable_face_detection(self):
        """Test face detection toggle."""
        with patch('raspibot.core.room_scan.Camera') as mock_camera_class:
            with patch('raspibot.core.room_scan.get_servo_controller') as mock_servo_func:
                scanner = RoomScanner()
                
                # Test enabling
                scanner.enable_face_detection(True)
                assert scanner.face_detection is True
                
                # Test disabling
                scanner.enable_face_detection(False)
                assert scanner.face_detection is False
    
    def test_get_scan_summary_no_data(self):
        """Test summary with no scan data."""
        with patch('raspibot.core.room_scan.Camera') as mock_camera_class:
            with patch('raspibot.core.room_scan.get_servo_controller') as mock_servo_func:
                scanner = RoomScanner()
                
                summary = scanner.get_scan_summary()
                
                assert "error" in summary
                assert summary["error"] == "No scan data available"
    
    def test_get_scan_summary_with_data(self):
        """Test summary generation with data."""
        mock_scan_data = [
            {
                "label": "person",
                "confidence": 0.8,
                "world_angle": 45.0
            },
            {
                "label": "chair", 
                "confidence": 0.7,
                "world_angle": 90.0
            },
            {
                "label": "person",
                "confidence": 0.9,
                "world_angle": 135.0
            }
        ]
        
        with patch('raspibot.core.room_scan.Camera') as mock_camera_class:
            with patch('raspibot.core.room_scan.get_servo_controller') as mock_servo_func:
                scanner = RoomScanner()
                scanner.last_scan_data = mock_scan_data
                scanner.scan_positions = [30.0, 90.0, 150.0]
                
                summary = scanner.get_scan_summary()
                
                assert summary["total_objects"] == 3
                assert summary["scan_positions"] == 3
                assert summary["objects_by_type"]["person"] == 2
                assert summary["objects_by_type"]["chair"] == 1
                assert summary["position_angles"] == [30.0, 90.0, 150.0]


class TestDetectionCapture:
    """Test detection capture mechanics."""
    
    def test_capture_detections_at_position(self):
        """Test detection capture mechanics."""
        mock_camera = Mock()
        mock_servo = Mock()
        
        # Mock detection
        mock_detection = {
            "label": "bottle",
            "score": 0.75,
            "box": [150, 200, 30, 80]
        }
        mock_tracked_obj = {"last_detection": mock_detection}
        mock_camera.tracked_objects = [mock_tracked_obj]
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=3, confidence_threshold=0.7)
                
                with patch('time.sleep'):
                    detections = scanner._capture_detections_at_position(90.0, 45.0, 1)
                
                # Should capture detections above confidence threshold
                assert len(detections) > 0
                assert detections[0]["label"] == "bottle"
                assert detections[0]["confidence"] == 0.75
                assert detections[0]["pan_angle"] == 90.0
    
    def test_capture_detections_confidence_filtering(self):
        """Test confidence threshold filtering."""
        mock_camera = Mock()
        mock_servo = Mock()
        
        # Mock low confidence detection
        mock_detection = {
            "label": "cup",
            "score": 0.3,  # Below threshold
            "box": [100, 100, 20, 40]
        }
        mock_tracked_obj = {"last_detection": mock_detection}
        mock_camera.tracked_objects = [mock_tracked_obj]
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(confidence_threshold=0.6)
                
                with patch('time.sleep'):
                    detections = scanner._capture_detections_at_position(90.0, 45.0, 0)
                
                # Should filter out low confidence detections
                assert len(detections) == 0
    
    def test_capture_detections_empty_tracked_objects(self):
        """Test with no tracked objects."""
        mock_camera = Mock()
        mock_servo = Mock()
        mock_camera.tracked_objects = []  # No objects
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner()
                
                with patch('time.sleep'):
                    detections = scanner._capture_detections_at_position(90.0, 45.0, 0)
                
                assert len(detections) == 0
    
    @pytest.mark.asyncio
    async def test_capture_detections_async(self):
        """Test async detection capture."""
        mock_camera = Mock()
        mock_servo = Mock()
        
        mock_detection = {
            "label": "book",
            "score": 0.8,
            "box": [50, 50, 40, 60]
        }
        mock_tracked_obj = {"last_detection": mock_detection}
        mock_camera.tracked_objects = [mock_tracked_obj]
        
        with patch('raspibot.core.room_scan.Camera', return_value=mock_camera):
            with patch('raspibot.core.room_scan.get_servo_controller', return_value=mock_servo):
                scanner = RoomScanner(frames_per_position=2)
                
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    with patch('asyncio.to_thread', new_callable=AsyncMock, return_value=mock_camera.tracked_objects):
                        detections = await scanner._capture_detections_at_position_async(45.0, 90.0, 0)
                
                # Should capture async detections
                assert len(detections) > 0