#!/usr/bin/env python3
"""Test different prescale values to find optimal setting for jitter reduction."""
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
    """Run prescale test at 104 degrees (problem angle)."""
    # Test prescale values at 104 degrees
    # 121 = standard 50Hz, higher = slower freq, lower = faster freq
    prescales = [115, 118, 121, 124, 127, 130]
    angle = 104
    ticks = int((0.5 + 2.0 * angle / 180.0) / 20.0 * 4096)

    print("PRESCALE TEST at 104 degrees")
    print("Standard=121, Lower=faster PWM, Higher=slower PWM")
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
        init_prescale(121)
        set_pwm(307)  # 90 degrees
        print("Done - back to 90 deg")
        bus.close()


if __name__ == "__main__":
    main()
