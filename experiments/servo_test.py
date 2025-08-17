from pathlib import Path
import sys
import time

sys.path.insert(0, Path(__file__).absolute().parent.parent)


from raspibot.hardware.servos.servo import PCA9685ServoController

controller = PCA9685ServoController()

for angle in range(85, 105):

    # controller.set_servo_angle(0, 0)
    # time.sleep(1)
    print(angle)
    controller.set_servo_angle(0, angle)
    time.sleep(0.5)

    controller.set_servo_angle(0, 0)
controller.shutdown()
