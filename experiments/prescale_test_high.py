#!/usr/bin/env python3
"""Test higher prescale values to find optimal setting."""
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


def main() -> None:
    """Run prescale test with higher values at 104 degrees."""
    # Test higher prescale values - oscillator seems to be running fast
    # 121 = 50Hz with 25MHz osc
    # Higher prescale = slower PWM frequency
    prescales = [127, 130, 133, 136, 140]
    angle = 104
    ticks = int((0.5 + 2.0 * angle / 180.0) / 20.0 * 4096)

    print("PRESCALE TEST (HIGH VALUES) at 104 degrees")
    print("Testing if oscillator is running fast (>25MHz)")
    print()

    try:
        for ps in prescales:
            freq = 25000000 / (4096 * (ps + 1))
            print(f">>> PRESCALE {ps} ({freq:.1f}Hz) <<<")
            init_prescale(ps)
            set_pwm(ticks)
            time.sleep(4)

    except KeyboardInterrupt:
        print("\nStopped")

    finally:
        # Stay at best prescale found (130) for now
        init_prescale(130)
        set_pwm(307)  # 90 degrees
        print("Done - back to 90 deg (prescale 130)")
        bus.close()


if __name__ == "__main__":
    main()
