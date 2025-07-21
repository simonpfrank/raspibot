# Iteration 2 Tech Spec: Hardware Implementation (PRD Phase 1)

## Overview

**Iteration**: 2  
**Focus**: Abstracted Servo Control System (PCA9685 + GPIO) (PRD Phase 1)  
**Duration**: 2-3 days  
**Approach**: Test Driven Development (TDD) with real hardware  
**PRD Support**: Implements PRD Phase 1 - Servo control and pan/tilt system  

## Objectives

1. **Abstracted Hardware Integration**: Implement servo control with support for PCA9685 and GPIO
2. **Servo Control System**: Create robust servo angle control with safety features
3. **Pan/Tilt System**: Build coordinate-based camera movement system
4. **Safety & Calibration**: Implement limits, emergency stop, and calibration tools
5. **Performance**: Achieve accurate and smooth servo movements
6. **Extensibility**: Design for easy addition of new hardware options

## Hardware Requirements

### Physical Components
- **Option 1**: PCA9685 Servo Controller (16-channel PWM controller)
- **Option 2**: Direct GPIO control (individual servo control)
- **Servos**: 2x standard servos (pan and tilt)
- **Connections**: I2C (SDA/SCL) for PCA9685 or GPIO pins for direct control
- **Power Supply**: 5V for servos, 3.3V for logic

### Software Dependencies
```python
# Core dependencies
RPi.GPIO>=0.7.0  # For GPIO servo control
smbus2>=0.4.0    # For I2C communication (fallback)

# Optional dependencies (for PCA9685)
adafruit-circuitpython-pca9685>=3.4.0
adafruit-circuitpython-busdevice>=5.2.0
```

## Architecture

### Core Components

#### 1. Abstract Servo Interface (`raspibot/hardware/servo_interface.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Optional

class ServoInterface(ABC):
    """Abstract interface for servo controllers."""
    
    @abstractmethod
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle with validation."""
        
    @abstractmethod
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle."""
        
    @abstractmethod
    def set_pwm_frequency(self, frequency: int) -> None:
        """Set PWM frequency (50Hz for servos)."""
        
    @abstractmethod
    def emergency_stop(self) -> None:
        """Emergency stop all servos."""
        
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the servo controller safely."""
```

#### 2. PCA9685 Implementation (`raspibot/hardware/pca9685_servo.py`)
```python
class PCA9685ServoController(ServoInterface):
    """PCA9685 servo controller implementation."""
    
    def __init__(self, i2c_bus: int = 1, address: int = 0x40):
        """Initialize PCA9685 controller."""
        
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle with validation."""
        
    # ... other abstract method implementations
