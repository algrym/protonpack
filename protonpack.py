#!/usr/bin/env python3

import gc
import os
import random
import sys
import time

import supervisor
from watchdog import WatchDogMode

import adafruit_fancyled.adafruit_fancyled as fancyled
import board
import digitalio
import microcontroller
import neopixel
from adafruit_debouncer import Debouncer
from code import __version__  # Import __version__ from code.py


# Function to get a pin from board module
def get_pin(pin_name):
    try:
        return getattr(board, pin_name)
    except AttributeError:
        raise ValueError(f"Pin {pin_name} not found on board")


# Load constants
def load_constants():
    constants = {}

    # Convert environment variable strings to integers where appropriate
    constants['stat_clock_time_ms'] = int(os.getenv('stat_clock_time_ms', "5000"))
    constants['sleep_time_secs'] = float(os.getenv('sleep_time_secs', "0.01"))
    constants['watch_dog_timeout_secs'] = int(os.getenv('watch_dog_timeout_secs', "7"))
    constants['neopixel_ring_pin'] = get_pin(os.getenv('neopixel_ring_pin', "GP28"))
    constants['neopixel_ring_size'] = int(os.getenv('neopixel_ring_size', "60"))
    constants['neopixel_ring_cursor_size'] = int(os.getenv('neopixel_ring_cursor_size', "3"))
    constants['neopixel_ring_brightness'] = float(os.getenv('neopixel_ring_brightness', "0.05"))
    constants['neopixel_stick_pin'] = get_pin(os.getenv('neopixel_stick_pin', "GP27"))
    constants['neopixel_stick_size'] = int(os.getenv('neopixel_stick_size', "20"))
    constants['neopixel_stick_brightness'] = float(os.getenv('neopixel_stick_brightness', "0.1"))
    constants['audio_out_pin'] = get_pin(os.getenv('audio_out_pin', "GP21"))
    constants['hero_switch_pin'] = get_pin(os.getenv('hero_switch_pin', "GP9"))
    constants['rotary_encoder_button_pin'] = get_pin(os.getenv('rotary_encoder_button_pin', "GP10"))
    constants['rotary_encoder_dt_pin'] = get_pin(os.getenv('rotary_encoder_dt_pin', "GP11"))
    constants['rotary_encoder_clock_pin'] = get_pin(os.getenv('rotary_encoder_clock_pin', "GP12"))

    print(f" - Loaded {len(constants)} constants from settings.toml")
    for i in constants:
        print(f"    - {i} = {constants[i]}")
    return constants


def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def print_cpu_id():
    # Convert UID bytearray to a hex string and print it
    uid_hex = ':'.join(['{:02x}'.format(x) for x in microcontroller.cpu.uid])
    print(f" - cpu uid: {uid_hex}")


def pretty_print_bytes(size):
    # Define unit thresholds and labels
    units = ["bytes", "KB", "MB", "GB"]
    step = 1024

    # Find the largest unit to express the size in full units
    for unit in units:
        if size < step:
            return f"{size:.2f} {unit}"
        size /= step

    # If size is large, it will be formatted in GB from the loop
    return f"{size:.2f} GB"


def setup_watch_dog(timeout):
    watch_dog = microcontroller.watchdog
    if timeout > 8:  # Hardware maximum of 8 secs
        timeout = 8
    watch_dog.timeout = timeout
    watch_dog.mode = WatchDogMode.RESET
    print(f"- Watch dog released.  Feed every {timeout} seconds or else.")
    watch_dog.feed()  # make sure the dog is fed before turning him loose
    return watch_dog


