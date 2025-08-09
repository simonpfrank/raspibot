"""
Simplified USB Camera using Picamera2 instead of complex OpenCV detection.
"""

import time
from typing import Optional, Tuple
import numpy as np

try:
    from picamera2 import Picamera2, Preview

    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

from raspibot.utils.logging_config import setup_logging
from raspibot.settings.config import *

display_modes = {
    "screen": Preview.QTGL,  # hardware accelerated
    "connect": Preview.QT,  # slow
    "ssh": Preview.DRM,  # no desktop running
    "none": Preview.NULL,
}


class USBCamera:
    """USB Camera implementation using Picamera2."""

    def __init__(
        self,
        camera_device_id: Optional[int] = None,
        camera_resolution: Optional[Tuple[int, int]] = None,
        display_resolution: Optional[Tuple[int, int]] = None,
        display_position: Optional[Tuple[int, int]] = None,
        display_mode: Optional[str] = None,
    ) -> None:
        """
        Initialize USB Camera.

        Args:
            camera_device_id: Camera device ID
            camera_resolution: Camera resolution
            display_resolution: Display resolution
            display_position: Display position
            display_mode: Display mode ("screen", "connect", "ssh", "none")
        """
        if not PICAMERA2_AVAILABLE:
            raise ImportError(
                "picamera2 not available. USB camera requires picamera2 library."
            )

        self.logger = setup_logging(__name__)

        # Use config defaults if not provided
        self.camera_resolution = camera_resolution or CAMERA_RESOLUTION
        self.display_resolution = display_resolution or CAMERA_DISPLAY_RESOLUTION
        self.display_position = display_position or CAMERA_DISPLAY_POSITION
        self.camera_device_id = camera_device_id or USB_CAMERA_DEVICE_ID
        self.display_mode = display_mode or PI_DISPLAY_MODE

        self.camera: Optional[Picamera2] = None
        self.is_running = False
        self.is_detecting = False
        if self.display_mode == "connect":
            # This may need adjusting for different displays other than direct
            os.environ["DISPLAY"] = ":0"  # for headles displays
            os.environ["QT_QPA_PLATFORM"] = "wayland"

        self.logger.info(f"Camera resolution: {self.camera_resolution}")
        self.logger.info(f"Display: {self.display_resolution}")
        self.current_fps = 0.0

        self.logger.info(f"Camera resolution: {self.camera_resolution}")
        self.logger.info(f"Display: {self.display_resolution}")

        self.logger.info("Initializing USB Camera with Picamera2")
        self._initialize_hardware()

    def _initialize_hardware(self) -> None:
        """Initialize USB camera hardware using Picamera2.global_camera_info()."""
        try:
            camera_info = Picamera2.global_camera_info()
            
            target_camera = None
            first_usb_camera = None
            
            # Single pass to find what we need
            for info in camera_info:
                model = info.get("Model", "").lower()
                camera_id = info.get("Id", "").lower()
                
                # Check if this is a USB camera
                if "uvc" in model or "usb" in camera_id:
                    # Keep track of first USB camera found
                    if first_usb_camera is None:
                        first_usb_camera = info
                    
                    # If we have a specific camera ID, check if this is it
                    if self.camera_device_id is not None and info.get("Num") == self.camera_device_id:
                        target_camera = info
                        break
            
            # Select camera based on what we found
            if self.camera_device_id is not None:
                if target_camera is None:
                    raise RuntimeError(f"Camera {self.camera_device_id} is not a USB camera")
                self.logger.info(f"Using specified USB camera {self.camera_device_id}: {target_camera.get('Model', 'Unknown')}")
            else:
                if first_usb_camera is None:
                    raise RuntimeError("No USB cameras found via Picamera2")
                target_camera = first_usb_camera
                self.camera_device_id = target_camera.get("Num")
                self.logger.info(f"Auto-selected USB camera {self.camera_device_id}: {target_camera.get('Model', 'Unknown')}")

            self.camera = Picamera2(self.camera_device_id)
            self.logger.info("USB Camera hardware initialized successfully")

        except Exception as e:
            self.logger.error(f"USBCamera._initialize_hardware failed: {type(e).__name__}: {e}")
            raise

    def start(self) -> bool:
        """Start camera capture."""
        try:
            self.logger.info(f"Starting Preview")
            self.camera.start_preview(
                display_modes[self.display_mode],
                x=self.display_position[0],
                y=self.display_position[1],
                width=self.display_resolution[0],
                height=self.display_resolution[1],
            )

            self.logger.info(f"Starting Camera")
            self.config = self.camera.create_preview_configuration(
                main={"size": self.camera_resolution},
            )
            self.camera.start(self.config)

            self.is_running = True
            self.logger.info("USB Camera started successfully")
            return True

        except Exception as e:
            self.logger.error(f"USBCamera.start failed: {type(e).__name__}: {e}")
            return False

    def stop(self):
        if self.camera is not None and self.is_running:
            self.is_detecting = False
            self.camera.stop()

    def shutdown(self) -> None:
        """Stop camera capture and release resources."""
        try:
            if self.camera is not None:
                self.is_detecting = False
                self.camera.stop()
                self.camera.close()

                self.is_running = False
                self.camera = None

            self.logger.info("USB Camera stopped")

        except Exception as e:
            self.logger.error(f"USBCamera.shutdown failed: {type(e).__name__}: {e}")

    def detect(self, callback=None):
        """Main detection which will run as long as self.is_detecting is True.
        
        Args:
            callback: Optional function to call in the loop for processing (face detection, annotation, etc.)
        """
        self.is_detecting = True

        while self.is_detecting:
            # Call optional callback for processing
            if callback:
                callback(self)
            
            # For USB camera, we just maintain the display
            time.sleep(0.1)  # Small delay to prevent busy waiting

            # Stop if preview object no longer exists (e.g when closed)
            if not self.camera._preview:
                self.is_detecting = False
                self.logger.info("Preview closed")
                break
        self.stop()


if __name__ == "__main__":
    try:
        # Initialize USB camera
        camera = USBCamera()

        # Start the camera
        if camera.start():
            print("USB camera started successfully. Close the preview window to stop.")

            # Run the detect loop (maintains display until closed)
            camera.detect()

        else:
            print("Failed to start USB camera")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Cleanup
        if "camera" in locals():
            camera.shutdown()
            print("USB camera stopped")
