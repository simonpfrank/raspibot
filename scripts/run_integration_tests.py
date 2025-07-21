#!/usr/bin/env python3
"""
Integration Test Runner

This script runs integration tests for the servo control system
and provides a clear summary of results.

Usage:
    python run_integration_tests.py

Requirements:
    - pytest and pytest-cov installed
    - Hardware available for integration testing
"""

import sys
import os
import subprocess
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_integration_tests():
    """Run integration tests and display results."""
    print("=== Servo Control System Integration Tests ===")
    print("Testing real hardware integration and component interaction")
    print()
    
    # Run integration tests
    print("Running integration tests...")
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/integration/test_servo_integration.py",
            "-v",
            "--tb=short"
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..'))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=== Test Results ===")
        print(result.stdout)
        
        if result.stderr:
            print("=== Warnings/Errors ===")
            print(result.stderr)
        
        print(f"=== Summary ===")
        print(f"Duration: {duration:.2f} seconds")
        
        if result.returncode == 0:
            print("✅ All integration tests PASSED!")
            print("🎉 Servo control system integration verified!")
        else:
            print("❌ Some integration tests FAILED!")
            print("Check the output above for details.")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False


def run_coverage_tests():
    """Run tests with coverage analysis."""
    print("\n=== Running Coverage Analysis ===")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/integration/test_servo_integration.py",
            "tests/unit/test_hardware/",
            "-v",
            "--cov=raspibot.hardware",
            "--cov=raspibot.movement",
            "--cov-report=term-missing"
        ], capture_output=True, text=True, cwd=os.path.join(os.path.dirname(__file__), '..'))
        
        print(result.stdout)
        
        if result.stderr:
            print("=== Warnings ===")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running coverage tests: {e}")
        return False


def main():
    """Main function."""
    print("🚀 Starting Servo Control System Integration Testing")
    print("=" * 60)
    
    # Run integration tests
    integration_success = run_integration_tests()
    
    # Run coverage tests
    coverage_success = run_coverage_tests()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL SUMMARY")
    print("=" * 60)
    
    if integration_success and coverage_success:
        print("✅ INTEGRATION TESTING COMPLETE!")
        print("✅ All tests passed")
        print("✅ Coverage analysis complete")
        print("🎉 Servo control system is ready for production!")
        return 0
    else:
        print("❌ INTEGRATION TESTING FAILED!")
        if not integration_success:
            print("❌ Integration tests failed")
        if not coverage_success:
            print("❌ Coverage analysis failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 