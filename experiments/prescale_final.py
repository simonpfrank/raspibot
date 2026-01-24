#!/usr/bin/env python3
"""Final validation of prescale 131 across all angles and directions."""
import smbus2
import time

MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06
PCA_ADDR = 0x40
CHANNEL = 14
OPTIMAL_PRESCALE = 131

bus = smbus2.SMBus(1)


def init_prescale(ps: int) -> None:
    """Initialize PCA9685 with given prescale value."""
    old_mode = bus.read_byte_data(PCA_ADDR, MODE1)
    bus.write_byte_data(PCA_ADDR, MODE1, (old_mode & 0x7F) | 0x10)
    bus.write_byte_data(PCA_ADDR, PRESCALE, ps)
    bus.write_byte_data(PCA_ADDR, MODE1, old_mode)
    time.sleep(0.005)
    bus.write_byte_data(PCA_ADDR, MODE1, old_mode | 0x80)


def set_pwm(off: int) -> None:
    """Set PWM off value for servo channel."""
    base = LED0_ON_L + 4 * CHANNEL
    bus.write_byte_data(PCA_ADDR, base, 0)
    bus.write_byte_data(PCA_ADDR, base + 1, 0)
    bus.write_byte_data(PCA_ADDR, base + 2, off & 0xFF)
    bus.write_byte_data(PCA_ADDR, base + 3, off >> 8)


def angle_to_ticks(angle: float) -> int:
    """Convert angle to PWM ticks."""
    pulse_ms = 0.5 + 2.0 * angle / 180.0
    return int(pulse_ms / 20.0 * 4096)


def main() -> None:
    """Final validation with prescale 131."""
    freq = 25000000 / (4096 * (OPTIMAL_PRESCALE + 1))

    print("=" * 50)
    print(f"FINAL VALIDATION - Prescale {OPTIMAL_PRESCALE} ({freq:.1f}Hz)")
    print("=" * 50)
    print()

    init_prescale(OPTIMAL_PRESCALE)

    # Full angle range including problem zone
    test_angles = [45, 90, 95, 100, 104, 108, 112, 115, 135]

    try:
        # Ascending
        print("--- ASCENDING ---")
        for angle in test_angles:
            print(f">>> {angle} degrees <<<")
            set_pwm(angle_to_ticks(angle))
            time.sleep(3)

        print()

        # Descending
        print("--- DESCENDING ---")
        for angle in reversed(test_angles):
            print(f">>> {angle} degrees <<<")
            set_pwm(angle_to_ticks(angle))
            time.sleep(3)

        print()

        # Random jumps to problem zone
        print("--- RANDOM JUMPS ---")
        jumps = [(45, 104), (135, 100), (90, 108), (115, 95)]
        for start, end in jumps:
            print(f">>> {start} -> {end} degrees <<<")
            set_pwm(angle_to_ticks(start))
            time.sleep(1.5)
            set_pwm(angle_to_ticks(end))
            time.sleep(3)

    except KeyboardInterrupt:
        print("\nStopped")

    finally:
        set_pwm(angle_to_ticks(90))
        print()
        print("=" * 50)
        print("DONE")
        print(f"If no jitter: Update config with prescale={OPTIMAL_PRESCALE}")
        print("=" * 50)
        bus.close()


if __name__ == "__main__":
    main()
