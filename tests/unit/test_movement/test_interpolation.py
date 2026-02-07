"""Unit tests for interpolation functions."""

import pytest

from raspibot.movement.interpolation import (
    InterpolationMethod,
    interpolate,
    linear,
    minjerk,
    ease_in_out,
)


class TestLinear:
    """Tests for linear interpolation."""

    def test_start(self) -> None:
        """Linear at t=0 returns 0."""
        assert linear(0.0) == 0.0

    def test_end(self) -> None:
        """Linear at t=1 returns 1."""
        assert linear(1.0) == 1.0

    def test_midpoint(self) -> None:
        """Linear at t=0.5 returns 0.5."""
        assert linear(0.5) == 0.5

    def test_quarter(self) -> None:
        """Linear at t=0.25 returns 0.25."""
        assert linear(0.25) == 0.25

    def test_monotonic(self) -> None:
        """Linear is monotonically increasing."""
        values = [linear(t / 100.0) for t in range(101)]
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1]


class TestMinjerk:
    """Tests for minimum-jerk interpolation."""

    def test_start(self) -> None:
        """Minjerk at t=0 returns 0."""
        assert minjerk(0.0) == pytest.approx(0.0)

    def test_end(self) -> None:
        """Minjerk at t=1 returns 1."""
        assert minjerk(1.0) == pytest.approx(1.0)

    def test_midpoint(self) -> None:
        """Minjerk at t=0.5 returns 0.5."""
        assert minjerk(0.5) == pytest.approx(0.5)

    def test_monotonic(self) -> None:
        """Minjerk is monotonically increasing on [0,1]."""
        values = [minjerk(t / 100.0) for t in range(101)]
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1]

    def test_slow_start(self) -> None:
        """Minjerk starts slow (value near 0 at t=0.1)."""
        assert minjerk(0.1) < 0.05

    def test_slow_end(self) -> None:
        """Minjerk ends slow (value near 1 at t=0.9)."""
        assert minjerk(0.9) > 0.95

    def test_symmetric(self) -> None:
        """Minjerk is symmetric: f(t) + f(1-t) = 1."""
        for t in [0.1, 0.2, 0.3, 0.4]:
            assert minjerk(t) + minjerk(1.0 - t) == pytest.approx(1.0)


class TestEaseInOut:
    """Tests for ease-in-out interpolation."""

    def test_start(self) -> None:
        """Ease-in-out at t=0 returns 0."""
        assert ease_in_out(0.0) == pytest.approx(0.0)

    def test_end(self) -> None:
        """Ease-in-out at t=1 returns 1."""
        assert ease_in_out(1.0) == pytest.approx(1.0)

    def test_midpoint(self) -> None:
        """Ease-in-out at t=0.5 returns 0.5."""
        assert ease_in_out(0.5) == pytest.approx(0.5)

    def test_monotonic(self) -> None:
        """Ease-in-out is monotonically increasing on [0,1]."""
        values = [ease_in_out(t / 100.0) for t in range(101)]
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1]

    def test_slow_start(self) -> None:
        """Ease-in-out starts slow."""
        assert ease_in_out(0.1) < 0.1

    def test_slow_end(self) -> None:
        """Ease-in-out ends slow."""
        assert ease_in_out(0.9) > 0.9


class TestInterpolateDispatch:
    """Tests for the interpolate() dispatch function."""

    def test_linear_dispatch(self) -> None:
        """interpolate with LINEAR uses linear function."""
        assert interpolate(0.5, InterpolationMethod.LINEAR) == 0.5

    def test_minjerk_dispatch(self) -> None:
        """interpolate with MINJERK uses minjerk function."""
        assert interpolate(0.5, InterpolationMethod.MINJERK) == pytest.approx(0.5)

    def test_ease_in_out_dispatch(self) -> None:
        """interpolate with EASE_IN_OUT uses ease_in_out function."""
        assert interpolate(0.5, InterpolationMethod.EASE_IN_OUT) == pytest.approx(0.5)

    def test_default_is_linear(self) -> None:
        """Default method is LINEAR."""
        assert interpolate(0.25) == 0.25


class TestInterpolationMethodEnum:
    """Tests for InterpolationMethod enum."""

    def test_three_methods(self) -> None:
        """Enum has exactly three methods."""
        assert len(InterpolationMethod) == 3

    def test_values(self) -> None:
        """Enum values are meaningful strings."""
        assert InterpolationMethod.LINEAR.value == "linear"
        assert InterpolationMethod.MINJERK.value == "minjerk"
        assert InterpolationMethod.EASE_IN_OUT.value == "ease_in_out"
