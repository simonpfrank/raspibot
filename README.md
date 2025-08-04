# Raspibot

**Code is changing a lot so not worth downloading yet**

A hobby development of simple robotics on a Raspberry Pi 5.

## Project Aims

* Pan and Tilt camera driven by face detection
* Face recognition - initially using OpenCV
* Multi array microphone to detect direction of wake word and reduction of extraneous noises
* Voice to LLM and voice response
* Movement - adding a wheeled base

## Future Goals

* Experiment with models on the Raspberry Pi AI camera
* Some level of autonomous movement, using ultrasound and possibly LIDAR

## Quick Start

### Prerequisites
- Raspberry Pi 5 8GB
- Adafruit 16-Channel 12-Bit PWM/Servo Driver - I2C interface (PCA9685)
- Adafruit mini Pan and Tilt kit with micro servos assembled

### Installation
```bash
# Install dependencies
./scripts/setup/install_dependencies.sh

# Run a basic example
python examples/cameras/picamera2_basic.py.py
```

### Learning Path
1. Start with basic examples in `/examples/basic/`
2. Explore hardware examples in `/examples/hardware/`
3. Try advanced features in `/examples/advanced/`

## Project Structure

```
raspibot/
├── raspibot/                    # Main package
│   ├── hardware/                # Hardware abstraction layer
│   ├── vision/                  # Computer vision modules
│   ├── core/                    # Core application logic
│   └── utils/                   # Utility functions
├── examples/                    # Educational examples
│   ├── camera/                   # Simple, single-concept examples
├── scripts/                     # Production utilities
│   └── utilities/               # Operational tools
└── tests/                       # Test suite **Out of date**
```

## Hardware Requirements

### Phase 1 (Current)
* Raspberry Pi 5 8GB
* Adafruit 16-Channel 12-Bit PWM/Servo Driver - I2C interface (PCA9685)
* Adafruit mini Pan and Tilt kit with micro servos assembled

### Phase 2
* Raspberry Pi AI Camera

### Phase 3
* Multi mic array (to be chosen)
* WaveShare Robot-Chassis-MP
* Adafruit DC & Stepper Motor Bonnet for Raspberry Pi

## Documentation

- [Examples Guide](examples/README.md) - Learn how to use the project
- [Scripts Guide](scripts/README.md) - System management utilities
- [Hardware Setup](docs/how_to/) - Hardware configuration guides
- [Development Guide](docs/) - Technical specifications and development docs


