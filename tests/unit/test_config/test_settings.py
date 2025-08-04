"""Tests for configuration settings module.

This module tests the simple, module-level configuration approach
using environment variables with sensible defaults.
"""

import os
import importlib
from unittest.mock import patch
import pytest

# Import the settings module (will be created after tests)
# from raspibot.settings import settings


class TestAppSettings:
    """Test application settings loading from environment variables."""

    def test_debug_default_false(self):
        """Test that DEBUG defaults to False when environment variable is not set."""
        # This test will fail until we implement the settings module
        from raspibot.settings import settings
        assert settings.DEBUG is False

    def test_debug_from_env_true(self, monkeypatch):
        """Test that DEBUG loads as True when RASPIBOT_DEBUG=true."""
        # This test will fail until we implement the settings module
        monkeypatch.setenv('RASPIBOT_DEBUG', 'true')
        importlib.reload(importlib.import_module('raspibot.settings.config'))
        from raspibot.settings import settings
        assert settings.DEBUG is True

    def test_debug_from_env_false(self, monkeypatch):
        """Test that DEBUG loads as False when RASPIBOT_DEBUG=false."""
        monkeypatch.setenv('RASPIBOT_DEBUG', 'false')
        importlib.reload(importlib.import_module('raspibot.settings.config'))
        from raspibot.settings import settings
        assert settings.DEBUG is False

    def test_log_level_default(self):
        """Test that LOG_LEVEL defaults to 'INFO'."""
        from raspibot.settings import settings
        assert settings.LOG_LEVEL == 'INFO'

    def test_log_level_from_env(self, monkeypatch):
        """Test that LOG_LEVEL loads from RASPIBOT_LOG_LEVEL environment variable."""
        monkeypatch.setenv('RASPIBOT_LOG_LEVEL', 'DEBUG')
        importlib.reload(importlib.import_module('raspibot.settings.config'))
        from raspibot.settings import settings
        assert settings.LOG_LEVEL == 'DEBUG'

    def test_log_to_file_default(self):
        """Test that LOG_TO_FILE defaults to True."""
        from raspibot.settings import settings
        assert settings.LOG_TO_FILE is True

    def test_log_to_file_from_env(self, monkeypatch):
        """Test that LOG_TO_FILE loads from RASPIBOT_LOG_TO_FILE environment variable."""
        monkeypatch.setenv('RASPIBOT_LOG_TO_FILE', 'false')
        importlib.reload(importlib.import_module('raspibot.settings.config'))
        from raspibot.settings import settings
        assert settings.LOG_TO_FILE is False

    def test_log_stacktrace_default(self):
        """Test that LOG_STACKTRACE defaults to False."""
        from raspibot.settings import settings
        assert settings.LOG_STACKTRACE is False

    def test_log_stacktrace_from_env(self, monkeypatch):
        """Test that LOG_STACKTRACE loads from RASPIBOT_LOG_STACKTRACE environment variable."""
        monkeypatch.setenv('RASPIBOT_LOG_STACKTRACE', 'true')
        importlib.reload(importlib.import_module('raspibot.settings.config'))
        from raspibot.settings import settings
        assert settings.LOG_STACKTRACE is True

    def test_boolean_conversion_case_insensitive(self, monkeypatch):
        """Test that boolean conversion is case insensitive."""
        monkeypatch.setenv('RASPIBOT_DEBUG', 'TRUE')
        importlib.reload(importlib.import_module('raspibot.settings.config'))
        from raspibot.settings import settings
        assert settings.DEBUG is True
        
        monkeypatch.setenv('RASPIBOT_DEBUG', 'False')
        importlib.reload(importlib.import_module('raspibot.settings.config'))
        from raspibot.settings import settings
        assert settings.DEBUG is False

    def test_missing_environment_variables_use_defaults(self):
        """Test that missing environment variables use sensible defaults."""
        with patch.dict(os.environ, {}, clear=True):
            importlib.reload(importlib.import_module('raspibot.settings.config'))
            from raspibot.settings import settings
            assert settings.DEBUG is False
            assert settings.LOG_LEVEL == 'INFO'
            assert settings.LOG_TO_FILE is True
            assert settings.LOG_STACKTRACE is False 