import os
from pathlib import Path
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
import cv2
import functools
import signal
import time

from raspibot.utils.logging_config import setup_logging
logger = setup_logging('USB Video Check')

video_devices = Path('/dev').glob('video*')

device_numbers = [int(device.name.replace('video', '')) for device in video_devices]
device_numbers.sort()

active_cameras=[]


def timeout(max_timeout, default=None):
    """Timeout decorator, parameter in seconds."""
    def timeout_decorator(func):
        """Wrap the original function."""
        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            """Timeout using signal."""
            class MyTimeoutError(Exception):
                pass
            def handler(signum, frame):
                raise MyTimeoutError(
                    f"{func.__name__} - Timeout after {max_timeout} seconds"
                )
            # set the timeout handler
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(max_timeout)
            result = default
            try:
                result = func(*args, **kwargs)
            except MyTimeoutError as exc:
                # handle the timeout
                logger.error("Timeout error",str(exc))
            finally:
                # Cancel the timer
                signal.alarm(0)
            return result
        return func_wrapper
    return timeout_decorator


@timeout(max_timeout=2)
def check_camera(device_number):
    logger.info(f"Checking camera:{device_number}")
    try:
        cap = cv2.VideoCapture(device_number)
        if cap is None or not cap.isOpened():
            return False
        result,frame = cap.read()
        if result:
            logger.info(f"Camera {device_number} is active")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"CV2 error {str(e)}")
        return False
    finally:
        cap.release()

def find_active_usb_cameras():
    for device_number in device_numbers:
        result = check_camera(device_number)
        if result:
            active_cameras.append(device_number)
        else:
            continue
    return active_cameras
    
