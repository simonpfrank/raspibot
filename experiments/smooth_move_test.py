#!/usr/bin/env python3
"""Test smooth movement to see if it reduces jitter."""
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


def smooth_move(start_angle: float, end_angle: float, duration: float = 1.0) -> None:
    """Move smoothly from start to end angle over duration seconds (linear)."""
    steps = 50
    step_delay = duration / steps
    angle_step = (end_angle - start_angle) / steps

    for i in range(steps + 1):
        angle = start_angle + (angle_step * i)
        set_pwm(angle_to_ticks(angle))
        time.sleep(step_delay)


def ease_in_out(t: float) -> float:
    """Ease-in/ease-out curve (smooth acceleration/deceleration)."""
    # Attempt a smoother curve: slow start, fast middle, slow end
    if t < 0.5:
        return 2 * t * t
    else:
        return 1 - ((-2 * t + 2) ** 2) / 2


def smooth_move_eased(start_angle: float, end_angle: float, duration: float = 1.0) -> None:
    """Move with ease-in/ease-out curve - much smoother looking."""
    steps = 100
    step_delay = duration / steps
    angle_range = end_angle - start_angle

    for i in range(steps + 1):
        t = i / steps  # 0.0 to 1.0
        eased_t = ease_in_out(t)
        angle = start_angle + (angle_range * eased_t)
        set_pwm(angle_to_ticks(angle))
        time.sleep(step_delay)


def main() -> None:
    """Compare instant vs smooth movement to problem angles."""
    print("=" * 50)
    print("SMOOTH MOVEMENT TEST")
    print("Comparing instant jump vs gradual move")
    print("=" * 50)
    print()

    # Use prescale 131 (our best value)
    init_prescale(131)
    print("Using prescale 131")
    print()

    try:
        # Test 1: Instant jump to problem angle
        print("--- TEST 1: INSTANT JUMP ---")
        print("Going to 45 degrees...")
        set_pwm(angle_to_ticks(45))
        time.sleep(2)

        print("INSTANT JUMP to 180 degrees (watch for jitter)")
        set_pwm(angle_to_ticks(180))
        time.sleep(4)

        # Test 2: Smooth move to problem angle
        print()
        print("--- TEST 2: SMOOTH MOVE (1 second) ---")
        print("Going to 45 degrees...")
        set_pwm(angle_to_ticks(45))
        time.sleep(2)

        print("SMOOTH MOVE to 180 degrees over 1 second...")
        smooth_move(45, 180, duration=1.0)
        print("Holding at 180... (watch for jitter)")
        time.sleep(4)

        # Test 3: Very slow move
        print()
        print("--- TEST 3: VERY SLOW MOVE (3 seconds) ---")
        print("Going to 45 degrees...")
        set_pwm(angle_to_ticks(45))
        time.sleep(2)

        print("VERY SLOW MOVE to 180 degrees over 3 seconds...")
        smooth_move(45, 180, duration=3.0)
        print("Holding at 180... (watch for jitter)")
        time.sleep(4)

        # Test 4: Ease-in/ease-out movement
        print()
        print("--- TEST 4: EASE-IN/EASE-OUT (2 seconds) ---")
        print("Going to 45 degrees...")
        set_pwm(angle_to_ticks(45))
        time.sleep(2)

        print("EASED MOVE to 180 degrees (slow-fast-slow)...")
        smooth_move_eased(45, 180, duration=2.0)
        print("Holding at 180...")
        time.sleep(3)

        # Test 5: Compare linear vs eased side by side
        print()
        print("--- TEST 5: COMPARISON ---")
        print("LINEAR move 45 -> 135...")
        set_pwm(angle_to_ticks(45))
        time.sleep(1)
        smooth_move(45, 135, duration=1.5)
        time.sleep(2)

        print("EASED move 135 -> 45...")
        smooth_move_eased(135, 45, duration=1.5)
        time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopped")

    finally:
        set_pwm(angle_to_ticks(90))
        print()
        print("Done - back to 90 degrees")
        bus.close()


if __name__ == "__main__":
    main()
