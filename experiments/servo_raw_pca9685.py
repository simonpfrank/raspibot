#!/usr/bin/env python3
"""Direct PCA9685 control via SMBus - bypasses Adafruit library.

This script provides raw I2C access to the PCA9685 for debugging servo jitter.
It includes multiple experiments to identify the root cause of jitter in the
98-110 degree range.

Usage:
    python experiments/servo_raw_pca9685.py [experiment_number]

Experiments:
    1 - Basic angle sweep (85-115 degrees)
    2 - Frequency variation (48Hz, 50Hz, 52Hz, 55Hz, 60Hz)
    3 - Pulse width range variation
    4 - Prescale calibration test
    5 - Fine-grained angle sweep (0.5 degree steps)
    6 - Channel switching test
"""
import sys
import time

try:
    import smbus2
except ImportError:
    print("ERROR: smbus2 not installed. Run: pip install smbus2")
    sys.exit(1)


# PCA9685 registers
MODE1 = 0x00
MODE2 = 0x01
PRESCALE = 0xFE
LED0_ON_L = 0x06

# Default configuration
PCA_ADDR = 0x40
DEFAULT_CHANNEL = 14  # Pan servo channel (0x0E)
OSCILLATOR_FREQ = 25_000_000  # 25MHz reference


def init_pca9685(bus: smbus2.SMBus, freq: int = 50, prescale_override: int | None = None) -> int:
    """Initialize PCA9685 with given frequency.

    Args:
        bus: SMBus instance
        freq: PWM frequency in Hz (default 50Hz for servos)
        prescale_override: Manual prescale value (bypasses calculation)

    Returns:
        Actual prescale value used
    """
    if prescale_override is not None:
        prescale = prescale_override
        actual_freq = OSCILLATOR_FREQ / (4096 * (prescale + 1))
        print(f"Using manual prescale: {prescale} (actual freq: {actual_freq:.2f}Hz)")
    else:
        # Standard formula: prescale = round(osc_freq / (4096 * pwm_freq)) - 1
        prescale = int(round(OSCILLATOR_FREQ / (4096.0 * freq)) - 1)
        print(f"Calculated prescale for {freq}Hz: {prescale}")

    # Enter sleep mode to set prescale
    old_mode = bus.read_byte_data(PCA_ADDR, MODE1)
    bus.write_byte_data(PCA_ADDR, MODE1, (old_mode & 0x7F) | 0x10)  # Sleep mode
    bus.write_byte_data(PCA_ADDR, PRESCALE, prescale)
    bus.write_byte_data(PCA_ADDR, MODE1, old_mode)
    time.sleep(0.005)
    bus.write_byte_data(PCA_ADDR, MODE1, old_mode | 0x80)  # Restart

    # Read back prescale to confirm
    actual_prescale = bus.read_byte_data(PCA_ADDR, PRESCALE)
    print(f"Prescale read back: {actual_prescale}")

    return prescale


def set_pwm(bus: smbus2.SMBus, channel: int, on: int, off: int) -> None:
    """Set PWM on/off times (0-4095).

    Args:
        bus: SMBus instance
        channel: PCA9685 channel (0-15)
        on: PWM on time in ticks
        off: PWM off time in ticks
    """
    base = LED0_ON_L + 4 * channel
    bus.write_byte_data(PCA_ADDR, base, on & 0xFF)
    bus.write_byte_data(PCA_ADDR, base + 1, on >> 8)
    bus.write_byte_data(PCA_ADDR, base + 2, off & 0xFF)
    bus.write_byte_data(PCA_ADDR, base + 3, off >> 8)


