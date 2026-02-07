"""Motion sequence playback for gesture and animation control.

Provides SequenceStep, MotionSequence, and SequencePlayer. Sequences
produce MotionOffset values that feed into OffsetComposer, keeping
gesture control separate from direct servo control.

Example:
    >>> from raspibot.movement.sequence import SequenceStep, MotionSequence, SequencePlayer
    >>> from raspibot.movement.motion_offset import MotionOffset
    >>> from raspibot.movement.interpolation import InterpolationMethod
    >>> step = SequenceStep(MotionOffset(tilt=-8), 0.3, InterpolationMethod.MINJERK)
    >>> seq = MotionSequence("nod", (step,))
    >>> player = SequencePlayer(seq)
    >>> player.start(0.0)
    >>> player.evaluate(0.15)
    MotionOffset(pan=0.0, tilt=-4.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from raspibot.movement.interpolation import InterpolationMethod, interpolate
from raspibot.movement.motion_offset import MotionOffset


@dataclass(frozen=True)
class SequenceStep:
    """One step in a motion sequence.

    Args:
        target: Where to move (as offset from neutral).
        duration: Seconds for this step.
        method: Interpolation method for this step.
    """

    target: MotionOffset
    duration: float
    method: InterpolationMethod


@dataclass(frozen=True)
class MotionSequence:
    """A named sequence of motion steps.

    Args:
        name: Human-readable name for this sequence.
        steps: Ordered tuple of steps to play.
    """

    name: str
    steps: Tuple[SequenceStep, ...]

    @property
    def total_duration(self) -> float:
        """Total duration of the sequence in seconds."""
        return sum(step.duration for step in self.steps)


class SequencePlayer:
    """Evaluates a motion sequence at a given time, producing current offset.

    The player tracks playback state and interpolates between steps.
    Each step interpolates from the previous step's target to the current
    step's target. The first step interpolates from zero offset.

    Args:
        sequence: The MotionSequence to play.

    Example:
        >>> player = SequencePlayer(nod_sequence)
        >>> player.start(current_time)
        >>> offset = player.evaluate(current_time + 0.1)
    """

    def __init__(self, sequence: MotionSequence) -> None:
        """Initialize the player with a sequence."""
        self._sequence = sequence
        self._start_time: Optional[float] = None
        self._complete = False

    def start(self, current_time: float) -> None:
        """Begin playback at the given time.

        Args:
            current_time: The time reference for playback start.
        """
        self._start_time = current_time
        self._complete = False

    @property
    def is_complete(self) -> bool:
        """Whether the sequence has finished playing."""
        return self._complete

    def evaluate(self, current_time: float) -> MotionOffset:
        """Get the offset at current_time.

        Returns zero offset if sequence hasn't started or is complete.

        Args:
            current_time: Current time for evaluation.

        Returns:
            Interpolated MotionOffset for this point in time.
        """
        if self._start_time is None:
            return MotionOffset()

        elapsed = current_time - self._start_time
        total = self._sequence.total_duration

        if elapsed > total:
            self._complete = True
            return MotionOffset()

        # Find which step we're in
        step_start = 0.0
        prev_target = MotionOffset()

        for step in self._sequence.steps:
            step_end = step_start + step.duration

            if elapsed < step_end:
                # We're in this step
                t = (elapsed - step_start) / step.duration
                fraction = interpolate(t, step.method)

                pan = prev_target.pan + (step.target.pan - prev_target.pan) * fraction
                tilt = prev_target.tilt + (step.target.tilt - prev_target.tilt) * fraction

                return MotionOffset(pan=pan, tilt=tilt)

            prev_target = step.target
            step_start = step_end

        # At exact total_duration boundary, return last step's target
        return prev_target
