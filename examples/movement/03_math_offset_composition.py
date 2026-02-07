"""Demonstrate offset composition with multiple named layers.

Shows how OffsetComposer combines a base position with multiple
offset layers (e.g. tracking + gesture) and clamps to servo limits.

Run:
    python -m examples.movement.03_math_offset_composition
"""

from raspibot.movement.motion_offset import MotionOffset, OffsetComposer

PAN_LIMITS = (0.0, 180.0)
TILT_LIMITS = (0.0, 150.0)


def main() -> None:
    """Walk through offset composition scenarios."""
    print("Offset Composition")
    print("==================")

    composer = OffsetComposer(pan_limits=PAN_LIMITS, tilt_limits=TILT_LIMITS)

    # Start at center
    composer.set_base(90.0, 90.0)
    pan, tilt = composer.resolve()
    print(f"\n1. Base at center: pan={pan:.1f}, tilt={tilt:.1f}")
    print(f"   Active layers: {composer.active_layers}")

    # Add a tracking offset (person slightly to the right)
    composer.set_offset("tracking", MotionOffset(pan=15.0, tilt=-5.0))
    pan, tilt = composer.resolve()
    print(f"\n2. + tracking offset (pan=+15, tilt=-5): pan={pan:.1f}, tilt={tilt:.1f}")
    print(f"   Active layers: {composer.active_layers}")

    # Add a gesture offset on top (nod down)
    composer.set_offset("gesture", MotionOffset(tilt=-8.0))
    pan, tilt = composer.resolve()
    print(f"\n3. + gesture offset (tilt=-8): pan={pan:.1f}, tilt={tilt:.1f}")
    print(f"   Active layers: {composer.active_layers}")

    # Clear the gesture (nod complete)
    composer.clear_offset("gesture")
    pan, tilt = composer.resolve()
    print(f"\n4. Gesture cleared: pan={pan:.1f}, tilt={tilt:.1f}")
    print(f"   Active layers: {composer.active_layers}")

    # Show clamping: push base near edge, add large offset
    composer.set_base(170.0, 10.0)
    composer.set_offset("tracking", MotionOffset(pan=20.0, tilt=-15.0))
    pan, tilt = composer.resolve()
    print("\n5. Clamping demo (base=170,10 + tracking=+20,-15):")
    print(f"   pan={pan:.1f} (clamped to {PAN_LIMITS[1]:.0f}), "
          f"tilt={tilt:.1f} (clamped to {TILT_LIMITS[0]:.0f})")

    # MotionOffset addition
    a = MotionOffset(pan=5.0, tilt=-3.0)
    b = MotionOffset(pan=-2.0, tilt=7.0)
    c = a + b
    print(f"\n6. Offset arithmetic: {a} + {b} = {c}")


if __name__ == "__main__":
    main()
