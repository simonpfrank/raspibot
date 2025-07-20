"""Hardware interface classes for the Raspibot project.

This module defines simple hardware interface classes that use
NotImplementedError for interface enforcement. This approach is
educational and easy to understand without complex abstractions.
"""


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


class Camera:
    """Hardware interface for camera control.
    
    This will be implemented with real camera hardware later, but for now
    we'll create a mock version for testing. Shows how to design
    for dependency injection and testing.
    """
    
    def capture_frame(self):
        """Capture a single frame from the camera."""
        raise NotImplementedError("Implement in subclass")
    
    def start_stream(self) -> None:
        """Start the camera stream."""
        raise NotImplementedError("Implement in subclass")
    
    def stop_stream(self) -> None:
        """Stop the camera stream."""
        raise NotImplementedError("Implement in subclass")
    
    def set_resolution(self, width: int, height: int) -> None:
        """Set the camera resolution."""
        raise NotImplementedError("Implement in subclass") 