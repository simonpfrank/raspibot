"""Demonstrate all hardware movement patterns.

Plays each gesture and an elliptical sweep on real servo hardware,
announcing each one before it runs.

Run:
    python -m examples.movement.04_hardware_gestures
"""

import asyncio
import logging
import math
import time

from raspibot.hardware.servos.servo import PCA9685ServoController
from raspibot.movement.gestures import ATTENTION, NO, NOD, SHAKE
from raspibot.movement.motion_controller import MotionController
from raspibot.movement.sequence import MotionSequence

logging.basicConfig(level=logging.WARNING)

BASE_PAN = 86.0
BASE_TILT = 75.0

# Ellipse parameters
PAN_CENTER = 90.0
PAN_AMPLITUDE = 60.0
TILT_CENTER = 75.0
TILT_AMPLITUDE = 50.0
JITTER_LOW = 87.0
JITTER_HIGH = 104.0
JITTER_MID = (JITTER_LOW + JITTER_HIGH) / 2.0
STEPS_PER_LOOP = 120
TICK_INTERVAL = 0.025

GESTURES: list[tuple[MotionSequence, str]] = [
    (NOD, "NOD — tilt down, up past center, back (acknowledgment)"),
    (NO, "NO — pan right, left, right, back (disagreement)"),
    (SHAKE, "SHAKE — pan left, right, center (searching)"),
    (ATTENTION, "ATTENTION — subtle tilt up with overshoot (alertness)"),
]


async def play_ellipse(mc: MotionController) -> None:
    """Trace an ellipse using hold-edge to avoid jitter zone."""
    mc.set_base(PAN_CENTER + PAN_AMPLITUDE, TILT_CENTER)
    mc.apply()
    await asyncio.sleep(0.5)

    for step in range(STEPS_PER_LOOP + 1):
        theta = 2.0 * math.pi * step / STEPS_PER_LOOP
        pan = PAN_CENTER + PAN_AMPLITUDE * math.cos(theta)
        tilt = TILT_CENTER + TILT_AMPLITUDE * math.sin(theta)

        if JITTER_LOW <= pan <= JITTER_HIGH:
            pan = JITTER_LOW - 1.0 if pan < JITTER_MID else JITTER_HIGH + 1.0

        mc.set_base(pan, tilt)
        mc.apply()
        await asyncio.sleep(TICK_INTERVAL)


async def main() -> None:
    """Run each movement pattern one by one."""
    servo = PCA9685ServoController()
    mc = MotionController(servo)

    mc.set_base(BASE_PAN, BASE_TILT)
    mc.apply()
    time.sleep(1.0)

    for gesture, description in GESTURES:
        print(f"\nNext: {description}")
        time.sleep(1.5)
        await mc.play_gesture(gesture)
        print("  Done.")
        time.sleep(1.0)

    print("\nNext: ELLIPSE — smooth circular sweep covering 2/3 of each axis")
    time.sleep(1.5)
    await play_ellipse(mc)
    print("  Done.")

    mc.set_base(BASE_PAN, BASE_TILT)
    mc.apply()
    time.sleep(0.5)
    print("\nAll movements complete.")
    servo.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