def angle_to_pulse(
    angle: float,
    min_pulse_ms: float = 0.5,
    max_pulse_ms: float = 2.5,
    period_ms: float = 20.0
) -> int:
    """Convert angle (0-180) to PCA9685 off value.

    Args:
        angle: Servo angle in degrees
        min_pulse_ms: Pulse width at 0 degrees
        max_pulse_ms: Pulse width at 180 degrees
        period_ms: PWM period in milliseconds

    Returns:
        PCA9685 off value (0-4095)
    """
    pulse_ms = min_pulse_ms + (max_pulse_ms - min_pulse_ms) * (angle / 180.0)
    ticks = int(pulse_ms / period_ms * 4096)
    return ticks


def disable_servo(bus: smbus2.SMBus, channel: int) -> None:
    """Disable servo output (stop PWM signal)."""
    set_pwm(bus, channel, 0, 0)


def experiment_1_basic_sweep(bus: smbus2.SMBus, channel: int = DEFAULT_CHANNEL) -> None:
    """Experiment 1: Basic angle sweep through problem zone.

    Tests angles 85-115 degrees with 1-degree steps.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 1: Basic Angle Sweep (85-115 degrees)")
    print("=" * 60)
    print("Press Ctrl+C to stop")

    init_pca9685(bus, freq=50)

    try:
        for angle in range(85, 116):
            off_val = angle_to_pulse(angle)
            pulse_ms = off_val / 4096 * 20
            print(f"Angle {angle:3d}deg -> ticks={off_val:4d} ({pulse_ms:.3f}ms)")
            set_pwm(bus, channel, 0, off_val)
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        set_pwm(bus, channel, 0, angle_to_pulse(90))
        print("Returned to 90 degrees")


def experiment_2_frequency_variation(bus: smbus2.SMBus, channel: int = DEFAULT_CHANNEL) -> None:
    """Experiment 2: Test different PWM frequencies.

    Tests 48Hz, 50Hz, 52Hz, 55Hz, 60Hz at problem angles.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 2: PWM Frequency Variation")
    print("=" * 60)

    frequencies = [48, 50, 52, 55, 60]
    test_angles = [90, 100, 105, 110]

    for freq in frequencies:
        print(f"\n--- Testing {freq}Hz ---")
        init_pca9685(bus, freq=freq)
        period_ms = 1000.0 / freq

        for angle in test_angles:
            off_val = angle_to_pulse(angle, period_ms=period_ms)
            pulse_ms = off_val / 4096 * period_ms
            print(f"  {angle}deg: ticks={off_val} ({pulse_ms:.3f}ms)")
            set_pwm(bus, channel, 0, off_val)

            response = input("  Jitter? (y/n/s=skip freq): ").strip().lower()
            if response == 's':
                break

    # Return to 50Hz, 90 degrees
    init_pca9685(bus, freq=50)
    set_pwm(bus, channel, 0, angle_to_pulse(90))
    print("\nReturned to 50Hz, 90 degrees")


