"""Unit tests for SequenceStep, MotionSequence, and SequencePlayer."""

import pytest

from raspibot.movement.interpolation import InterpolationMethod
from raspibot.movement.motion_offset import MotionOffset
from raspibot.movement.sequence import SequenceStep, MotionSequence, SequencePlayer


class TestSequenceStep:
    """Tests for SequenceStep dataclass."""

    def test_create_step(self) -> None:
        """SequenceStep stores target, duration, and method."""
        step = SequenceStep(
            target=MotionOffset(tilt=-8.0),
            duration=0.3,
            method=InterpolationMethod.MINJERK,
        )
        assert step.target.tilt == -8.0
        assert step.duration == 0.3
        assert step.method == InterpolationMethod.MINJERK

    def test_immutable(self) -> None:
        """SequenceStep is frozen."""
        step = SequenceStep(
            target=MotionOffset(), duration=1.0, method=InterpolationMethod.LINEAR
        )
        with pytest.raises(AttributeError):
            step.duration = 2.0  # type: ignore[misc]


class TestMotionSequence:
    """Tests for MotionSequence dataclass."""

    def test_create_sequence(self) -> None:
        """MotionSequence stores name and steps."""
        steps = (
            SequenceStep(MotionOffset(tilt=-8.0), 0.3, InterpolationMethod.MINJERK),
            SequenceStep(MotionOffset(tilt=0.0), 0.3, InterpolationMethod.MINJERK),
        )
        seq = MotionSequence(name="nod", steps=steps)
        assert seq.name == "nod"
        assert len(seq.steps) == 2

    def test_total_duration(self) -> None:
        """Total duration is sum of step durations."""
        steps = (
            SequenceStep(MotionOffset(), 0.3, InterpolationMethod.LINEAR),
            SequenceStep(MotionOffset(), 0.5, InterpolationMethod.LINEAR),
        )
        seq = MotionSequence(name="test", steps=steps)
        assert seq.total_duration == pytest.approx(0.8)


class TestSequencePlayer:
    """Tests for SequencePlayer."""

    @pytest.fixture
    def single_step_sequence(self) -> MotionSequence:
        """A simple single-step sequence."""
        return MotionSequence(
            name="single",
            steps=(
                SequenceStep(
                    target=MotionOffset(pan=10.0),
                    duration=1.0,
                    method=InterpolationMethod.LINEAR,
                ),
            ),
        )

    @pytest.fixture
    def two_step_sequence(self) -> MotionSequence:
        """A two-step sequence."""
        return MotionSequence(
            name="two_step",
            steps=(
                SequenceStep(
                    target=MotionOffset(tilt=-8.0),
                    duration=0.5,
                    method=InterpolationMethod.LINEAR,
                ),
                SequenceStep(
                    target=MotionOffset(tilt=0.0),
                    duration=0.5,
                    method=InterpolationMethod.LINEAR,
                ),
            ),
        )

    def test_not_complete_before_start(self, single_step_sequence: MotionSequence) -> None:
        """Player is not complete before starting."""
        player = SequencePlayer(single_step_sequence)
        assert not player.is_complete

    def test_evaluate_at_start(self, single_step_sequence: MotionSequence) -> None:
        """At t=0 offset is zero (start of first step)."""
        player = SequencePlayer(single_step_sequence)
        player.start(0.0)
        offset = player.evaluate(0.0)
        assert offset.pan == pytest.approx(0.0)

    def test_evaluate_at_mid(self, single_step_sequence: MotionSequence) -> None:
        """At t=0.5 (midpoint), offset is half target (linear)."""
        player = SequencePlayer(single_step_sequence)
        player.start(0.0)
        offset = player.evaluate(0.5)
        assert offset.pan == pytest.approx(5.0)

    def test_evaluate_at_end(self, single_step_sequence: MotionSequence) -> None:
        """At t=1.0 (end), offset equals target."""
        player = SequencePlayer(single_step_sequence)
        player.start(0.0)
        offset = player.evaluate(1.0)
        assert offset.pan == pytest.approx(10.0)

    def test_is_complete_after_end(self, single_step_sequence: MotionSequence) -> None:
        """Player is complete after total duration passes."""
        player = SequencePlayer(single_step_sequence)
        player.start(0.0)
        player.evaluate(1.1)
        assert player.is_complete

    def test_evaluate_after_complete_returns_zero(
        self, single_step_sequence: MotionSequence
    ) -> None:
        """After completion, evaluate returns zero offset."""
        player = SequencePlayer(single_step_sequence)
        player.start(0.0)
        offset = player.evaluate(2.0)
        assert offset.pan == pytest.approx(0.0)
        assert offset.tilt == pytest.approx(0.0)

    def test_two_step_first_half(self, two_step_sequence: MotionSequence) -> None:
        """During first step, offset interpolates toward first target."""
        player = SequencePlayer(two_step_sequence)
        player.start(0.0)
        offset = player.evaluate(0.25)  # Midpoint of first step
        assert offset.tilt == pytest.approx(-4.0)

    def test_two_step_transition(self, two_step_sequence: MotionSequence) -> None:
        """At step boundary, offset equals first step target."""
        player = SequencePlayer(two_step_sequence)
        player.start(0.0)
        # At t=0.5, just at end of first step / start of second
        offset = player.evaluate(0.5)
        assert offset.tilt == pytest.approx(-8.0)

    def test_two_step_second_half(self, two_step_sequence: MotionSequence) -> None:
        """During second step, offset interpolates from first target to second."""
        player = SequencePlayer(two_step_sequence)
        player.start(0.0)
        offset = player.evaluate(0.75)  # Midpoint of second step
        # Interpolates from -8.0 to 0.0, at midpoint = -4.0
        assert offset.tilt == pytest.approx(-4.0)

    def test_two_step_end(self, two_step_sequence: MotionSequence) -> None:
        """At end of two-step sequence, offset equals last target."""
        player = SequencePlayer(two_step_sequence)
        player.start(0.0)
        offset = player.evaluate(1.0)
        assert offset.tilt == pytest.approx(0.0)

    def test_minjerk_produces_nonlinear_curve(self) -> None:
        """With minjerk, offset at t=0.1 is smaller than linear."""
        seq = MotionSequence(
            name="minjerk_test",
            steps=(
                SequenceStep(
                    target=MotionOffset(pan=10.0),
                    duration=1.0,
                    method=InterpolationMethod.MINJERK,
                ),
            ),
        )
        player = SequencePlayer(seq)
        player.start(0.0)
        offset = player.evaluate(0.1)
        # Minjerk at t=0.1 is ~0.009, so offset ~0.09
        assert offset.pan < 0.5  # Much less than linear's 1.0

    def test_start_with_offset_time(self) -> None:
        """Player can start at a non-zero time."""
        seq = MotionSequence(
            name="offset_start",
            steps=(
                SequenceStep(
                    target=MotionOffset(pan=10.0),
                    duration=1.0,
                    method=InterpolationMethod.LINEAR,
                ),
            ),
        )
        player = SequencePlayer(seq)
        player.start(100.0)
        offset = player.evaluate(100.5)
        assert offset.pan == pytest.approx(5.0)
