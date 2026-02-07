"""Unit tests for predefined gesture sequences."""

import pytest

from raspibot.movement.gestures import NOD, SHAKE, ATTENTION
from raspibot.movement.motion_offset import MotionOffset
from raspibot.movement.sequence import MotionSequence, SequencePlayer


class TestGestureDefinitions:
    """Tests for predefined gesture constants."""

    def test_nod_is_motion_sequence(self) -> None:
        """NOD is a MotionSequence."""
        assert isinstance(NOD, MotionSequence)

    def test_nod_name(self) -> None:
        """NOD has correct name."""
        assert NOD.name == "nod"

    def test_nod_uses_tilt(self) -> None:
        """NOD primarily uses tilt axis."""
        for step in NOD.steps:
            assert step.target.pan == 0.0

    def test_shake_is_motion_sequence(self) -> None:
        """SHAKE is a MotionSequence."""
        assert isinstance(SHAKE, MotionSequence)

    def test_shake_name(self) -> None:
        """SHAKE has correct name."""
        assert SHAKE.name == "shake"

    def test_shake_uses_pan(self) -> None:
        """SHAKE primarily uses pan axis."""
        for step in SHAKE.steps:
            assert step.target.tilt == 0.0

    def test_shake_returns_to_zero(self) -> None:
        """SHAKE ends at zero offset."""
        assert SHAKE.steps[-1].target.pan == 0.0

    def test_attention_is_motion_sequence(self) -> None:
        """ATTENTION is a MotionSequence."""
        assert isinstance(ATTENTION, MotionSequence)

    def test_attention_name(self) -> None:
        """ATTENTION has correct name."""
        assert ATTENTION.name == "attention"

    def test_attention_returns_to_zero(self) -> None:
        """ATTENTION ends at zero offset."""
        assert ATTENTION.steps[-1].target.tilt == 0.0


class TestGesturePlayback:
    """Tests for playing gestures through SequencePlayer."""

    def test_nod_produces_tilt_offset(self) -> None:
        """Playing NOD produces tilt offset at midpoint."""
        player = SequencePlayer(NOD)
        player.start(0.0)
        mid_time = NOD.steps[0].duration / 2
        offset = player.evaluate(mid_time)
        assert offset.tilt != 0.0

    def test_shake_produces_pan_offset(self) -> None:
        """Playing SHAKE produces pan offset during playback."""
        player = SequencePlayer(SHAKE)
        player.start(0.0)
        mid_time = SHAKE.steps[0].duration / 2
        offset = player.evaluate(mid_time)
        assert offset.pan != 0.0

    def test_all_gestures_complete(self) -> None:
        """All gestures complete after their total duration."""
        for gesture in [NOD, SHAKE, ATTENTION]:
            player = SequencePlayer(gesture)
            player.start(0.0)
            player.evaluate(gesture.total_duration + 0.1)
            assert player.is_complete, f"{gesture.name} did not complete"