def experiment_3_pulse_range(bus: smbus2.SMBus, channel: int = DEFAULT_CHANNEL) -> None:
    """Experiment 3: Test different pulse width ranges.

    Tests various min/max pulse width combinations.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: Pulse Width Range Variation")
    print("=" * 60)

    init_pca9685(bus, freq=50)

    # Different pulse ranges to test
    pulse_ranges = [
        ("SG90 Datasheet", 1.0, 2.0),
        ("Extended", 0.5, 2.5),
        ("Your Calibrated", 0.4, 2.52),
        ("Narrower", 0.6, 2.4),
        ("Wide", 0.3, 2.7),
    ]

    test_angle = 105  # Problem angle

    for name, min_ms, max_ms in pulse_ranges:
        print(f"\n--- {name}: {min_ms}ms - {max_ms}ms ---")

        for angle in [90, 100, 105, 110]:
            off_val = angle_to_pulse(angle, min_pulse_ms=min_ms, max_pulse_ms=max_ms)
            pulse_ms = off_val / 4096 * 20
            print(f"  {angle}deg: ticks={off_val} ({pulse_ms:.3f}ms)")
            set_pwm(bus, channel, 0, off_val)

            response = input("  Jitter? (y/n/s=skip range): ").strip().lower()
            if response == 's':
                break

    set_pwm(bus, channel, 0, angle_to_pulse(90))
    print("\nReturned to 90 degrees (default pulse range)")


def experiment_4_prescale_calibration(bus: smbus2.SMBus, channel: int = DEFAULT_CHANNEL) -> None:
    """Experiment 4: Test different prescale values.

    The PCA9685 oscillator can drift 4-8%. Test prescale values to compensate.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Prescale Calibration")
    print("=" * 60)
    print("Testing prescale values to find optimal setting")
    print("Standard prescale for 50Hz with 25MHz osc: 121")
    print("If osc is 26MHz: prescale should be ~126")
    print("If osc is 27MHz: prescale should be ~130")

    prescale_values = [118, 121, 124, 127, 130, 133]
    test_angle = 105  # Problem angle

    for prescale in prescale_values:
        expected_freq = OSCILLATOR_FREQ / (4096 * (prescale + 1))
        print(f"\n--- Prescale {prescale} (expected {expected_freq:.1f}Hz) ---")
        init_pca9685(bus, prescale_override=prescale)

        # Calculate period for this prescale
        period_ms = 1000.0 / expected_freq

        for angle in [90, 100, 105, 110]:
            off_val = angle_to_pulse(angle, period_ms=period_ms)
            pulse_ms = off_val / 4096 * period_ms
            print(f"  {angle}deg: ticks={off_val} ({pulse_ms:.3f}ms)")
            set_pwm(bus, channel, 0, off_val)

            response = input("  Jitter? (y/n/s=skip prescale): ").strip().lower()
            if response == 's':
                break

    # Return to default
    init_pca9685(bus, freq=50)
    set_pwm(bus, channel, 0, angle_to_pulse(90))
    print("\nReturned to default prescale, 90 degrees")


def experiment_5_fine_sweep(bus: smbus2.SMBus, channel: int = DEFAULT_CHANNEL) -> None:
    """Experiment 5: Fine-grained sweep with 0.5 degree steps.

    Find exact angles where jitter starts/stops.
    Non-interactive version - holds each angle for 2 seconds.
    Watch and note which angles show jitter.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 5: Fine-Grained Angle Sweep (0.5 degree steps)")
    print("=" * 60)
    print("Sweeping 90-115 degrees in 0.5 degree increments")
    print("Each angle held for 2 seconds - WATCH FOR JITTER")
    print("Press Ctrl+C to stop")
    print()

    init_pca9685(bus, freq=50)

    try:
        # 90.0 to 115.0 in 0.5 degree steps
        for angle_x10 in range(900, 1155, 5):
            angle = angle_x10 / 10.0
            off_val = angle_to_pulse(angle)
            pulse_ms = off_val / 4096 * 20

            set_pwm(bus, channel, 0, off_val)
            print(f"Angle {angle:5.1f}deg: ticks={off_val:4d} ({pulse_ms:.3f}ms)")
            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\nStopped by user")

    finally:
        set_pwm(bus, channel, 0, angle_to_pulse(90))
        print("\nReturned to 90 degrees")


def experiment_6_channel_test(bus: smbus2.SMBus) -> None:
    """Experiment 6: Test different PCA9685 channels.

    Tests if jitter is specific to channel 14.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 6: Channel Switching Test")
    print("=" * 60)
    print("This requires physically moving the servo to a different channel")

    channels_to_test = [0, 1, 2, 14, 15]

    init_pca9685(bus, freq=50)

    for channel in channels_to_test:
        print(f"\n--- Testing Channel {channel} ---")
        print(f"Connect servo signal wire to channel {channel} on PCA9685")
        response = input("Ready? (y/s=skip/q=quit): ").strip().lower()

        if response == 'q':
            break
        if response == 's':
            continue

        for angle in [90, 100, 105, 110]:
            off_val = angle_to_pulse(angle)
            set_pwm(bus, channel, 0, off_val)
            print(f"  {angle}deg")
            jitter = input("  Jitter? (y/n): ").strip().lower()

        # Disable this channel before moving to next
        disable_servo(bus, channel)

    print("\nTest complete")


