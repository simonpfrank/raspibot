"""Motion offset layer for composable servo control.

Provides MotionOffset (an immutable pan/tilt offset) and OffsetComposer
(combines a base position with named offset layers). This allows multiple
behaviours (tracking, gestures, nudges) to contribute to final servo
position without fighting for control.

Example:
    >>> composer = OffsetComposer(pan_limits=(0, 180), tilt_limits=(0, 150))
    >>> composer.set_base(90.0, 90.0)
    >>> composer.set_offset("tracking", MotionOffset(pan=5.0))
    >>> composer.resolve()
    (95.0, 90.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class MotionOffset:
    """An immutable pan/tilt offset.

    Args:
        pan: Pan offset in degrees. Default 0.0.
        tilt: Tilt offset in degrees. Default 0.0.
    """

    pan: float = 0.0
    tilt: float = 0.0

    def __add__(self, other: MotionOffset) -> MotionOffset:
        """Add two offsets together.

        Args:
            other: Another MotionOffset to add.

        Returns:
            New MotionOffset with summed pan and tilt.
        """
        return MotionOffset(pan=self.pan + other.pan, tilt=self.tilt + other.tilt)


class OffsetComposer:
    """Combines a base position with named offset layers.

    The final servo position is: base + sum(all offsets), clamped to limits.
    Named layers make it easy to debug which behaviour is contributing.

    Args:
        pan_limits: (min, max) pan angle in degrees.
        tilt_limits: (min, max) tilt angle in degrees.

    Example:
        >>> composer = OffsetComposer((0, 180), (0, 150))
        >>> composer.set_base(90, 90)
        >>> composer.set_offset("gesture", MotionOffset(tilt=-8))
        >>> composer.resolve()
        (90.0, 82.0)
    """

    def __init__(
        self,
        pan_limits: Tuple[float, float],
        tilt_limits: Tuple[float, float],
    ) -> None:
        """Initialize with servo limits."""
        self._pan_min, self._pan_max = pan_limits
        self._tilt_min, self._tilt_max = tilt_limits
        self._base_pan: float = 0.0
        self._base_tilt: float = 0.0
        self._offsets: Dict[str, MotionOffset] = {}

    def set_base(self, pan: float, tilt: float) -> None:
        """Set the base position (from scanner or primary behaviour).

        Args:
            pan: Base pan angle in degrees.
            tilt: Base tilt angle in degrees.
        """
        self._base_pan = pan
        self._base_tilt = tilt

    def set_offset(self, layer_name: str, offset: MotionOffset) -> None:
        """Set offset for a named layer.

        Args:
            layer_name: Name of the offset layer (e.g., 'tracking', 'gesture').
            offset: The offset to apply.
        """
        self._offsets[layer_name] = offset

    def clear_offset(self, layer_name: str) -> None:
        """Remove a named offset layer.

        Args:
            layer_name: Name of the offset layer to remove.
        """
        self._offsets.pop(layer_name, None)

    @property
    def active_layers(self) -> List[str]:
        """Get names of all active offset layers.

        Returns:
            List of active layer names.
        """
        return list(self._offsets.keys())

    def resolve(self) -> Tuple[float, float]:
        """Compute final (pan, tilt) = base + sum(offsets), clamped to limits.

        Returns:
            Tuple of (pan, tilt) in degrees, clamped to servo limits.
        """
        total = MotionOffset()
        for offset in self._offsets.values():
            total = total + offset

        pan = self._base_pan + total.pan
        tilt = self._base_tilt + total.tilt

        pan = max(self._pan_min, min(self._pan_max, pan))
        tilt = max(self._tilt_min, min(self._tilt_max, tilt))

        return (pan, tilt)
