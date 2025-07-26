# Environment Setup Guide

## 🚨 Critical Environment Learnings

### Pi AI Camera & OpenCV Issues

#### 1. Headless Pi OpenCV Installation
**Problem**: OpenCV with GUI dependencies fails on headless Raspberry Pi
**Solution**: Install opencv-headless instead
```bash
# For headless Pi (no display)
pip install opencv-python-headless

# For Pi with display
pip install opencv-python
```

#### 2. PiCamera2 + NumPy Version Conflict
**Problem**: `simplejpeg` module fails with numpy dimension errors
**Root Cause**: PiCamera2 package requires numpy 1.x, newer versions cause conflicts
**Solution**: 
```bash
# Pin numpy to compatible version
pip install "numpy<2.0"
# or
pip install "numpy>=1.21,<2.0"
```

#### 3. Virtual Environment with System Packages
**Problem**: PiCamera2 and related packages not found in virtual environment
**Root Cause**: Some packages installed via apt-get aren't accessible in isolated venv
**Solution**: Create virtual environment with system site packages
```bash
# Install system packages first
sudo apt-get install python3-picamera2 python3-opencv

# Create venv with system packages
python3 -m venv .venv --system-site-packages

# Activate and install additional packages
source .venv/bin/activate
pip install -r requirements.txt
```

### Vision Module Specific Issues

#### 4. Pi AI Camera Resource Conflicts
**Problem**: "Device or resource busy" when creating multiple camera instances
**Root Cause**: Pi AI camera can only have one active instance at a time
**Solutions**:
- Run integration tests individually, not in batch
- Implement proper camera cleanup between tests
- Use camera pooling or singleton pattern for multiple scenarios

#### 5. RGBA vs BGR Format Handling
**Problem**: Pi AI camera returns RGBA (4 channels), face detector expects BGR (3 channels)
**Solution**: Added automatic format conversion in `FaceDetector.detect_faces()`
```python
# Automatic conversion in face detector
if frame.shape[2] == 4:
    frame_bgr = frame[:, :, :3]  # Remove alpha channel
else:
    frame_bgr = frame
```

#### 6. Camera Initialization Timeouts
**Problem**: Pi AI camera takes 4-5 seconds to initialize (firmware upload)
**Solution**: Add proper timeout handling and user feedback
```python
# In camera selector
logger.info("Loading network firmware onto the IMX500 can take several minutes...")
```

### Servo Control Issues

#### 7. I2C Permission Issues
**Problem**: Permission denied when accessing I2C bus for PCA9685
**Root Cause**: User not in i2c group or device not enabled
**Solution**:
```bash
# Add user to i2c group
sudo usermod -a -G i2c $USER

# Enable I2C in raspi-config
sudo raspi-config
# Interface Options → I2C → Enable

# Check I2C devices
sudo i2cdetect -y 1
```

#### 8. GPIO Permission Issues
**Problem**: Permission denied when accessing GPIO pins
**Root Cause**: User not in gpio group
**Solution**:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Or run with sudo (not recommended for production)
sudo python3 your_script.py
```

#### 9. PCA9685 Address Conflicts
**Problem**: Multiple I2C devices with same address
**Root Cause**: Hardware address conflicts or wiring issues
**Solution**:
```bash
# Check I2C bus for devices
sudo i2cdetect -y 1

# Verify PCA9685 is at expected address (usually 0x40)
# If not found, check wiring and power
```

### General Raspberry Pi Environment Issues

#### 10. Python Version Compatibility
**Problem**: Some packages require specific Python versions
**Solution**: Use Python 3.11+ for best compatibility
```bash
# Check Python version
python3 --version

# Update if needed
sudo apt update
sudo apt install python3.11 python3.11-venv
```

#### 11. Memory and Performance Issues
**Problem**: Out of memory errors with vision processing
**Root Cause**: Limited RAM on Raspberry Pi
**Solutions**:
- Increase swap space
- Use lower resolution camera settings
- Optimize image processing algorithms
- Close unnecessary applications

#### 12. Temperature Management
**Problem**: Pi AI camera and intensive processing can cause thermal throttling
**Solution**:
```bash
# Monitor temperature
vcgencmd measure_temp

# Check for throttling
vcgencmd get_throttled

# Consider active cooling for intensive workloads
```

#### 13. Virtual Environment Activation Issues
**Problem**: Forgetting to activate virtual environment causes import errors
**Root Cause**: Common mistake during development
**Solution**: Always activate before running tests or scripts
```bash
# Always activate first
source .venv/bin/activate

