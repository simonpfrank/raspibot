"""Abstract servo controller interface.

This module defines the abstract interface that all servo controller
implementations must follow, ensuring consistency and testability.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class ServoInterface(ABC):
    """Abstract interface for servo controllers.
    
    All servo controller implementations must inherit from this class
    and implement all abstract methods.
    """
    
    @abstractmethod
    def set_servo_angle(self, channel: int, angle: float) -> None:
        """Set servo angle on specified channel.
        
        Args:
            channel: Servo channel number
            angle: Target angle in degrees
        """
        pass
    
    @abstractmethod
    def get_servo_angle(self, channel: int) -> float:
        """Get current servo angle on specified channel.
        
        Args:
            channel: Servo channel number
            
        Returns:
            Current angle in degrees
        """
        pass
    
    @abstractmethod
    def smooth_move_to_angle(self, channel: int, target_angle: float, speed: float = 1.0) -> None:
        """Move servo smoothly to target angle.
        
        Args:
            channel: Servo channel number
            target_angle: Target angle in degrees
            speed: Movement speed (0.1 to 1.0)
        """
        pass
    
    @abstractmethod
    def emergency_stop(self) -> None:
        """Emergency stop all servos."""
        pass
    
    @abstractmethod
    def set_calibration_offset(self, channel: int, offset: float) -> None:
        """Set calibration offset for a servo channel.
        
        Args:
            channel: Servo channel number
            offset: Calibration offset in degrees
        """
        pass
    
    @abstractmethod
    def get_calibration_offset(self, channel: int) -> float:
        """Get calibration offset for a servo channel.
        
        Args:
            channel: Servo channel number
            
        Returns:
            Calibration offset in degrees
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Safely shutdown the servo controller."""
        pass
    
    @abstractmethod
    def get_controller_type(self) -> str:
        """Get the type of controller.
        
        Returns:
            Controller type string (e.g., "PCA9685", "GPIO")
        """
        pass
    
    @abstractmethod
    def get_available_channels(self) -> list[int]:
        """Get list of available servo channels.
        
        Returns:
            List of available channel numbers
        """
        pass 