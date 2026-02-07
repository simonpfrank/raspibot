"""Demonstrate interpolation curves for smooth servo movement.

Shows the three available interpolation methods and how they map
a progress fraction (0..1) to a position fraction (0..1).

Run:
    python -m examples.movement.01_math_basic_interpolation
"""

from raspibot.movement.interpolation import InterpolationMethod, interpolate

STEPS = 10


def show_curve(method: InterpolationMethod) -> None:
    """Print interpolation values for a given method."""
    print(f"\n{method.value}:")
    for i in range(STEPS + 1):
        t = i / STEPS
        value = interpolate(t, method)
        bar = "#" * int(value * 40)
        print(f"  t={t:.1f}  value={value:.3f}  {bar}")


def main() -> None:
    """Show all three interpolation curves side by side."""
    print("Interpolation Methods")
    print("=====================")
    print("Each curve maps progress (t) to position (value).")
    print("Linear = constant speed, minjerk = smooth start/stop,")
    print("ease_in_out = slow edges with fast middle.")

    for method in InterpolationMethod:
        show_curve(method)

    # Show how to use for a servo move from 45 to 135 degrees
    start_angle = 45.0
    end_angle = 135.0
    print(f"\nExample: servo move {start_angle}° → {end_angle}° using minjerk")
    for i in range(STEPS + 1):
        t = i / STEPS
        fraction = interpolate(t, InterpolationMethod.MINJERK)
        angle = start_angle + (end_angle - start_angle) * fraction
        print(f"  t={t:.1f}  angle={angle:.1f}°")


if __name__ == "__main__":
    main()
