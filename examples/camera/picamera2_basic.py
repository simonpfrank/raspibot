import sys
import os
import cv2
import time
from pathlib import Path
from picamera2 import Picamera2,Preview

# If using Raspberry Pi Connect or VNC, you will need to research how to set up the display
# for a connected display remove these lines
os.environ['DISPLAY'] = ':0' # for headles displays
os.environ['QT_QPA_PLATFORM'] = 'wayland' # for software rendering

camera = Picamera2()
config = camera.create_preview_configuration()
camera.configure(config)
camera.start_preview(Preview.QT) # May need QTGL or DRM for ssh only
camera.start()
time.sleep(10)
camera.stop()







