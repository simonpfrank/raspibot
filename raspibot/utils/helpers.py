"""Utility helper functions for the Raspibot project.

This module provides simple, useful utility functions used across the project.
"""

import os
import time
import uuid
import math
from contextlib import contextmanager
from typing import Union, Optional


def generate_correlation_id() -> str:
    """Generate a simple 8-character correlation ID.
    
    Returns:
        A unique 8-character hexadecimal string for correlation tracking.
    """
    return uuid.uuid4().hex[:8]


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory to ensure exists.
    """
    os.makedirs(directory_path, exist_ok=True)


def check_file_permissions(file_path: str, permission: str) -> bool:
    """Check if a file has the specified permission.
    
    Args:
        file_path: Path to the file to check.
        permission: Permission to check ('r' for read, 'w' for write, 'x' for execute).
    
    Returns:
        True if the file has the specified permission, False otherwise.
    """
    if permission == 'r':
        return os.access(file_path, os.R_OK)
    elif permission == 'w':
        return os.access(file_path, os.W_OK)
    elif permission == 'x':
        return os.access(file_path, os.X_OK)
    else:
        return False


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians.
    
    Args:
        degrees: Angle in degrees.
    
    Returns:
        Angle in radians.
    """
    return degrees * (math.pi / 180.0)


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees.
    
    Args:
        radians: Angle in radians.
    
    Returns:
        Angle in degrees.
    """
    return radians * (180.0 / math.pi)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between a minimum and maximum.
    
    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
    
    Returns:
        The clamped value.
    """
    return max(min_val, min(value, max_val))


class Timer:
    """Simple timer context manager for measuring elapsed time."""
    
    def __init__(self):
        self.start_time = None
        self.elapsed = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time


def timer(func):
    """Decorator to time function execution.
    
    Args:
        func: The function to time.
    
    Returns:
        Wrapped function that prints execution time.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"{func.__name__} took {elapsed:.4f} seconds")
        return result
    return wrapper 