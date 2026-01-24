#!/usr/bin/env python3
"""Fine-tune prescale around 130 with longer hold times."""
import smbus2
import time

MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06
PCA_ADDR = 0x40
CHANNEL = 14

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
    """Fine-tune prescale with longer holds at problem angle."""
    print("=" * 50)
    print("PRESCALE FINE-TUNE TEST")
    print("Testing 128-132 at 104 degrees with 5s holds")
    print("=" * 50)
    print()

    # Fine-tune around 130
    prescales = [128, 129, 130, 131, 132]
    problem_angle = 104

    try:
        for ps in prescales:
            freq = 25000000 / (4096 * (ps + 1))
            print(f">>> PRESCALE {ps} ({freq:.1f}Hz) <<<")
            init_prescale(ps)

            # Start from 90, then go to problem angle
            print("    Starting at 90...")
            set_pwm(angle_to_ticks(90))
            time.sleep(1.5)

            print(f"    Moving to {problem_angle}... (hold 5s)")
            set_pwm(angle_to_ticks(problem_angle))
            time.sleep(5)

            print()

    except KeyboardInterrupt:
        print("\nStopped")

    finally:
        init_prescale(130)
        set_pwm(angle_to_ticks(90))
        print("Done - back to 90 degrees")
        bus.close()


if __name__ == "__main__":
    main()
