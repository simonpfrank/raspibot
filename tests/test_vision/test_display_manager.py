"""Unit tests for display manager and handlers."""

import pytest
import os
import cv2
import numpy as np
from unittest.mock import patch, MagicMock, Mock

from raspibot.vision.display_manager import (
    DisplayManager, 
    get_screen_dimensions, 
    center_window_on_screen,
    get_unsupported_environment_message
)
from raspibot.vision.display_handlers import (
    BaseDisplayHandler,
    ConnectedDisplayHandler,
    RaspberryConnectDisplayHandler,
    HeadlessDisplayHandler
)


class TestDisplayManager:
    """Test cases for DisplayManager class."""
    
    def test_init_auto_detect(self):
        """Test DisplayManager initialization with auto-detection."""
        with patch('raspibot.vision.display_manager.DisplayManager._detect_display_method') as mock_detect:
            mock_detect.return_value = 'headless'
            
            manager = DisplayManager(auto_detect=True)
            
            assert manager.auto_detect is True
            assert manager.display_method == 'headless'
            mock_detect.assert_called_once()
    
    def test_init_manual_mode(self):
        """Test DisplayManager initialization with manual mode."""
        manager = DisplayManager(auto_detect=False, mode='headless')
        
        assert manager.auto_detect is False
        assert manager.display_method == 'headless'
    
    def test_init_invalid_mode(self):
        """Test DisplayManager initialization with invalid mode."""
        with pytest.raises(ValueError, match="Unsupported display method"):
            DisplayManager(auto_detect=False, mode='invalid_mode')
    
    def test_detect_display_method_connected_screen(self):
        """Test detection of connected screen environment."""
        with patch('cv2.namedWindow'), patch('cv2.destroyWindow'):
            manager = DisplayManager(auto_detect=False)
            result = manager._detect_display_method()
            
            assert result == 'connected_screen'
    
    def test_detect_display_method_raspberry_connect(self):
        """Test detection of Raspberry Pi Connect environment."""
        with patch('cv2.namedWindow', side_effect=Exception("No display")):
            with patch('os.path.exists') as mock_exists:
                mock_exists.side_effect = lambda path: path == '/tmp/wayvnc/wayvncctl.sock' or path == '/tmp/.X11-unix/X0'
                
                with patch.dict(os.environ, {}, clear=True):
                    manager = DisplayManager(auto_detect=False)
                    result = manager._detect_display_method()
                    
                    assert result == 'raspberry_connect'
                    assert os.environ['DISPLAY'] == ':0'
    
    def test_detect_display_method_headless(self):
        """Test detection of headless environment."""
        with patch('cv2.namedWindow', side_effect=Exception("No display")):
            with patch('os.path.exists', return_value=False):
                manager = DisplayManager(auto_detect=False)
                result = manager._detect_display_method()
                
                assert result == 'headless'
    
    def test_get_display_method(self):
        """Test getting display method."""
        manager = DisplayManager(auto_detect=False, mode='headless')
        assert manager.get_display_method() == 'headless'
    
    def test_get_display_handler(self):
        """Test getting display handler."""
        manager = DisplayManager(auto_detect=False, mode='headless')
        handler = manager.get_display_handler()
        
        assert isinstance(handler, HeadlessDisplayHandler)
    
    def test_show_frame(self):
        """Test showing frame through display manager."""
        manager = DisplayManager(auto_detect=False, mode='headless')
        
        display_data = {
            'frame': np.zeros((480, 640, 3), dtype=np.uint8),
            'fps': 30.0,
            'frame_count': 1
        }
        
        result = manager.show_frame(display_data)
        assert result is True
    
    def test_context_manager(self):
        """Test DisplayManager as context manager."""
        with DisplayManager(auto_detect=False, mode='headless') as manager:
            assert manager.display_method == 'headless'
            # Context manager should work without errors


