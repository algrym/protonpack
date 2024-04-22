#!/usr/bin/env python3

import gc
import os
import sys
import time

import supervisor

import microcontroller
from code import __version__  # Import __version__ from code.py


# Load constants
def load_constants():
    constants = {}

    constants['stat_clock_time_ms'] = os.getenv('stat_clock_time_ms') or "5000"
    constants['sleep_time_secs'] = os.getenv('sleep_time_secs') or "5.0"

    print(f" - Loaded {len(constants)} constants from settings.toml")
    for i in (constants):
        print(f"    - {i} = {constants[i]}")
    return constants


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


def main_loop():
    # Print startup information
    print(f"-=< protonpack v{__version__} - https://github.com/algrym/protonpack/ >=-")
    print(f" - uname: {os.uname()}")
    print_cpu_id()
    print(f" -- freq: {microcontroller.cpu.frequency / 1e6} MHz")
    print(f" -- reset reason: {microcontroller.cpu.reset_reason}")
    print(f" -- nvm: {len(microcontroller.nvm)} bytes")
    print(f" - python v{sys.version}")
    gc.collect()
    starting_memory_free = gc.mem_free()
    print(f" - Free memory: {pretty_print_bytes(starting_memory_free)}")

    # Read in constants
    # TODO: getting an error with return from load_constants
    constants = load_constants()

    # Setup timers
    next_stat_clock: int = supervisor.ticks_ms() + constants['stat_clock_time_ms']

    while True:
        print(".")
        time.sleep(5.0)
