"""Main face tracking robot class integrating all components."""

import time
from typing import Optional

from ..hardware.servo_factory import get_servo_controller, ServoControllerType
from ..movement.pan_tilt import PanTiltSystem
from ..vision.camera import Camera
from ..vision.face_tracker import FaceTracker
from ..vision.display import Display
from ..utils.logging_config import setup_logging
from ..exceptions import HardwareException


class FaceTrackingRobot:
    """Simple face tracking robot - brings it all together."""
    
    def __init__(self, servo_type: str = "pca9685", camera_device: int = 0):
        """
        Initialize the face tracking robot.
        
        Args:
            servo_type: Type of servo controller ("pca9685" or "gpio")
            camera_device: Camera device ID
        """
        self.logger = setup_logging(__name__)
        self.running = False
        
        # Initialize hardware
        try:
            controller_type = ServoControllerType.PCA9685 if servo_type == "pca9685" else ServoControllerType.GPIO
            self.servo_controller = get_servo_controller(controller_type)
            self.pan_tilt = PanTiltSystem(self.servo_controller)
            
            self.logger.info(f"Servo controller initialized: {servo_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize servo controller: {e}")
            raise HardwareException(f"Servo initialization failed: {e}")
        
        # Initialize vision components
        try:
            self.camera = Camera(device_id=camera_device)
            camera_width, camera_height = self.camera.get_resolution()
            
            self.face_tracker = FaceTracker(self.pan_tilt, camera_width, camera_height)
            self.display = Display()
            
            self.logger.info(f"Vision components initialized: camera {camera_width}x{camera_height}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vision components: {e}")
            if hasattr(self, 'servo_controller'):
                self.servo_controller.shutdown()
            raise RuntimeError(f"Vision initialization failed: {e}")
    
    def start(self) -> None:
        """Start the face tracking robot."""
        try:
            # Start camera
            if not self.camera.start():
                raise RuntimeError("Failed to start camera")
            
            self.logger.info("Camera started successfully")
            
            # Move to center position
            self.pan_tilt.move_to_coordinates(0, 0)
            self.logger.info("Pan/tilt system centered")
            
            self.running = True
            self.logger.info("Face tracking robot started! Press 'q' to quit.")
            
            # Main loop
            self._run_main_loop()
            
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Error during operation: {e}")
            self.display.show_error_message(f"Error: {e}")
        finally:
            self.stop()
    
    def _run_main_loop(self) -> None:
        """Main processing loop."""
        frame_count = 0
        start_time = time.time()
        
        while self.running:
            try:
                # Capture frame
                frame = self.camera.get_frame()
                if frame is None:
                    self.logger.warning("Failed to capture frame")
                    continue
                
                # Track faces
                stable_face, all_faces = self.face_tracker.track_face(frame)
                
                # Get stable faces for display
                stable_faces = [stable_face] if stable_face else []
                
                # Get current servo position
                servo_position = self.pan_tilt.get_current_coordinates()
                
                # Get search pattern status
                search_status = self.face_tracker.get_search_status()
                
                # Update display
                continue_running = self.display.show_frame(
                    frame=frame,
                    faces=all_faces,
                    stable_faces=stable_faces,
                    camera_fps=self.camera.get_fps(),
                    detection_fps=self.face_tracker.face_detector.get_detection_fps(),
                    servo_position=servo_position,
                    search_status=search_status
                )
                
                if not continue_running:
                    self.logger.info("User requested quit")
                    break
                
                # Performance monitoring
                frame_count += 1
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    avg_fps = frame_count / elapsed
                    self.logger.info(f"Performance: {avg_fps:.1f} avg FPS over {frame_count} frames")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.03)  # Target ~30 FPS
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(0.1)  # Brief pause before continuing
    
    def stop(self) -> None:
        """Stop the robot and cleanup resources."""
        self.logger.info("Stopping face tracking robot")
        self.running = False
        
        try:
            # Stop camera
            if hasattr(self, 'camera'):
                self.camera.stop()
                self.logger.info("Camera stopped")
            
            # Close display
            if hasattr(self, 'display'):
                self.display.close()
                self.logger.info("Display closed")
            
            # Shutdown servo controller
            if hasattr(self, 'servo_controller'):
                self.servo_controller.shutdown()
                self.logger.info("Servo controller shutdown")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    def is_running(self) -> bool:
        """
        Check if robot is currently running.
        
        Returns:
            True if running
        """
        return self.running
    
    def get_status(self) -> dict:
        """
        Get current robot status.
        
        Returns:
            Dictionary with status information
        """
        try:
            camera_status = "running" if self.camera.is_available() else "stopped"
            servo_position = self.pan_tilt.get_current_coordinates()
            sleep_status = self.face_tracker.get_sleep_status()
            time_until_sleep = self.face_tracker.get_time_until_sleep()
            
            return {
                "running": self.running,
                "camera_status": camera_status,
                "camera_fps": self.camera.get_fps(),
                "detection_fps": self.face_tracker.face_detector.get_detection_fps(),
                "servo_position": servo_position,
                "sleep_status": sleep_status,
                "time_until_sleep": time_until_sleep
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {"error": str(e)}
    
    def force_wake_up(self) -> None:
        """Force the robot to wake up from sleep mode."""
        try:
            self.face_tracker.force_wake_up()
            self.logger.info("Robot forced to wake up")
        except Exception as e:
            self.logger.error(f"Error forcing wake up: {e}")
    
    def force_sleep(self) -> None:
        """Force the robot to go to sleep mode."""
        try:
            self.face_tracker.force_sleep()
            self.logger.info("Robot forced to sleep")
        except Exception as e:
            self.logger.error(f"Error forcing sleep: {e}")
    
    def center_camera(self) -> None:
        """Center the camera."""
        self.pan_tilt.center_camera()
        self.logger.info("Camera centered")
    
    def force_search(self) -> bool:
        """
        Force start search pattern immediately.
        
        Returns:
            True if search started successfully
        """
        return self.face_tracker.force_start_search()
    
    def stop_search(self) -> None:
        """Stop current search pattern."""
        self.face_tracker.stop_search()
    
    def get_search_status(self) -> dict:
        """
        Get search pattern status.
        
        Returns:
            Dictionary with search status information
        """
        return self.face_tracker.get_search_status()
    
    def set_search_interval(self, interval: float) -> None:
        """
        Set search interval (how often to search when no faces detected).
        
        Args:
            interval: Search interval in seconds
        """
        self.face_tracker.set_search_interval(interval)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop() 