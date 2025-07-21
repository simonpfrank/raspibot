"""Application settings loaded from environment variables.

This module provides simple, module-level configuration constants
that are loaded from environment variables with sensible defaults.
"""

import os
from typing import Final

# Application settings loaded from environment
DEBUG: Final[bool] = os.getenv('RASPIBOT_DEBUG', 'false').lower() == 'true'
LOG_LEVEL: Final[str] = os.getenv('RASPIBOT_LOG_LEVEL', 'INFO')
LOG_TO_FILE: Final[bool] = os.getenv('RASPIBOT_LOG_TO_FILE', 'true').lower() == 'true'
LOG_STACKTRACE: Final[bool] = os.getenv('RASPIBOT_LOG_STACKTRACE', 'false').lower() == 'true'
LOG_FILE_PATH: Final[str] = os.getenv('RASPIBOT_LOG_FILE_PATH', 'data/logs/raspibot.log') 