# Check if activated
which python  # Should show .venv/bin/python
```

#### 14. Face Detection Model Path Issues
**Problem**: YuNet face detection model not found
**Root Cause**: Model file not downloaded or wrong path
**Solution**: Ensure model exists in expected location
```bash
# Check if model exists
ls -la data/models/face_detection_yunet_2023mar.onnx

# Download if missing (should be done during setup)
# Model is ~1.5MB and required for face detection
```

#### 15. Logging Configuration Issues
**Problem**: Logs not appearing or wrong format
**Root Cause**: Logging not properly configured for development
**Solution**: Use our logging setup
```python
from raspibot.utils.logging_config import setup_logging
logger = setup_logging(__name__)
```

#### 16. Servo Calibration Issues
**Problem**: Servos not moving to expected positions
**Root Cause**: Different servo models have different pulse ranges
**Solution**: Calibrate each servo individually
```python
# Test servo range
for angle in range(0, 180, 10):
    servo.set_angle(angle)
    time.sleep(0.5)

# Find min/max pulse widths for your specific servos
# Standard servos: 500-2500 microseconds
# Some servos: 600-2400 microseconds
```

#### 17. Power Supply Issues for Servos
**Problem**: Servos jitter or don't move when multiple servos active
**Root Cause**: Insufficient power supply for servo load
**Solution**: Use adequate power supply
```bash
# Calculate power requirements
# Typical servo: 500mA-1A at 5V under load
# Multiple servos: Use 5V/3A+ power supply
# Separate power for servos vs Pi logic
```

#### 18. I2C Bus Speed Issues
**Problem**: Servo movements are slow or unreliable
**Root Cause**: I2C bus speed too high for reliable communication
**Solution**: Lower I2C bus speed
```bash
# Check current I2C speed
sudo cat /sys/class/i2c-adapter/i2c-1/of_node/clock-frequency

# Set lower speed in /boot/config.txt
# dtparam=i2c_arm=on,i2c_arm_baudrate=100000
```

## 📋 Complete Setup Checklist

### 1. System Preparation
- [ ] Update Raspberry Pi OS
- [ ] Enable I2C interface
- [ ] Enable SPI interface (if needed)
- [ ] Add user to i2c and gpio groups
- [ ] Install system packages

### 2. Python Environment
- [ ] Install Python 3.11+
- [ ] Create virtual environment with --system-site-packages
- [ ] Install opencv-headless (for headless Pi)
- [ ] Pin numpy to compatible version
- [ ] Install other requirements

### 3. Hardware Verification
- [ ] Test I2C bus with i2cdetect
- [ ] Verify PCA9685 servo controller
- [ ] Test Pi AI camera initialization
- [ ] Check GPIO pin access

### 4. Software Testing
- [ ] Run unit tests
- [ ] Test camera functionality
- [ ] Test servo control
- [ ] Run integration tests individually

## 🔧 Troubleshooting Commands

### Check System Status
```bash
# Check Python version
python3 --version

# Check installed packages
pip list

# Check I2C devices
sudo i2cdetect -y 1

# Check GPIO permissions
ls -la /dev/gpiomem

# Check temperature
vcgencmd measure_temp

# Check memory usage
free -h
```

### Debug Camera Issues
```bash
# Check camera modules
lsmod | grep camera

# Check camera devices
ls -la /dev/video*

# Test Pi AI camera
python3 -c "from picamera2 import Picamera2; print('PiCamera2 available')"
```

### Debug Servo Issues
```bash
# Check I2C bus
sudo i2cdetect -y 1

# Test PCA9685 communication
python3 -c "import smbus2; bus = smbus2.SMBus(1); print('I2C bus accessible')"

# Check servo power
# Use multimeter to verify 5V supply
```

## 📚 Additional Resources

### Documentation
- [PiCamera2 Documentation](https://picamera2.readthedocs.io/)
- [OpenCV Python Documentation](https://docs.opencv.org/)
- [PCA9685 Datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf)

### Community Resources
- [Raspberry Pi Forums](https://forums.raspberrypi.com/)
- [PiCamera2 GitHub](https://github.com/raspberrypi/picamera2)
- [OpenCV Python Examples](https://github.com/opencv/opencv-python)

## 🚀 Performance Tips

### For Vision Processing
- Use lower resolution for faster processing
- Implement frame skipping for real-time applications
- Use hardware acceleration when available
- Optimize face detection parameters

### For Servo Control
- Use appropriate PWM frequency (50Hz for servos)
- Implement smooth movement algorithms
- Add position limits to prevent damage
- Use proper power supply for multiple servos

### General Optimization
- Monitor system resources during development
- Use profiling tools to identify bottlenecks
- Consider using Cython for performance-critical code
- Implement proper error handling and recovery

This guide should help avoid the common pitfalls we've encountered during development! 