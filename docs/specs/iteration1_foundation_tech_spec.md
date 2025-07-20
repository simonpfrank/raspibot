# Iteration 1: Project Foundation & Configuration Infrastructure

## Overview

**Iteration:** 1 (Foundation)  
**Status:** Planning  
**Priority:** Critical Foundation  
**Estimated Effort:** 2-3 days

This iteration establishes the foundational infrastructure for the Raspibot project, including project structure, configuration management, logging, hardware abstraction interfaces, and testing framework. All components in this iteration are designed to be fully unit testable without hardware dependencies and will support all PRD phases (1-5).

## Objectives

1. **Establish Project Structure**: Create the complete directory structure as defined in the cursor rules
2. **Configuration Management**: Implement robust settings and hardware configuration systems
3. **Logging Infrastructure**: Set up comprehensive logging with proper formatting and levels
4. **Hardware Abstraction**: Create interfaces that can be mocked for testing and implemented with real hardware later
5. **Testing Framework**: Establish pytest-based testing with high coverage standards
6. **Dependency Management**: Set up proper Python package management and environment handling

## Technical Requirements

### 1. Project Structure Setup

**Files to Create:**
```
raspibot/
├── raspibot/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── hardware_config.py
│   ├── hardware/
│   │   ├── __init__.py
│   │   └── interfaces.py       # Hardware abstraction interfaces
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_config.py
│   │   └── helpers.py
│   └── exceptions.py           # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest configuration and fixtures
│   ├── unit/                  # Unit tests (no external dependencies)
│   │   ├── __init__.py
│   │   ├── test_config/
│   │   │   ├── __init__.py
│   │   │   ├── test_settings.py
│   │   │   └── test_hardware_config.py
│   │   └── test_utils/
│   │       ├── __init__.py
│   │       ├── test_logging_config.py
│   │       └── test_helpers.py
│   └── integration/           # Integration tests (hardware dependencies)
│       ├── __init__.py
│       └── test_hardware/
│           ├── __init__.py
│           └── test_servo_integration.py  # Future integration tests
├── requirements.txt
├── setup.py
└── .env.example
```

### 2. Configuration Management (`raspibot/config/`)

#### 2.1 Settings Module (`settings.py`)
**Purpose**: Simple, clear configuration management using dataclasses and environment variables

**Key Features:**
- Simple dataclasses with type hints (educational and clear)
- Environment variable loading with sensible defaults
- Manual validation (shows how validation works, no magic)
- Easy to understand and extend
- Clear separation of concerns

**Implementation Approach (Module-Level - Simplest):**
```python
# settings.py
import os
from typing import Final

# Application settings loaded from environment
DEBUG: Final[bool] = os.getenv('RASPIBOT_DEBUG', 'false').lower() == 'true'
LOG_LEVEL: Final[str] = os.getenv('RASPIBOT_LOG_LEVEL', 'INFO')
LOG_TO_FILE: Final[bool] = os.getenv('RASPIBOT_LOG_TO_FILE', 'true').lower() == 'true'
LOG_STACKTRACE: Final[bool] = os.getenv('RASPIBOT_LOG_STACKTRACE', 'false').lower() == 'true'

# Usage: from raspibot.config.settings import DEBUG, LOG_LEVEL
```

**Educational Value**: Shows environment variable parsing, type hints with `Final`, string-to-boolean conversion, and module organization - all clear, standard Python patterns with no decorators or magic.

#### 2.2 Hardware Configuration (`hardware_config.py`)
**Purpose**: Hardware-specific mappings and constants

**Key Features:**
- Pin mapping constants for GPIO, I2C, SPI
- Hardware device addresses (PCA9685, sensors)
- Servo angle limits and calibration defaults
- Camera resolution and frame rate settings
- Microphone array configuration

### 3. Logging Infrastructure (`raspibot/utils/logging_config.py`)

**Purpose**: Comprehensive logging setup following Python best practices

**Key Features:**
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured logging with consistent formatting
- File rotation and size management
- Console and file output options
- Module-specific loggers with class.function:line_number precision
- Performance logging capabilities
- Async operation tracking with correlation IDs
- Configurable error handling (stack traces on demand)

