from pathlib import Path
import sys
import time

sys.path.insert(0, Path(__file__).absolute().parent.parent)


from raspibot.hardware.servos.servo import PCA9685ServoController

controller = PCA9685ServoController()

print("Moving 0")
# .set_servo_angle("pan", 0)
print("Moving 1")
controller.set_servo_angle("tilt", 80)
controller.shutdown()