def experiment_7_continuous_hold(bus: smbus2.SMBus, channel: int = DEFAULT_CHANNEL) -> None:
    """Experiment 7: Hold at problem angle continuously.

    Useful for measuring PWM signal with oscilloscope or logic analyzer.
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT 7: Continuous Hold at Problem Angle")
    print("=" * 60)

    init_pca9685(bus, freq=50)

    try:
        while True:
            angle_str = input("Enter angle (or 'q' to quit): ").strip()
            if angle_str.lower() == 'q':
                break

            try:
                angle = float(angle_str)
                if not 0 <= angle <= 180:
                    print("Angle must be 0-180")
                    continue

                off_val = angle_to_pulse(angle)
                pulse_ms = off_val / 4096 * 20
                print(f"Holding at {angle}deg: ticks={off_val} ({pulse_ms:.3f}ms)")
                print("Press Ctrl+C or enter new angle to change")
                set_pwm(bus, channel, 0, off_val)

            except ValueError:
                print("Invalid angle")

    except KeyboardInterrupt:
        pass

    finally:
        set_pwm(bus, channel, 0, angle_to_pulse(90))
        print("\nReturned to 90 degrees")


def show_menu() -> None:
    """Display experiment menu."""
    print("\n" + "=" * 60)
    print("SERVO JITTER INVESTIGATION - Direct PCA9685 Control")
    print("=" * 60)
    print("\nExperiments:")
    print("  1 - Basic angle sweep (85-115 degrees)")
    print("  2 - Frequency variation (48-60Hz)")
    print("  3 - Pulse width range variation")
    print("  4 - Prescale calibration (oscillator drift)")
    print("  5 - Fine-grained sweep (0.5 degree steps)")
    print("  6 - Channel switching test")
    print("  7 - Continuous hold (for scope measurement)")
    print("  q - Quit")
    print()


def main() -> None:
    """Main entry point."""
    bus = smbus2.SMBus(1)

    # Check for command line argument
    if len(sys.argv) > 1:
        exp_num = sys.argv[1]
    else:
        exp_num = None

    try:
        if exp_num:
            # Run specific experiment
            experiments = {
                '1': lambda: experiment_1_basic_sweep(bus),
                '2': lambda: experiment_2_frequency_variation(bus),
                '3': lambda: experiment_3_pulse_range(bus),
                '4': lambda: experiment_4_prescale_calibration(bus),
                '5': lambda: experiment_5_fine_sweep(bus),
                '6': lambda: experiment_6_channel_test(bus),
                '7': lambda: experiment_7_continuous_hold(bus),
            }
            if exp_num in experiments:
                experiments[exp_num]()
            else:
                print(f"Unknown experiment: {exp_num}")
                show_menu()
        else:
            # Interactive menu
            while True:
                show_menu()
                choice = input("Select experiment (1-7, q): ").strip().lower()

                if choice == 'q':
                    break
                elif choice == '1':
                    experiment_1_basic_sweep(bus)
                elif choice == '2':
                    experiment_2_frequency_variation(bus)
                elif choice == '3':
                    experiment_3_pulse_range(bus)
                elif choice == '4':
                    experiment_4_prescale_calibration(bus)
                elif choice == '5':
                    experiment_5_fine_sweep(bus)
                elif choice == '6':
                    experiment_6_channel_test(bus)
                elif choice == '7':
                    experiment_7_continuous_hold(bus)
                else:
                    print("Invalid choice")

    finally:
        # Ensure servo is disabled on exit
        disable_servo(bus, DEFAULT_CHANNEL)
        bus.close()
        print("\nPCA9685 connection closed")


if __name__ == "__main__":
    main()