```

#### 3. GPIO Implementation (`raspibot/hardware/gpio_servo.py`)
```python
class GPIOServoController(ServoInterface):
    """GPIO-based servo controller implementation."""
    
    def __init__(self, servo_pins: Dict[int, int]):
        """Initialize GPIO servo controller.
        
        Args:
            servo_pins: Dictionary mapping servo channels to GPIO pins
                       e.g., {0: 17, 1: 18} for servos on GPIO 17 and 18
        """
        
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle with validation."""
        
    # ... other abstract method implementations
```

#### 4. Servo Factory (`raspibot/hardware/servo_factory.py`)
```python
from enum import Enum
from typing import Dict, Optional

class ServoControllerType(Enum):
    """Available servo controller types."""
    PCA9685 = "pca9685"
    GPIO = "gpio"

class ServoControllerFactory:
    """Factory for creating servo controllers."""
    
    @staticmethod
    def create_controller(
        controller_type: ServoControllerType,
        **kwargs
    ) -> ServoInterface:
        """Create a servo controller instance.
        
        Args:
            controller_type: Type of controller to create
            **kwargs: Additional arguments for specific controller types
            
        Returns:
            Servo controller instance
        """
```

#### 5. Pan/Tilt System (`raspibot/movement/pan_tilt.py`)
```python
class PanTiltSystem:
    """Pan/tilt camera control system."""
    
    def __init__(self, servo_controller: ServoInterface):
        """Initialize pan/tilt system with any servo controller."""
        
    def move_to_coordinates(self, x: float, y: float) -> None:
        """Move to x,y coordinates."""
        
    def move_to_angles(self, pan_angle: float, tilt_angle: float) -> None:
        """Move to specific pan/tilt angles."""
        
    def smooth_track(self, target_x: float, target_y: float, speed: float = 1.0) -> None:
        """Smooth tracking movement."""
        
    def go_home(self) -> None:
        """Return to home position."""
```

#### 6. Calibration Tools (`raspibot/utils/calibration.py`)
```python
class ServoCalibrator:
    """Servo calibration and offset management."""
    
    def __init__(self, servo_controller: ServoInterface):
        """Initialize calibrator with servo controller."""
        
    def calibrate_servo(self, channel: int) -> dict:
        """Calibrate servo and return offset data."""
        
    def save_calibration(self, channel: int, data: dict) -> None:
        """Save calibration data to file."""
        
    def load_calibration(self, channel: int) -> dict:
        """Load calibration data from file."""
```

## Implementation Plan

### Phase 1: Abstract Interface & Basic Implementations
1. **Create Abstract Interface**
   - Define `ServoInterface` abstract base class
   - Define common servo control methods
   - Create comprehensive interface tests

2. **Implement GPIO Controller**
   - Create `GPIOServoController` class
   - Implement PWM using RPi.GPIO
   - Add channel management and validation
   - Create GPIO-specific tests

3. **Refactor PCA9685 Controller**
   - Update existing PCA9685 implementation to use interface
   - Ensure compatibility with abstract interface
   - Update PCA9685-specific tests

### Phase 2: Factory Pattern & Configuration
1. **Create Servo Factory**
   - Implement `ServoControllerFactory`
   - Add configuration-based controller selection
   - Create factory tests

2. **Configuration Management**
   - Update hardware configuration for multiple controller types
   - Add environment variable support for controller selection
   - Create configuration validation

### Phase 3: Pan/Tilt System & Advanced Features
1. **Update Pan/Tilt System**
   - Modify to use abstract `ServoInterface`
   - Test with both controller types
   - Add coordinate-based movement

2. **Calibration System**
   - Update calibration tools for abstract interface
   - Create calibration tests for both controller types
   - Add calibration data management

### Phase 4: Integration & Testing
1. **Integration Testing**
   - Test both controller types with real hardware
   - Performance comparison between controllers
   - Safety and reliability testing

2. **Documentation & Examples**
   - Create usage examples for both controllers
   - Update hardware setup guides
   - Create troubleshooting documentation

## Technical Specifications

### Servo Control Parameters
- **PWM Frequency**: 50Hz (standard for servos)
- **Pulse Width Range**: 1ms (0°) to 2ms (180°)
- **Angle Range**: 0° to 180° (configurable per servo)
- **Accuracy**: ±1° target
- **Response Time**: < 100ms

### GPIO Configuration
- **PWM Method**: Software PWM using RPi.GPIO
- **Pin Assignment**: Configurable per servo channel
- **Frequency**: 50Hz (hardware limitation)
- **Resolution**: 12-bit (4096 steps)

### I2C Configuration (PCA9685)
- **Bus**: I2C1 (pins 3, 5)
- **Address**: 0x40 (default PCA9685 address)
- **Speed**: 100kHz (standard mode)
- **Timeout**: 1 second

### Safety Limits
- **Maximum Angle Change**: 45°/second (prevent damage)
- **Emergency Stop**: Immediate PWM disable
- **Temperature Monitoring**: Shutdown if overheating
- **Voltage Monitoring**: Shutdown if voltage drops

## Testing Strategy

### Unit Tests (Mocked Hardware)
```python
def test_servo_interface_contract():
    """Test that all implementations follow the interface contract."""
    
def test_gpio_servo_angle_validation():
    """Test GPIO servo angle validation."""
    
def test_pca9685_servo_angle_validation():
    """Test PCA9685 servo angle validation."""
    
def test_servo_factory_creation():
    """Test servo controller factory."""
    
def test_pan_tilt_with_different_controllers():
    """Test pan/tilt system with different controllers."""
```

### Integration Tests (Real Hardware)
```python
def test_gpio_servo_movement():
    """Test actual GPIO servo movement."""
    
def test_pca9685_servo_movement():
    """Test actual PCA9685 servo movement."""
    
def test_controller_switching():
    """Test switching between controller types."""
    
def test_calibration_both_controllers():
    """Test calibration with both controller types."""
```

### Performance Tests
```python
def test_gpio_vs_pca9685_performance():
    """Compare performance between GPIO and PCA9685."""
    
def test_accuracy_comparison():
    """Compare accuracy between controller types."""
    
def test_load_handling():
    """Test performance under load."""
```

## Error Handling

### Hardware Errors
- **GPIO Errors**: Pin validation and error recovery
- **I2C Communication Failure**: Retry logic with exponential backoff
- **Servo Stalling**: Current monitoring and timeout
- **Power Issues**: Voltage monitoring and graceful shutdown

### Software Errors
- **Invalid Angles**: Validation and error messages
- **Channel Conflicts**: Channel management and validation
- **Controller Selection**: Fallback mechanisms and validation
- **Configuration Errors**: Default configuration loading

## Configuration

### Environment Variables
```bash
# Controller Selection
RASPIBOT_SERVO_CONTROLLER_TYPE=gpio  # or pca9685
RASPIBOT_SERVO_PINS=0:17,1:18       # GPIO pins for servos
RASPIBOT_I2C_BUS=1                  # I2C bus for PCA9685
RASPIBOT_PCA9685_ADDRESS=0x40       # PCA9685 address

# Servo Limits
RASPIBOT_SERVO_MIN_ANGLE=0
RASPIBOT_SERVO_MAX_ANGLE=180
RASPIBOT_SERVO_DEFAULT_ANGLE=90

# Safety Settings
RASPIBOT_MAX_SPEED=45.0  # degrees/second
RASPIBOT_EMERGENCY_STOP_ENABLED=true
```

### Hardware Configuration
```python
# GPIO Configuration
GPIO_SERVO_PINS = {
    0: 17,  # Pan servo on GPIO 17
    1: 18,  # Tilt servo on GPIO 18
}

# PCA9685 Configuration
PCA9685_CONFIG = {
    'i2c_bus': 1,
    'address': 0x40,
    'channels': [0, 1],  # Pan and tilt channels
}
```

## Success Criteria

### Technical Metrics
- [ ] 90%+ test coverage for new hardware code
- [ ] All servo movements within ±1° accuracy
- [ ] Pan/tilt response time < 100ms
- [ ] Zero hardware damage or safety incidents
- [ ] Both controller types fully functional

### Functional Metrics
- [ ] Servos respond correctly to angle commands (both controllers)
- [ ] Pan/tilt system follows coordinate inputs
- [ ] Calibration tools work with both controllers
- [ ] Safety limits prevent damage
- [ ] Emergency stop functions properly

### Performance Metrics
- [ ] Servo movement smoothness (no jerky motion)
- [ ] Coordinate conversion accuracy
- [ ] Memory usage < 50MB
- [ ] CPU usage < 10% during normal operation

## Risks and Mitigation

### Hardware Risks
1. **GPIO Limitations**: Software PWM may be less smooth than hardware
2. **Servo Damage**: Implement strict limits and emergency stop
3. **I2C Communication**: Robust error handling and retry logic
4. **Power Issues**: Voltage monitoring and graceful shutdown

### Software Risks
1. **Interface Complexity**: Keep interface simple and well-documented
2. **Controller Selection**: Provide clear configuration and fallback options
3. **Performance Differences**: Document performance characteristics
4. **Integration Issues**: Comprehensive testing and validation

## Deliverables

### Code Modules
- [ ] `raspibot/hardware/servo_interface.py`
- [ ] `raspibot/hardware/gpio_servo.py`
- [ ] `raspibot/hardware/pca9685_servo.py`
- [ ] `raspibot/hardware/servo_factory.py`
- [ ] `raspibot/movement/pan_tilt.py`
- [ ] `raspibot/utils/calibration.py`
- [ ] `scripts/test_servo_controllers.py`

### Tests
- [ ] Unit tests for all hardware modules
- [ ] Integration tests with real hardware
- [ ] Performance and safety tests
- [ ] Calibration test procedures

### Documentation
- [ ] Hardware setup guide (both controllers)
- [ ] Calibration procedures
- [ ] API documentation
- [ ] Troubleshooting guide

### Configuration
- [ ] Updated requirements.txt
- [ ] Environment variable templates
- [ ] Calibration file formats
- [ ] Safety configuration

## Next Steps

After Iteration 2 completion:
1. **Iteration 3**: Camera integration and vision processing
2. **Iteration 4**: Audio processing and voice recognition
3. **Future**: Mobility and emotion display features

The abstracted hardware foundation established in Iteration 2 will support all future iterations and PRD phases with flexibility for different hardware configurations. 