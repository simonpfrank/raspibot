#!/bin/bash

# Script to run tests with proper environment setup for Raspberry Pi Connect

# Set display for WayVNC/XWayland
export DISPLAY=:0

# Activate virtual environment
source .venv/bin/activate

# Run the specified test or all tests
if [ $# -eq 0 ]; then
    echo "Running all tests..."
    python -m pytest tests/ -v
else
    echo "Running specific test: $1"
    python -m pytest "$1" -v
fi 