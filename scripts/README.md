# Scripts Directory

This directory contains production utility scripts for system management, setup, and maintenance of the Raspibot project.

## Directory Structure

### `/setup/` - Installation and Setup
Scripts for initial system setup and configuration.

- **install_dependencies.sh** - Install all required system dependencies
- **calibrate_servos.py** - Servo calibration tool (to be created)

### `/maintenance/` - System Maintenance
Scripts for ongoing system maintenance and emergency operations.

- **return_servos_safe.py** - Emergency servo reset to safe positions
- **system_check.py** - System health check (to be created)

### `/utilities/` - Operational Tools
Utility scripts for testing and operational tasks.

- **servo_range_test.py** - Test servo movement ranges and limits

## Usage

### Setup Scripts
```bash
# Install dependencies
./scripts/setup/install_dependencies.sh

# Calibrate servos (when implemented)
python scripts/setup/calibrate_servos.py
```

### Maintenance Scripts
```bash
# Emergency servo reset
python scripts/maintenance/return_servos_safe.py

# System health check (when implemented)
python scripts/maintenance/system_check.py
```

### Utility Scripts
```bash
# Test servo ranges
python scripts/utilities/servo_range_test.py
```

## Script Requirements

- **Permissions**: Some scripts may require sudo access for hardware operations
- **Hardware**: Most scripts require specific hardware to be connected
- **Environment**: Run from project root directory for proper imports

## Safety Notes

- **return_servos_safe.py**: Use this script if servos are in unexpected positions
- **Hardware testing**: Always ensure hardware is properly connected before running
- **Emergency stop**: Use Ctrl+C to stop any running script immediately

## Contributing

When adding new scripts:
- Place in appropriate directory based on purpose
- Include proper error handling and safety checks
- Add help text and usage examples
- Ensure scripts are idempotent where possible
- Test thoroughly before committing 