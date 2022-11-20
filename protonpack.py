#!/usr/bin/env python3
import os
import random
import sys
import time

import board
import neopixel

# Software version
protonpack_version: str = '0.5'

# Update this to match the number of NeoPixel LEDs connected to your boards
neopixel_stick_num_pixels: int = 20
neopixel_ring_num_pixels: int = 60

# Which pins are the stick and ring connected to?
# (These should be different, but you do you.)
neopixel_stick_pin = board.GP27
neopixel_ring_pin = board.GP28

neopixel_stick_brightness: float = 0.02  # 0.008 is the dimmest I can make the stick
neopixel_ring_brightness: float = 0.3  # 0.008 is the dimmest I can make them

# How fast should the neopixel cycle?
sleep_duration: float = 0.001
neopixel_stick_speed = 6
neopixel_ring_speed = 3
onboard_led_speed = 20

# Print startup info
print(f"-=< protonpack v{protonpack_version} - https://github.com/algrym/protonpack/ >=-")
print(f" - uname: {os.uname()}")
print(f" - python v{sys.version}")
print(f" - neopixel v{neopixel.__version__}")

# Color constants
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)

# initialize neopixels
stick_pixels = neopixel.NeoPixel(neopixel_stick_pin, neopixel_stick_num_pixels)
ring_pixels = neopixel.NeoPixel(neopixel_ring_pin, neopixel_ring_num_pixels)

# set brightness
stick_pixels.brightness = neopixel_stick_brightness
ring_pixels.brightness = neopixel_ring_brightness

# Make sure all the pixels are working
for c in (OFF, RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, WHITE, OFF):
    stick_pixels.fill(c)
    ring_pixels.fill(c)
    time.sleep(0.1)

# set up main driver loop
clock = ring_cursor = 0
ring_previous = len(ring_pixels) - 1
stick_cursor = stick_max = 0

# main driver loop
while True:
    # if the clock is a multiple of the speed,
    #   check the status of the pixel at the cursor.
    #      Turn it on if it's off.
    #      Turn it off if it's on, and increment the cursor.
    if clock % neopixel_ring_speed == 0:
        if ring_pixels[ring_cursor] == OFF:
            ring_pixels[ring_cursor] = RED
            ring_pixels[ring_previous] = RED
        else:
            ring_pixels[ring_cursor] = OFF
            ring_pixels[ring_previous] = OFF
            ring_previous = ring_cursor
            ring_cursor += 1
    if ring_cursor >= len(ring_pixels):
        ring_cursor = 0
    if ring_previous >= len(ring_pixels):
        ring_previous = 0
        clock = 0

    # increment the power cell
    if clock % neopixel_stick_speed == 0:
        if stick_cursor >= stick_max:
            stick_max = random.randrange(0, len(stick_pixels))
            stick_cursor = 0
            stick_pixels.fill(OFF)
            ring_pixels[ring_cursor] = WHITE  # flash the ring element to white
        stick_pixels[stick_cursor] = BLUE
        stick_cursor += 1
    if stick_cursor >= len(stick_pixels):
        stick_pixels = 0

    clock += 1