class TestDisplayHandlers:
    """Test cases for display handlers."""
    
    def test_base_display_handler_abstract(self):
        """Test that BaseDisplayHandler is abstract."""
        with pytest.raises(TypeError):
            BaseDisplayHandler()
    
    def test_connected_display_handler_init(self):
        """Test ConnectedDisplayHandler initialization."""
        handler = ConnectedDisplayHandler("test_window")
        
        assert handler.window_name == "test_window"
        assert handler.display_name == "Connected Screen"
        assert handler.show_info_overlay is True
    
    def test_connected_display_handler_setup_window_success(self):
        """Test successful window setup for connected display."""
        with patch('cv2.namedWindow'), patch('cv2.resizeWindow'), patch('cv2.moveWindow'):
            with patch('raspibot.vision.display_handlers.get_screen_dimensions', return_value=(1920, 1080)):
                handler = ConnectedDisplayHandler("test_window")
                result = handler.setup_window()
                
                assert result is True
                assert handler.is_initialized is True
    
    def test_connected_display_handler_setup_window_failure(self):
        """Test failed window setup for connected display."""
        with patch('cv2.namedWindow', side_effect=Exception("Display error")):
            handler = ConnectedDisplayHandler("test_window")
            result = handler.setup_window()
            
            assert result is False
            assert handler.is_initialized is False
    
    def test_connected_display_handler_show_frame(self):
        """Test showing frame on connected display."""
        with patch('cv2.namedWindow'), patch('cv2.resizeWindow'), patch('cv2.moveWindow'):
            with patch('cv2.imshow'), patch('cv2.waitKey', return_value=ord('q')):
                with patch('raspibot.vision.display_handlers.get_screen_dimensions', return_value=(1920, 1080)):
                    handler = ConnectedDisplayHandler("test_window")
                    handler.setup_window()
                    
                    display_data = {
                        'frame': np.zeros((480, 640, 3), dtype=np.uint8),
                        'show_info': True
                    }
                    
                    result = handler.show_frame(display_data)
                    assert result is False  # 'q' key pressed
    
    def test_raspberry_connect_display_handler_init(self):
        """Test RaspberryConnectDisplayHandler initialization."""
        handler = RaspberryConnectDisplayHandler("test_window")
        
        assert handler.window_name == "test_window"
        assert handler.display_name == "Raspberry Pi Connect"
    
    def test_headless_display_handler_init(self):
        """Test HeadlessDisplayHandler initialization."""
        handler = HeadlessDisplayHandler("test_window")
        
        assert handler.window_name == "test_window"
        assert handler.display_name == "Headless Mode"
        assert handler.log_interval == 5.0
    
    def test_headless_display_handler_setup_window(self):
        """Test headless display window setup."""
        handler = HeadlessDisplayHandler("test_window")
        result = handler.setup_window()
        
        assert result is True
        assert handler.is_initialized is True
    
    def test_headless_display_handler_show_frame(self):
        """Test showing frame in headless mode."""
        handler = HeadlessDisplayHandler("test_window")
        handler.setup_window()
        
        display_data = {
            'frame': np.zeros((480, 640, 3), dtype=np.uint8),
            'fps': 30.0,
            'frame_count': 1,
            'camera_info': {'type': 'TestCamera'}
        }
        
        result = handler.show_frame(display_data)
        assert result is True
    
    def test_headless_display_handler_get_key(self):
        """Test getting key in headless mode."""
        handler = HeadlessDisplayHandler("test_window")
        key = handler.get_key()
        
        assert key == -1  # Always returns -1 in headless mode


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_get_screen_dimensions_xrandr_success(self):
        """Test getting screen dimensions via xrandr."""
        mock_output = "Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 8192 x 8192\n"
        mock_output += "HDMI-A-0 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 509mm x 286mm\n"
        mock_output += "   1920x1080     60.00*+  50.00    59.94\n"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_output
            
            with patch.dict(os.environ, {'DISPLAY': ':0'}):
                width, height = get_screen_dimensions()
                
                assert width == 1920
                assert height == 1080
    
    def test_get_screen_dimensions_fallback(self):
        """Test getting screen dimensions with fallback."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with patch.dict(os.environ, {'DISPLAY': ':0'}):
                width, height = get_screen_dimensions()
                
                # Should return first common resolution
                assert width == 1920
                assert height == 1080
    
    def test_get_screen_dimensions_no_display(self):
        """Test getting screen dimensions without display."""
        with patch.dict(os.environ, {}, clear=True):
            width, height = get_screen_dimensions()
            
            # Should return fallback resolution
            assert width == 1280
            assert height == 720
    
    def test_center_window_on_screen_success(self):
        """Test centering window on screen."""
        with patch('raspibot.vision.display_manager.get_screen_dimensions', return_value=(1920, 1080)):
            with patch('cv2.moveWindow') as mock_move:
                center_window_on_screen("test_window", 800, 600)
                
                # Should center 800x600 window on 1920x1080 screen
                expected_x = (1920 - 800) // 2  # 560
                expected_y = (1080 - 600) // 2  # 240
                mock_move.assert_called_once_with("test_window", expected_x, expected_y)
    
    def test_center_window_on_screen_failure(self):
        """Test centering window when it fails."""
        with patch('raspibot.vision.display_manager.get_screen_dimensions', side_effect=Exception("Error")):
            with patch('cv2.moveWindow', side_effect=Exception("Move error")):
                # Should not raise exception
                center_window_on_screen("test_window", 800, 600)
    
    def test_get_unsupported_environment_message(self):
        """Test getting unsupported environment message."""
        message = get_unsupported_environment_message()
        
        assert "Display Environment Not Supported" in message
        assert "Connected Screen" in message
        assert "Raspberry Pi Connect" in message
        assert "Headless Mode" in message
        assert "docs/camera_display_modes.md" in message


class TestDisplayHandlerIntegration:
    """Integration tests for display handlers."""
    
    def test_connected_display_handler_info_overlay(self):
        """Test info overlay on connected display."""
        with patch('cv2.namedWindow'), patch('cv2.resizeWindow'), patch('cv2.moveWindow'):
            with patch('cv2.imshow'), patch('cv2.waitKey', return_value=-1):
                with patch('raspibot.vision.display_handlers.get_screen_dimensions', return_value=(1920, 1080)):
                    handler = ConnectedDisplayHandler("test_window")
                    handler.setup_window()
                    
                    # Create test frame
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    
                    display_data = {
                        'frame': frame,
                        'show_info': True,
                        'fps': 30.0,
                        'frame_count': 100,
                        'camera_info': {
                            'type': 'TestCamera',
                            'resolution': (640, 480)
                        }
                    }
                    
                    # This should not raise any exceptions
                    result = handler.show_frame(display_data)
                    assert result is True
    
    def test_headless_display_handler_logging(self):
        """Test logging in headless display handler."""
        with patch('time.time', return_value=1000.0):
            handler = HeadlessDisplayHandler("test_window")
            handler.setup_window()
            
            display_data = {
                'frame': np.zeros((480, 640, 3), dtype=np.uint8),
                'fps': 25.5,
                'frame_count': 150,
                'camera_info': {'type': 'TestCamera'}
            }
            
            # Should log status information
            result = handler.show_frame(display_data)
            assert result is True
    
    def test_display_handler_cleanup(self):
        """Test display handler cleanup."""
        with patch('cv2.namedWindow'), patch('cv2.resizeWindow'), patch('cv2.moveWindow'):
            with patch('cv2.destroyWindow') as mock_destroy:
                with patch('raspibot.vision.display_handlers.get_screen_dimensions', return_value=(1920, 1080)):
                    handler = ConnectedDisplayHandler("test_window")
                    handler.setup_window()
                    handler.close()
                    
                    mock_destroy.assert_called_once_with("test_window") 