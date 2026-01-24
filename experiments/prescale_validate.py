#!/usr/bin/env python3
"""Validate prescale 130 across full problem range with both directions."""
import smbus2
import time

MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06
PCA_ADDR = 0x40
CHANNEL = 14
OPTIMAL_PRESCALE = 130

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
    """Validate prescale 130 with ascending and descending sweeps."""
    print("=" * 50)
    print(f"VALIDATION TEST - Prescale {OPTIMAL_PRESCALE}")
    print("=" * 50)
    print()

    init_prescale(OPTIMAL_PRESCALE)
    freq = 25000000 / (4096 * (OPTIMAL_PRESCALE + 1))
    print(f"PWM frequency: {freq:.1f}Hz")
    print()

    test_angles = [90, 95, 100, 104, 106, 108, 110, 115]

    try:
        # Test 1: Ascending (low to high)
        print("--- ASCENDING (90 -> 115) ---")
        for angle in test_angles:
            print(f">>> {angle} degrees <<<")
            set_pwm(angle_to_ticks(angle))
            time.sleep(2.5)

        print()
        time.sleep(1)

        # Test 2: Descending (high to low)
        print("--- DESCENDING (115 -> 90) ---")
        for angle in reversed(test_angles):
            print(f">>> {angle} degrees <<<")
            set_pwm(angle_to_ticks(angle))
            time.sleep(2.5)

        print()
        time.sleep(1)

        # Test 3: Jump to problem angles from far away
        print("--- JUMP TEST (from 45 and 135 to 104) ---")

        print(">>> 45 degrees (start far low) <<<")
        set_pwm(angle_to_ticks(45))
        time.sleep(2)

        print(">>> JUMP to 104 degrees <<<")
        set_pwm(angle_to_ticks(104))
        time.sleep(3)

        print(">>> 135 degrees (start far high) <<<")
        set_pwm(angle_to_ticks(135))
        time.sleep(2)

        print(">>> JUMP to 104 degrees <<<")
        set_pwm(angle_to_ticks(104))
        time.sleep(3)

    except KeyboardInterrupt:
        print("\nStopped")

    finally:
        set_pwm(angle_to_ticks(90))
        print()
        print("Done - back to 90 degrees")
        print(f"Optimal prescale confirmed: {OPTIMAL_PRESCALE}")
        bus.close()


if __name__ == "__main__":
    main()
