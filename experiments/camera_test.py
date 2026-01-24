from pathlib import Path
import sys
import time
from threading import Thread

sys.path.insert(0, Path(__file__).absolute().parent.parent)


from raspibot.hardware.cameras.camera import Camera

camera = Camera()
camera.start()
camera.process()

while True:
    time.sleep(1)