def main_loop():
    # Print startup information
    print(f"-=< protonpack v{__version__} - https://github.com/algrym/protonpack/ >=-")
    print(f" - uname: {os.uname()}")
    print_cpu_id()
    print(f" -- freq: {microcontroller.cpu.frequency / 1e6} MHz")
    print(f" -- reset reason: {microcontroller.cpu.reset_reason}")
    print(f" -- nvm: {pretty_print_bytes(len(microcontroller.nvm))}")
    print(f" - python v{sys.version}")
    gc.collect()
    starting_memory_free = gc.mem_free()
    print(f" - Free memory: {pretty_print_bytes(starting_memory_free)}")

    # Read in constants
    constants = load_constants()

    watch_dog = setup_watch_dog(constants['watch_dog_timeout_secs'])

    # Color constants
    brightness_levels = (0.25, 0.3, 0.15)
    RED = fancyled.gamma_adjust(fancyled.CRGB(255, 0, 0), brightness=brightness_levels).pack()
    ORANGE = fancyled.gamma_adjust(fancyled.CRGB(255, 165, 0), brightness=brightness_levels).pack()
    YELLOW = fancyled.gamma_adjust(fancyled.CRGB(255, 255, 0), brightness=brightness_levels).pack()
    GREEN = fancyled.gamma_adjust(fancyled.CRGB(0, 255, 0), brightness=brightness_levels).pack()
    BLUE = fancyled.gamma_adjust(fancyled.CRGB(0, 0, 255), brightness=brightness_levels).pack()
    PURPLE = fancyled.gamma_adjust(fancyled.CRGB(128, 0, 128), brightness=brightness_levels).pack()
    WHITE = fancyled.gamma_adjust(fancyled.CRGB(255, 255, 255), brightness=brightness_levels).pack()
    OFF = (0, 0, 0)

    # Initialize Neopixels
    print(f" - neopixel v{neopixel.__version__}")
    print(f"   - NeoPixel stick size {constants['neopixel_stick_size']} on {constants['neopixel_stick_pin']}")
    stick_pixels = neopixel.NeoPixel(constants['neopixel_stick_pin'],
                                     constants['neopixel_stick_size'],
                                     brightness=constants['neopixel_stick_brightness'],
                                     pixel_order=neopixel.GRBW)  # TODO: this should come from settings.toml
    stick_pixels.fill(OFF)

    print(f"   - NeoPixel ring size {constants['neopixel_ring_size']} on {constants['neopixel_ring_pin']}")
    ring_pixels = neopixel.NeoPixel(constants['neopixel_ring_pin'],
                                    constants['neopixel_ring_size'],
                                    brightness=constants['neopixel_ring_brightness'])
    ring_pixels.fill(OFF)

    # State definitions
    class State:
        POWER_ON = 1
        STANDBY = 2
        STARTUP = 3
        LOOP_IDLE = 4

    # Initialize switch input
    print(f"   - Input select on {constants['hero_switch_pin']}")
    hero_switch_pin_input = digitalio.DigitalInOut(constants['hero_switch_pin'])
    hero_switch_pin_input.direction = digitalio.Direction.INPUT
    # expecting switch wired from its pin to GND with 4.7kΩ pull up resistor
    hero_switch_pin_input.pull = digitalio.Pull.UP
    hero_switch = Debouncer(hero_switch_pin_input)

    # Initialize cyclotron counters
    cyclotron_speed: int = 30  # TODO: temporary value for cyclotron_speed
    next_cyclotron_clock: int = 0
    cyclotron_cursor_width: int = constants['neopixel_ring_cursor_size']
    cyclotron_cursor_on: int = 0
    cyclotron_cursor_off: int = 0

    # Initialize power meter counters
    power_meter_speed: int = 10  # TODO: temporary value for power_meter_speed
    next_power_meter_clock: int = 0
    power_meter_max: int = 1
    power_meter_max_previous: int = 0
    power_meter_cursor: int = 1

    # Initialize her switch state
    hero_switch.update()
    if hero_switch.value:
        current_state = State.LOOP_IDLE
    else:
        current_state = State.STANDBY

    # Initialize timers and counters
    start_clock: int = supervisor.ticks_ms()
    next_stat_clock: int = supervisor.ticks_ms() + constants['stat_clock_time_ms']
    loop_count: int = 0

    next_watch_dog_clock: int = 0

    # main driver loop
    print("- Starting main driver loop")
    gc.collect()  # garbage collect right before starting the while loop
    while True:
        clock = supervisor.ticks_ms()
        loop_count += 1

        # process the stats output
        if clock > next_stat_clock:
            elapsed_time = (clock - start_clock) / 1000  # Convert ms to seconds
            loops_per_second = loop_count / elapsed_time if elapsed_time > 0 else 0
            print(
                f"{format_time(elapsed_time)} loop {loop_count:,} at {loops_per_second:.2f} loops/s free={pretty_print_bytes(gc.mem_free())}")
            next_stat_clock = clock + constants['stat_clock_time_ms']

        # Periodically feed the watch dog
        if clock > next_watch_dog_clock:
            watch_dog.feed()
            print(f".")
            next_watch_dog_clock = clock + (constants['watch_dog_timeout_secs'] * 500)

        # check hero_switch
        hero_switch.update()
        if hero_switch.fell:
            current_state = State.STANDBY
            ring_pixels.fill(OFF)
            stick_pixels.fill(OFF)
            print(f" - Hero switch fell: current_state={current_state}")
        elif hero_switch.rose:
            current_state = State.LOOP_IDLE
            print(f" - Hero switch rose: current_state={current_state}")

        # Update the Cyclotron
        if (clock > next_cyclotron_clock) and (current_state == State.LOOP_IDLE):
            # Calculate time of next cyclotron update
            next_cyclotron_clock = clock + cyclotron_speed

            # turn on the appropriate pixels
            ring_pixels[cyclotron_cursor_on] = RED
            ring_pixels[cyclotron_cursor_off] = OFF

            # increment cursors
            cyclotron_cursor_off = (cyclotron_cursor_on - cyclotron_cursor_width) % len(ring_pixels)
            cyclotron_cursor_on = (cyclotron_cursor_on + 1) % len(ring_pixels)

        # Update the Power Meter
        if (clock > next_power_meter_clock) and (current_state == State.LOOP_IDLE):
            # Calculate time of next power meter update
            next_power_meter_clock = clock + power_meter_speed

            # reset if the cursor is over the max
            if power_meter_cursor > power_meter_max:
                ring_pixels[cyclotron_cursor_off] = WHITE  # spark when we hit max
                power_meter_max_previous = power_meter_max
                power_meter_max = random.randrange(0, len(stick_pixels) - 1)
                power_meter_cursor = 0
                stick_pixels.fill(OFF)

            # turn on the appropriate pixels
            stick_pixels[power_meter_cursor] = BLUE
            stick_pixels[power_meter_max_previous] = GREEN
            power_meter_cursor += 1

        time.sleep(constants['sleep_time_secs'])
