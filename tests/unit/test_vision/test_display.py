"""Unit tests for Display class."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from raspibot.vision.display import Display


class TestDisplay:
    """Test Display class functionality."""

    @patch('cv2.namedWindow')
    def test_display_initialization(self, mock_named_window):
        """Test display initialization."""
        display = Display("Test Window")
        
        assert display.window_name == "Test Window"
        assert display.font_scale == 1.0
        assert display.font_thickness == 2
        mock_named_window.assert_called_once_with("Test Window", 1)  # WINDOW_AUTOSIZE

    @patch('cv2.namedWindow')
    def test_display_custom_params(self, mock_named_window):
        """Test display with custom parameters."""
        display = Display(window_name="Custom", font_scale=0.8, font_thickness=1)
        
        assert display.window_name == "Custom"
        assert display.font_scale == 0.8
        assert display.font_thickness == 1

    @patch('cv2.namedWindow')
    @patch('cv2.imshow')
    @patch('cv2.waitKey')
    def test_show_frame_basic(self, mock_wait_key, mock_imshow, mock_named_window):
        """Test basic frame display."""
        mock_wait_key.return_value = ord('a')  # Not 'q'
        
        display = Display()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = display.show_frame(frame)
        
        assert result is True
        mock_imshow.assert_called_once()
        mock_wait_key.assert_called_once_with(1)

    @patch('cv2.namedWindow')
    @patch('cv2.imshow')
    @patch('cv2.waitKey')
    def test_show_frame_quit_key(self, mock_wait_key, mock_imshow, mock_named_window):
        """Test frame display with quit key pressed."""
        mock_wait_key.return_value = ord('q')
        
        display = Display()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = display.show_frame(frame)
        
        assert result is False

    @patch('cv2.namedWindow')
    def test_show_frame_none(self, mock_named_window):
        """Test frame display with None frame."""
        display = Display()
        
        result = display.show_frame(None)
        
        assert result is True

    @patch('cv2.namedWindow')
    @patch('cv2.imshow')
    @patch('cv2.waitKey')
    @patch('cv2.rectangle')
    @patch('cv2.circle')
    @patch('cv2.putText')
    def test_show_frame_with_faces(self, mock_put_text, mock_circle, mock_rectangle, 
                                  mock_wait_key, mock_imshow, mock_named_window):
        """Test frame display with face detection boxes."""
        mock_wait_key.return_value = ord('a')
        
        display = Display()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = [(100, 100, 80, 80), (300, 200, 60, 60)]
        stable_faces = [(100, 100, 80, 80)]
        
        result = display.show_frame(
            frame=frame,
            faces=faces,
            stable_faces=stable_faces,
            camera_fps=30.0,
            detection_fps=15.0,
            servo_position=(0.5, -0.2)
        )
        
        assert result is True
        # Should draw rectangles and circles for faces
        assert mock_rectangle.call_count >= 2
        assert mock_circle.call_count >= 2
        # Should draw status text
        assert mock_put_text.call_count >= 5

    @patch('cv2.namedWindow')
    @patch('cv2.destroyWindow')
    def test_close_display(self, mock_destroy_window, mock_named_window):
        """Test display close."""
        display = Display("Test Window")
        display.close()
        
        mock_destroy_window.assert_called_once_with("Test Window")

    @patch('cv2.namedWindow')
    @patch('cv2.imshow')
    @patch('cv2.waitKey')
    @patch('cv2.putText')
    def test_show_error_message(self, mock_put_text, mock_wait_key, mock_imshow, mock_named_window):
        """Test error message display."""
        display = Display()
        
        display.show_error_message("Test error\nSecond line")
        
        mock_imshow.assert_called()
        mock_wait_key.assert_called_with(0)
        # Should put text for each line plus instruction
        assert mock_put_text.call_count >= 3

    @patch('cv2.namedWindow')
    def test_context_manager(self, mock_named_window):
        """Test display as context manager."""
        with patch.object(Display, 'close') as mock_close:
            with Display() as display:
                assert isinstance(display, Display)
            mock_close.assert_called_once()

    @patch('cv2.namedWindow')
    @patch('cv2.imshow')
    @patch('cv2.waitKey')
    def test_show_frame_exception(self, mock_wait_key, mock_imshow, mock_named_window):
        """Test frame display with exception."""
        mock_imshow.side_effect = Exception("Display error")
        
        display = Display()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = display.show_frame(frame)
        
        assert result is False 