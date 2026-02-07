"""Unit tests for MotionOffset and OffsetComposer."""

import pytest

from raspibot.movement.motion_offset import MotionOffset, OffsetComposer


class TestMotionOffset:
    """Tests for MotionOffset dataclass."""

    def test_default_values(self) -> None:
        """Default offset is zero for both axes."""
        offset = MotionOffset()
        assert offset.pan == 0.0
        assert offset.tilt == 0.0

    def test_custom_values(self) -> None:
        """MotionOffset stores given pan and tilt."""
        offset = MotionOffset(pan=5.0, tilt=-3.0)
        assert offset.pan == 5.0
        assert offset.tilt == -3.0

    def test_immutable(self) -> None:
        """MotionOffset is frozen (immutable)."""
        offset = MotionOffset(pan=5.0)
        with pytest.raises(AttributeError):
            offset.pan = 10.0  # type: ignore[misc]

    def test_add_zero(self) -> None:
        """Adding zero offset returns same values."""
        a = MotionOffset(pan=5.0, tilt=-3.0)
        b = MotionOffset()
        result = a + b
        assert result.pan == 5.0
        assert result.tilt == -3.0

    def test_add_positive_negative(self) -> None:
        """Adding positive and negative offsets."""
        a = MotionOffset(pan=5.0, tilt=-3.0)
        b = MotionOffset(pan=-2.0, tilt=7.0)
        result = a + b
        assert result.pan == pytest.approx(3.0)
        assert result.tilt == pytest.approx(4.0)

    def test_add_commutative(self) -> None:
        """Addition is commutative."""
        a = MotionOffset(pan=5.0, tilt=-3.0)
        b = MotionOffset(pan=-2.0, tilt=7.0)
        assert (a + b).pan == (b + a).pan
        assert (a + b).tilt == (b + a).tilt

    def test_add_returns_new_instance(self) -> None:
        """Addition returns a new MotionOffset, does not mutate."""
        a = MotionOffset(pan=5.0, tilt=-3.0)
        b = MotionOffset(pan=1.0, tilt=1.0)
        result = a + b
        assert result is not a
        assert result is not b


class TestOffsetComposer:
    """Tests for OffsetComposer."""

    def test_no_offsets_returns_base(self) -> None:
        """With no offsets, resolve returns base position."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(90.0, 90.0)
        assert composer.resolve() == (90.0, 90.0)

    def test_one_offset_adds_to_base(self) -> None:
        """Single offset is added to base."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(90.0, 90.0)
        composer.set_offset("tracking", MotionOffset(pan=5.0, tilt=-3.0))
        pan, tilt = composer.resolve()
        assert pan == pytest.approx(95.0)
        assert tilt == pytest.approx(87.0)

    def test_multiple_offsets_sum(self) -> None:
        """Multiple offsets are summed."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(90.0, 90.0)
        composer.set_offset("tracking", MotionOffset(pan=5.0, tilt=0.0))
        composer.set_offset("gesture", MotionOffset(pan=-2.0, tilt=-8.0))
        pan, tilt = composer.resolve()
        assert pan == pytest.approx(93.0)
        assert tilt == pytest.approx(82.0)

    def test_clear_offset(self) -> None:
        """Clearing an offset removes it from computation."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(90.0, 90.0)
        composer.set_offset("tracking", MotionOffset(pan=10.0))
        composer.clear_offset("tracking")
        assert composer.resolve() == (90.0, 90.0)

    def test_clear_nonexistent_offset_safe(self) -> None:
        """Clearing a non-existent offset does not raise."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(90.0, 90.0)
        composer.clear_offset("nonexistent")
        assert composer.resolve() == (90.0, 90.0)

    def test_clamp_pan_max(self) -> None:
        """Pan is clamped to upper limit."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(170.0, 90.0)
        composer.set_offset("big", MotionOffset(pan=20.0))
        pan, _ = composer.resolve()
        assert pan == 180.0

    def test_clamp_pan_min(self) -> None:
        """Pan is clamped to lower limit."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(10.0, 90.0)
        composer.set_offset("big", MotionOffset(pan=-20.0))
        pan, _ = composer.resolve()
        assert pan == 0.0

    def test_clamp_tilt_max(self) -> None:
        """Tilt is clamped to upper limit."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 150.0))
        composer.set_base(90.0, 140.0)
        composer.set_offset("big", MotionOffset(tilt=20.0))
        _, tilt = composer.resolve()
        assert tilt == 150.0

    def test_clamp_tilt_min(self) -> None:
        """Tilt is clamped to lower limit."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 150.0))
        composer.set_base(90.0, 10.0)
        composer.set_offset("big", MotionOffset(tilt=-20.0))
        _, tilt = composer.resolve()
        assert tilt == 0.0

    def test_replace_offset(self) -> None:
        """Setting an offset with same name replaces the previous one."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_base(90.0, 90.0)
        composer.set_offset("tracking", MotionOffset(pan=10.0))
        composer.set_offset("tracking", MotionOffset(pan=-5.0))
        pan, _ = composer.resolve()
        assert pan == pytest.approx(85.0)

    def test_default_base_is_zero(self) -> None:
        """Default base position is (0, 0)."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        assert composer.resolve() == (0.0, 0.0)

    def test_active_layers(self) -> None:
        """Can query which offset layers are active."""
        composer = OffsetComposer(pan_limits=(0.0, 180.0), tilt_limits=(0.0, 180.0))
        composer.set_offset("tracking", MotionOffset(pan=5.0))
        composer.set_offset("gesture", MotionOffset(tilt=-3.0))
        assert set(composer.active_layers) == {"tracking", "gesture"}
