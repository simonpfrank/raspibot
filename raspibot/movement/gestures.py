"""Predefined motion gesture sequences.

Each gesture is a MotionSequence that produces MotionOffset values.
Feed these through SequencePlayer and OffsetComposer for playback.

Available gestures:
    NOD: Double nod — up, down, up, down to center (acknowledgment).
    NO: Smooth head shake — right, left, right, back (disagreement).
    SHAKE: Pan left, right, center (searching).
    ATTENTION: Tilt up sharply, overshoot down, settle (alertness).

Example:
    >>> from raspibot.movement.gestures import NOD
    >>> from raspibot.movement.sequence import SequencePlayer
    >>> player = SequencePlayer(NOD)
    >>> player.start(0.0)
"""

from raspibot.movement.interpolation import InterpolationMethod
from raspibot.movement.motion_offset import MotionOffset
from raspibot.movement.sequence import MotionSequence, SequenceStep

NOD = MotionSequence(
    name="nod",
    steps=(
        SequenceStep(
            target=MotionOffset(tilt=12.0),
            duration=0.25,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(tilt=-12.0),
            duration=0.25,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(tilt=12.0),
            duration=0.25,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(tilt=0.0),
            duration=0.25,
            method=InterpolationMethod.MINJERK,
        ),
    ),
)

NO = MotionSequence(
    name="no",
    steps=(
        SequenceStep(
            target=MotionOffset(pan=10.0),
            duration=0.3,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(pan=-10.0),
            duration=0.3,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(pan=10.0),
            duration=0.3,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(pan=0.0),
            duration=0.3,
            method=InterpolationMethod.MINJERK,
        ),
    ),
)

SHAKE = MotionSequence(
    name="shake",
    steps=(
        SequenceStep(
            target=MotionOffset(pan=-10.0),
            duration=0.25,
            method=InterpolationMethod.EASE_IN_OUT,
        ),
        SequenceStep(
            target=MotionOffset(pan=10.0),
            duration=0.25,
            method=InterpolationMethod.EASE_IN_OUT,
        ),
        SequenceStep(
            target=MotionOffset(pan=0.0),
            duration=0.25,
            method=InterpolationMethod.EASE_IN_OUT,
        ),
    ),
)

ATTENTION = MotionSequence(
    name="attention",
    steps=(
        SequenceStep(
            target=MotionOffset(tilt=-10.0),
            duration=0.2,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(tilt=6.0),
            duration=0.4,
            method=InterpolationMethod.MINJERK,
        ),
        SequenceStep(
            target=MotionOffset(tilt=0.0),
            duration=0.3,
            method=InterpolationMethod.MINJERK,
        ),
    ),
)
