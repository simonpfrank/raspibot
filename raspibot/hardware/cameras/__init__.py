"""Unified camera package using Picamera2 for all camera types."""

from .unified_camera import create_camera, CameraType, get_available_cameras, list_cameras

# Backward compatibility aliases
get_camera = create_camera
get_best_available_camera = lambda: create_camera("auto")

__all__ = [
    'create_camera', 'get_camera', 'CameraType', 'get_available_cameras', 'list_cameras'
] 