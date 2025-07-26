"""Simple servo controller interface.

This module defines the servo controller interface that all implementations
must follow, using NotImplementedError for simplicity and educational value.
"""

from typing import Dict, Optional


class ServoInterface:
    """Simple interface for servo controllers.
    
    All servo controller implementations should inherit from this class
    and implement all methods. This approach is educational and easy to
    understand without complex abstractions.
    """
    
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle on specified channel.
        
        Args:
            channel: Servo channel number
            angle: Target angle in degrees
        """
        raise NotImplementedError("Subclass must implement set_servo_angle()")
    
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle on specified channel.
        
        Args:
            channel: Servo channel number
            
        Returns:
            Current angle in degrees
        """
        raise NotImplementedError("Subclass must implement get_servo_angle()")
    
    def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Move servo smoothly to target angle.
        
        Args:
            channel: Servo channel number
            target_angle: Target angle in degrees
            speed: Movement speed (0.1 to 1.0)
        """
        raise NotImplementedError("Subclass must implement smooth_move_to_angle()")
    
    def emergency_stop(self) -> None:
        """Emergency stop all servos."""
        raise NotImplementedError("Subclass must implement emergency_stop()")
    
    def set_calibration_offset(self, channel: int, offset: float) -> None:
        """Set calibration offset for a servo channel.
        
        Args:
            channel: Servo channel number
            offset: Calibration offset in degrees
        """
        raise NotImplementedError("Subclass must implement set_calibration_offset()")
    
    def get_calibration_offset(self, channel: int) -> float:
        """Get calibration offset for a servo channel.
        
        Args:
            channel: Servo channel number
            
        Returns:
            Calibration offset in degrees
        """
        raise NotImplementedError("Subclass must implement get_calibration_offset()")
    
    def shutdown(self) -> None:
        """Safely shutdown the servo controller."""
        raise NotImplementedError("Subclass must implement shutdown()")
    
    def get_controller_type(self) -> str:
        """Get the type of controller.
        
        Returns:
            Controller type string (e.g., "PCA9685", "GPIO")
        """
        raise NotImplementedError("Subclass must implement get_controller_type()")
    
    def get_available_channels(self) -> list[int]:
        """Get list of available servo channels.
        
        Returns:
            List of available channel numbers
        """
        raise NotImplementedError("Subclass must implement get_available_channels()") 