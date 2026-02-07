"""Interpolation functions for smooth servo movement.

Provides different easing curves for servo transitions:
- LINEAR: Constant speed (default for backward compatibility).
- MINJERK: Minimum-jerk trajectory — smooth start and stop, bio-inspired.
- EASE_IN_OUT: Quadratic ease-in/ease-out — snappy in the middle.

Example:
    >>> from raspibot.movement.interpolation import interpolate, InterpolationMethod
    >>> interpolate(0.5, InterpolationMethod.MINJERK)
    0.5
"""

from enum import Enum


class InterpolationMethod(Enum):
    """Available interpolation methods for servo movement."""

    LINEAR = "linear"
    MINJERK = "minjerk"
    EASE_IN_OUT = "ease_in_out"


def linear(t: float) -> float:
    """Linear interpolation (constant speed).

    Args:
        t: Progress fraction (0.0 to 1.0).

    Returns:
        Position fraction (0.0 to 1.0).
    """
    return t


def minjerk(t: float) -> float:
    """Minimum-jerk trajectory (smooth start and stop).

    The minimum-jerk polynomial: 10t^3 - 15t^4 + 6t^5.
    Zero velocity and acceleration at endpoints.

    Args:
        t: Progress fraction (0.0 to 1.0).

    Returns:
        Position fraction (0.0 to 1.0).
    """
    return 10.0 * t**3 - 15.0 * t**4 + 6.0 * t**5


def ease_in_out(t: float) -> float:
    """Quadratic ease-in/ease-out (slow start and end, fast middle).

    Args:
        t: Progress fraction (0.0 to 1.0).

    Returns:
        Position fraction (0.0 to 1.0).
    """
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


_METHODS = {
    InterpolationMethod.LINEAR: linear,
    InterpolationMethod.MINJERK: minjerk,
    InterpolationMethod.EASE_IN_OUT: ease_in_out,
}


def interpolate(
    t: float, method: InterpolationMethod = InterpolationMethod.LINEAR
) -> float:
    """Map progress fraction to position fraction using given method.

    Args:
        t: Progress fraction (0.0 to 1.0).
        method: Interpolation method to use. Default LINEAR.

    Returns:
        Position fraction (0.0 to 1.0).
    """
    return _METHODS[method](t)
