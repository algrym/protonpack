#!/usr/bin/env python3
import os
import random
import sys
import time

import board
import digitalio
import neopixel

# Software version
protonpack_version: str = '0.4'

# Update this to match the number of NeoPixel LEDs connected to your boards
neopixel_stick_num_pixels: int = 20
neopixel_ring_num_pixels: int = 20

# Which pins are the stick and ring connected to?
# (These should be different, but you do you.)
neopixel_stick_pin = board.GP1
neopixel_ring_pin = board.GP0

neopixel_stick_brightness: float = 0.008  # 0.008 is the dimmest I can make them
neopixel_ring_brightness: float = 0.02  # 0.008 is the dimmest I can make them

# How fast should the neopixel cycle?
neopixel_stick_speed = 40
neopixel_ring_speed = 40

# Color constants
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)


def print_startup():
    print(f"-=< protonpack v{protonpack_version} - https://github.com/algrym/protonpack/ >=-")
    print(f" - uname: {os.uname()}")
    print(f" - python v{sys.version}")
    print(f" - neopixel v{neopixel.__version__}")


def neopixel_run():
    stick_pixels = neopixel.NeoPixel(neopixel_stick_pin, neopixel_stick_num_pixels)
    ring_pixels = neopixel.NeoPixel(neopixel_ring_pin, neopixel_ring_num_pixels)

    stick_pixels.brightness = neopixel_stick_brightness
    ring_pixels.brightness = neopixel_ring_brightness

    # Set up the LED on-board the pico to indicate the clock
    onboard_led = digitalio.DigitalInOut(board.LED)
    onboard_led.direction = digitalio.Direction.OUTPUT

    # Make sure all the pixels are working
    for c in (OFF, RED, GREEN, BLUE, WHITE, OFF):
        stick_pixels.fill(c)
        ring_pixels.fill(c)
        time.sleep(1)

    # Main driver loop
    clock = ring_cursor = 0
    stick_cursor = stick_max = 0
    while True:
        # if the clock is a multiple of the speed,
        #   check the status of the pixel at the cursor.
        #      Turn it on if it's off.
        #      Turn it off if it's on, and increment the cursor.
        if clock % neopixel_ring_speed == 0:
            if ring_pixels[ring_cursor] == OFF:
                ring_pixels[ring_cursor] = RED
            else:
                ring_pixels[ring_cursor] = OFF
                ring_cursor += 1
        if ring_cursor >= len(ring_pixels):
            ring_cursor = 0

        # increment the power cell
        if clock % neopixel_stick_speed == 0:
            if stick_cursor >= stick_max:
                stick_max = random.randrange(0, len(stick_pixels))
                stick_cursor = 0
                stick_pixels.fill(OFF)
            stick_pixels[stick_cursor] = BLUE
            stick_cursor += 1
        if stick_cursor >= len(stick_pixels):
            stick_pixels = 0

        # reset counters periodically to avoid overflow
        if (ring_cursor == 0) and (stick_cursor == 0):
            print("Resetting clock and LEDs")
            stick_pixels.fill(OFF)
            clock = 0

        # increment the LED and clock
        onboard_led.value = clock % 2
        clock += 1

        time.sleep(0.1)


def main() -> int:
    print_startup()
    neopixel_run()
    return 0


# main
if __name__ == '__main__':
    sys.exit(main())
