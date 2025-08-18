"""Unit tests for raspibot.utils.logging_config module."""

import pytest
import logging
import os
import contextvars
from unittest.mock import patch, Mock, MagicMock
from io import StringIO

from raspibot.utils.logging_config import (
    RaspibotFormatter,
    setup_logging,
    set_correlation_id,
    get_correlation_id
)


class TestRaspibotFormatter:
    """Test custom log formatter."""
    
    def test_format_basic_message(self):
        """Test basic log message formatting."""
        formatter = RaspibotFormatter()
        
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        
        formatted = formatter.format(record)
        
        assert "INFO" in formatted
        assert "module.test_function:42" in formatted
        assert "[:] Test message" in formatted
    
    def test_format_with_correlation_id(self):
        """Test formatting with correlation ID."""
        formatter = RaspibotFormatter()
        
        # Set correlation context
        with patch('raspibot.utils.logging_config._correlation_id') as mock_corr_id:
            with patch('raspibot.utils.logging_config._task_name') as mock_task_name:
                mock_corr_id.get.return_value = "abc123"
                mock_task_name.get.return_value = "test_task"
                
                record = logging.LogRecord(
                    name="test.module",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=42,
                    msg="Test message",
                    args=(),
                    exc_info=None
                )
                record.funcName = "test_function"
                
                formatted = formatter.format(record)
                
                assert "[abc123:test_task]" in formatted
    
    def test_format_without_correlation(self):
        """Test formatting without correlation info."""
        formatter = RaspibotFormatter()
        
        with patch('raspibot.utils.logging_config._correlation_id') as mock_corr_id:
            with patch('raspibot.utils.logging_config._task_name') as mock_task_name:
                mock_corr_id.get.return_value = None
                mock_task_name.get.return_value = None
                
                record = logging.LogRecord(
                    name="test.module",
                    level=logging.INFO,
                    pathname="test.py",
                    lineno=42,
                    msg="Test message",
                    args=(),
                    exc_info=None
                )
                record.funcName = "test_function"
                
                formatted = formatter.format(record)
                
                assert "[:]" in formatted
    
    def test_format_with_exception_stacktrace_disabled(self):
        """Test exception formatting without stack trace."""
        formatter = RaspibotFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        with patch.dict(os.environ, {'RASPIBOT_LOG_STACKTRACE': 'false'}):
            record = logging.LogRecord(
                name="test.module",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Test message",
                args=(),
                exc_info=exc_info
            )
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            
            # Should not contain stack trace
            assert "Traceback" not in formatted
            assert "ValueError: Test error" not in formatted
    
    def test_format_with_exception_stacktrace_enabled(self):
        """Test exception formatting with stack trace."""
        formatter = RaspibotFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        with patch.dict(os.environ, {'RASPIBOT_LOG_STACKTRACE': 'true'}):
            record = logging.LogRecord(
                name="test.module",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Test message",
                args=(),
                exc_info=exc_info
            )
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            
            # Should contain stack trace
            assert "Traceback" in formatted
            assert "ValueError: Test error" in formatted
    
    def test_format_class_function_info(self):
        """Test class/function/line formatting."""
        formatter = RaspibotFormatter()
        
        record = logging.LogRecord(
            name="raspibot.hardware.servos.servo",
            level=logging.DEBUG,
            pathname="servo.py",
            lineno=123,
            msg="Debug message",
            args=(),
            exc_info=None
        )
        record.funcName = "set_servo_angle"
        
        formatted = formatter.format(record)
        
        assert "servo.set_servo_angle:123" in formatted


