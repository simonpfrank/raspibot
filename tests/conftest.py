"""Pytest configuration and fixtures for the Raspibot project.

This module provides common fixtures and configuration for all tests.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock
from typing import Generator

from raspibot.hardware.servos.servo_interface import ServoController, Camera


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_servo_controller() -> Mock:
    """Provide a mock servo controller for testing."""
    mock_controller = Mock(spec=ServoController)
    
    # Mock the methods
    mock_controller.set_angle.return_value = None
    mock_controller.get_angle.return_value = 90.0
    mock_controller.initialize.return_value = None
    mock_controller.shutdown.return_value = None
    
    return mock_controller


@pytest.fixture
def mock_camera() -> Mock:
    """Provide a mock camera for testing."""
    mock_camera = Mock(spec=Camera)
    
    # Mock the methods
    mock_camera.capture_frame.return_value = "mock_frame_data"
    mock_camera.start_stream.return_value = None
    mock_camera.stop_stream.return_value = None
    mock_camera.set_resolution.return_value = None
    
    return mock_camera


@pytest.fixture
def clean_environment() -> Generator[None, None, None]:
    """Provide a clean environment for testing configuration."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Clear environment variables that might interfere with tests
    test_env_vars = [
        'RASPIBOT_DEBUG',
        'RASPIBOT_LOG_LEVEL', 
        'RASPIBOT_LOG_TO_FILE',
        'RASPIBOT_LOG_STACKTRACE'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_logs_dir() -> Generator[str, None, None]:
    """Provide a test logs directory."""
    test_logs_dir = "data/logs"
    
    # Create the directory if it doesn't exist
    os.makedirs(test_logs_dir, exist_ok=True)
    
    yield test_logs_dir
    
    # Clean up test log files
    for file in os.listdir(test_logs_dir):
        if file.endswith('.log'):
            os.remove(os.path.join(test_logs_dir, file))


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark tests in unit/ directory as unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark tests in integration/ directory as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration) 