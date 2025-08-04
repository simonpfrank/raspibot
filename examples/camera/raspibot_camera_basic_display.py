import sys
import os
os.environ['OPENCV_LOG_LEVEL'] = 'OFF' # turn off opencv logging while looking for USB cameras
import cv2  
from pathlib import Path

# Add path to raspibot for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from raspibot.hardware.cameras import get_camera, CameraType, get_available_cameras, get_best_available_camera
from raspibot.hardware.cameras.active_usb_cameras import find_active_usb_cameras
from raspibot.utils.logging_config import setup_logging

os.environ['DISPLAY'] = ':0' #required for headless via raspbery connect

logger = setup_logging('Raspibot Camera Basic Display')

# MENU Get possible types of cameras (for connected cameras use get_available_cameras())
print('-'*100)
print('select the type of camera to use (or q to quit):')
camera_list = list(enumerate(CameraType))
for index, camera in camera_list:
    print(f"{index}: {camera.value}")
camera_index = input("Enter the camera number: ")
if camera_index == 'q':
    exit()

# Start the selected camera
camera_index = int(camera_index)
camera_type = camera_list[camera_index][1]

if camera_type == CameraType.USB: 
    logger.info("searching for active USB cameras")
    active_cameras = find_active_usb_cameras()
    if len(active_cameras) > 0:
        logger.info(f"found {len(active_cameras)} active USB cameras, using the first one ({active_cameras[0]})")
        camera = get_camera(camera_type,device_id=active_cameras[0])
else:
    camera = get_camera(camera_type)  

logger.info(f"Using camera type: {camera_type}")
camera.start()

# Use opencv as the simple display
while True:
    frame = camera.get_frame()
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break

camera.shutdown()