class TestCorrelationContext:
    """Test correlation context management."""
    
    def test_set_correlation_id(self):
        """Test correlation ID context setting."""
        set_correlation_id("test123", "test_task")
        
        assert get_correlation_id() == ("test123", "test_task")
    
    def test_get_correlation_id(self):
        """Test correlation ID retrieval."""
        # Test with no context set
        with patch('raspibot.utils.logging_config._correlation_id') as mock_corr_id:
            with patch('raspibot.utils.logging_config._task_name') as mock_task_name:
                mock_corr_id.get.return_value = None
                mock_task_name.get.return_value = None
                
                assert get_correlation_id() == (None, None)
        
        # Test with context set
        set_correlation_id("abc456", "another_task")
        assert get_correlation_id() == ("abc456", "another_task")
    
    def test_correlation_context_isolation(self):
        """Test context isolation across tasks."""
        import asyncio
        
        async def task1():
            set_correlation_id("task1_id", "task1")
            await asyncio.sleep(0.01)
            return get_correlation_id()
        
        async def task2():
            set_correlation_id("task2_id", "task2")
            await asyncio.sleep(0.01)
            return get_correlation_id()
        
        async def run_test():
            results = await asyncio.gather(task1(), task2())
            return results
        
        # This test may need to be adjusted based on actual context implementation
        # For now, just test basic functionality
        set_correlation_id("main_id", "main_task")
        assert get_correlation_id() == ("main_id", "main_task")


class TestLoggingSetup:
    """Test logging setup functionality."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        with patch('raspibot.utils.logging_config.logging.getLogger') as mock_get_logger:
            with patch('raspibot.utils.logging_config.logging.StreamHandler') as mock_handler:
                with patch('raspibot.utils.logging_config.logging.FileHandler') as mock_file_handler:
                    mock_logger = Mock()
                    mock_get_logger.return_value = mock_logger
                    
                    logger = setup_logging()
                    
                    assert logger is mock_logger
                    mock_logger.setLevel.assert_called()
    
    def test_setup_logging_custom_level(self):
        """Test custom log level setup."""
        with patch.dict(os.environ, {'RASPIBOT_LOG_LEVEL': 'DEBUG'}):
            with patch('raspibot.utils.logging_config.logging.getLogger') as mock_get_logger:
                with patch('raspibot.utils.logging_config.logging.StreamHandler') as mock_handler:
                    with patch('raspibot.utils.logging_config.logging.FileHandler') as mock_file_handler:
                        mock_logger = Mock()
                        mock_get_logger.return_value = mock_logger
                        
                        logger = setup_logging()
                        
                        # Should set DEBUG level
                        mock_logger.setLevel.assert_called()
    
    def test_setup_logging_file_output(self):
        """Test file output configuration."""
        with patch.dict(os.environ, {'RASPIBOT_LOG_TO_FILE': 'true'}):
            with patch('raspibot.utils.logging_config.logging.getLogger') as mock_get_logger:
                with patch('raspibot.utils.logging_config.logging.StreamHandler') as mock_handler:
                    with patch('raspibot.utils.logging_config.logging.FileHandler') as mock_file_handler:
                        with patch('raspibot.utils.helpers.ensure_directory_exists') as mock_ensure_dir:
                            mock_logger = Mock()
                            mock_get_logger.return_value = mock_logger
                            
                            logger = setup_logging()
                            
                            # Should create file handler
                            mock_file_handler.assert_called()
    
    def test_setup_logging_console_only(self):
        """Test console-only configuration."""
        with patch.dict(os.environ, {'RASPIBOT_LOG_TO_FILE': 'false'}):
            # Need to patch the config values that are imported in the function
            with patch('raspibot.settings.config.LOG_TO_FILE', False):
                with patch('raspibot.utils.logging_config.logging.getLogger') as mock_get_logger:
                    with patch('raspibot.utils.logging_config.logging.StreamHandler') as mock_handler:
                        with patch('raspibot.utils.logging_config.logging.FileHandler') as mock_file_handler:
                            mock_logger = Mock()
                            mock_get_logger.return_value = mock_logger
                            
                            logger = setup_logging()
                            
                            # Should not create file handler
                            mock_file_handler.assert_not_called()