**Log Format:**
```
2024-01-15 10:30:45.123 INFO ServoController.initialize:42 Servo initialized on channel 0
2024-01-15 10:30:45.456 ERROR FaceDetector.detect_faces:87 [abc123:face_tracking] CameraException: Camera not initialized (camera.py:156)
2024-01-15 10:30:45.789 DEBUG ConfigLoader.load_settings:23 [:] Loading configuration from environment
```

**Error Handling Strategy:**
- Log error type and actual source line number (where error originated)
- No stack traces by default (configurable via RASPIBOT_LOG_STACKTRACE=true)
- Simple error context using standard logging
- Clean, readable error information

**Async Context Features:**
- Simple correlation ID tracking using built-in `contextvars`
- Format: `[correlation_id:task_name]` or `[:]` if no async context
- Automatic context preservation across await boundaries
- Minimal overhead, maximum clarity

### 4. Hardware Abstraction (`raspibot/hardware/interfaces.py`)

**Purpose**: Simple, clear interface definitions for hardware components (educational focus)

**Simple Approach - Just Classes with Documentation:**
```python
class ServoController:
    """Hardware interface for servo control.
    
    This will be implemented with real hardware later, but for now
    we'll create a mock version for testing. Shows how to design
    for dependency injection and testing.
    """
    
    def set_angle(self, channel: int, angle: float) -> None:
        """Set servo angle on specified channel."""
        raise NotImplementedError("Implement in subclass")
    
    def get_angle(self, channel: int) -> float:
        """Get current servo angle on specified channel."""
        raise NotImplementedError("Implement in subclass")
    
    def initialize(self) -> None:
        """Initialize the servo controller."""
        raise NotImplementedError("Implement in subclass")
    
    def shutdown(self) -> None:
        """Shutdown the servo controller safely."""
        raise NotImplementedError("Implement in subclass")
```

**Educational Value**: Shows interface design, documentation, dependency injection concepts, and how to design for testing without complex abstractions. Uses standard Python patterns that are easy to understand and extend.

**Alternative with typing.Protocol**: If desired for teaching modern Python typing, we can show Protocol usage later, but starting simple makes the concepts clearer.

### 5. Utility Functions (`raspibot/utils/helpers.py`)

**Purpose**: Common utility functions used across the project

**Functions to Include:**
- Configuration validation helpers
- File system utilities (create directories, check permissions)
- Hardware detection utilities (mock implementations for now)
- Math utilities (angle conversions, coordinate transformations)
- Timing and performance utilities
- Simple correlation ID generation (using `uuid.uuid4().hex[:8]`)

**Keep It Simple**: All logging utilities consolidated in `logging_config.py` to avoid over-modularization. Focus on readable, educational code patterns.

### 6. Exception Handling (`raspibot/exceptions.py`)

**Purpose**: Simple, clear custom exception classes for domain-specific error handling

**Exception Classes:**
```python
class RaspibotException(Exception):
    """Base exception for all raspibot errors"""
    pass

class HardwareException(RaspibotException):
    """Hardware-related errors (servo, camera, sensors)"""
    pass

class ConfigurationException(RaspibotException):
    """Configuration and settings errors"""
    pass

class CalibrationException(RaspibotException):
    """Servo/camera calibration errors"""
    pass

class CameraException(HardwareException):
    """Camera-specific hardware errors"""
    pass

class ServoException(HardwareException):
    """Servo-specific hardware errors"""
    pass
```

**Simple Error Handling Pattern:**
- Clean exception hierarchy for easy understanding
- Use standard Python patterns (no magic)
- Error details captured in logging, not exception classes
- Easy to extend and understand for Python learners

### 7. Testing Framework Setup

#### 7.1 Testing Configuration (`tests/conftest.py`)
**Purpose**: Pytest configuration, fixtures, and test utilities

**Key Features:**
- Mock hardware fixtures
- Temporary configuration fixtures
- Log capture fixtures
- Test data generators

#### 7.2 Test Coverage Requirements
- **Minimum Coverage**: 90%
- **Test Types**: Unit tests only (no integration tests in this phase)
- **Mock Strategy**: All hardware interfaces must be mocked
- **Test Data**: Use parameterized tests for configuration validation

### 8. Dependency Management

