#!/bin/bash
# Installation script for Raspibot servo controller dependencies

echo "=== Installing Raspibot Servo Controller Dependencies ==="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    echo "   Some dependencies may not work on other systems"
    echo
fi

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3-pip python3-venv i2c-tools

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Enable I2C (for PCA9685)
echo "🔌 Enabling I2C interface..."
if ! grep -q "i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    echo "✓ I2C enabled in config.txt"
else
    echo "✓ I2C already enabled"
fi

# Add user to i2c group
echo "👤 Adding user to i2c group..."
sudo usermod -a -G i2c $USER

# Test I2C
echo "🧪 Testing I2C bus..."
if i2cdetect -y 1 >/dev/null 2>&1; then
    echo "✓ I2C bus 1 is working"
    echo "  Available devices:"
    i2cdetect -y 1
else
    echo "⚠️  I2C bus 1 not detected"
fi

echo
echo "🎉 Installation completed!"
echo
echo "Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. Test GPIO servo controller: python3 scripts/simple_gpio_test.py"
echo "3. Test both controllers: python3 scripts/test_servo_controllers.py"
echo
echo "Note: After reboot, you may need to log out and back in for i2c group changes to take effect." 