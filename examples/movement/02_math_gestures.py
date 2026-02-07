"""Demonstrate predefined gesture sequences.

Shows how to play NOD, SHAKE, and ATTENTION gestures through
a SequencePlayer, printing the offset at each time step.

Run:
    python -m examples.movement.02_math_gestures
"""

from raspibot.movement.gestures import ATTENTION, NOD, SHAKE
from raspibot.movement.sequence import MotionSequence, SequencePlayer

TIME_STEP = 0.05  # seconds between samples


def play_gesture(gesture: MotionSequence) -> None:
    """Print offsets for a gesture over its full duration."""
    print(f"\n{gesture.name.upper()} (duration={gesture.total_duration:.2f}s)")
    print(f"  {'time':>6}  {'pan':>8}  {'tilt':>8}")
    print(f"  {'----':>6}  {'----':>8}  {'----':>8}")

    player = SequencePlayer(gesture)
    player.start(0.0)

    t = 0.0
    while not player.is_complete:
        offset = player.evaluate(t)
        print(f"  {t:6.2f}  {offset.pan:8.2f}  {offset.tilt:8.2f}")
        t += TIME_STEP

    # Show final state
    offset = player.evaluate(t)
    print(f"  {t:6.2f}  {offset.pan:8.2f}  {offset.tilt:8.2f}  (complete)")


def main() -> None:
    """Play all three predefined gestures."""
    print("Gesture Playback")
    print("================")
    print("Each gesture produces pan/tilt offsets over time.")
    print("Feed these into OffsetComposer for real servo control.")

    for gesture in (NOD, SHAKE, ATTENTION):
        play_gesture(gesture)


if __name__ == "__main__":
    main()