#### 8.1 Requirements (`requirements.txt`)
**Development Dependencies:**
```
# Core dependencies (absolute minimum)
python-dotenv>=1.0.0  # Only for .env file loading convenience

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-asyncio>=0.21.0  # For async test support

# Code quality
black>=23.0.0
isort>=5.12.0
mypy>=1.0.0

# Future hardware dependencies (commented out for Iteration 1)
# adafruit-circuitpython-pca9685
# opencv-python
# numpy
```

**Simplicity Philosophy**: Using Python standard library wherever possible. Even `python-dotenv` is optional - we can load environment variables with `os.getenv()` if needed. Configuration validation done with simple type checking and manual validation for educational clarity.

#### 8.2 Package Setup (`setup.py`)
**Purpose**: Proper Python package configuration for development installation

## Implementation Strategy

### Iteration 1.1: Core Structure (Day 1)
1. Create directory structure
2. Implement configuration management
3. Set up logging infrastructure
4. Create hardware interfaces

### Iteration 1.2: Testing & Validation (Day 2)
1. Implement comprehensive unit tests
2. Set up pytest configuration
3. Achieve 90%+ test coverage
4. Validate all configurations

### Iteration 1.3: Documentation & Polish (Day 3)
1. Add comprehensive docstrings
2. Type annotation validation
3. Code formatting with black and isort
4. Final testing and validation

## Testing Strategy

### Unit Test Coverage
- **Configuration Loading**: Test environment variable handling, defaults, validation
- **Logging Setup**: Test log formatting, file creation, level filtering
- **Hardware Interfaces**: Test mock implementations and interface compliance
- **Utility Functions**: Test all helper functions with edge cases
- **Exception Handling**: Test custom exception hierarchy

### Test Data Strategy
- Use temporary directories for file-based tests
- Mock all external dependencies
- Parameterized tests for configuration variations
- Property-based testing for numeric ranges (angles, coordinates)

## Success Criteria

### Technical Criteria
- [ ] All modules have 100% type annotation coverage
- [ ] 90%+ unit test coverage achieved
- [ ] All tests pass in isolation and in suite
- [ ] Code passes black, isort, and mypy checks
- [ ] All modules have comprehensive Google-style docstrings

### Functional Criteria
- [ ] Configuration can be loaded from environment variables
- [ ] Logging works correctly with multiple output destinations
- [ ] Hardware interfaces can be mocked successfully
- [ ] Project can be installed in development mode
- [ ] All utility functions work as expected

### Quality Criteria
- [ ] No code duplication (DRY principle)
- [ ] Clear separation of concerns
- [ ] Follows established project patterns
- [ ] Comprehensive error handling
- [ ] Performance-conscious implementation

## Dependencies

### Internal Dependencies
- None (this is the foundation phase)

### External Dependencies
- Python 3.11.2 (system requirement)
- pip and venv for package management
- pytest for testing framework
- Type checking and formatting tools

### Hardware Dependencies
- None (all hardware is mocked in this phase)

## Risks and Mitigation

### Technical Risks
1. **Configuration Complexity**: Start simple, iterate based on needs
2. **Over-abstraction**: Focus on interfaces we know we'll need
3. **Testing Overhead**: Prioritize high-value test coverage

### Mitigation Strategies
- Start with minimal viable implementations
- Use TDD to drive interface design
- Regular code reviews for design decisions
- Keep hardware interfaces simple and focused

## Next Iteration Dependencies

This iteration provides the foundation for:
- **PRD Phase 1**: Servo control and pan/tilt movement (Iteration 2)
- **PRD Phase 2**: Camera integration and vision processing (Iteration 3) 
- **PRD Phases 3-5**: Audio, mobility, and emotion display features (Future iterations)
- **All future iterations**: Hardware integration and feature development

The interfaces and patterns established here will be extended but not fundamentally changed in future iterations or PRD phases.

## Validation Checklist

Before marking Iteration 1 complete:
- [ ] All code is properly formatted and type-checked
- [ ] Test coverage meets or exceeds 90%
- [ ] All docstrings are complete and accurate
- [ ] Configuration system handles all expected scenarios
- [ ] Logging produces readable, actionable output
- [ ] Hardware interfaces are properly abstracted
- [ ] Exception handling covers expected error cases
- [ ] Code follows all established patterns and guidelines 