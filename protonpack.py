#!/usr/bin/env python3
import atexit
import os
import random
import sys

import board
import neopixel
import supervisor
import digitalio

import adafruit_fancyled.adafruit_fancyled as fancyled
from adafruit_debouncer import Debouncer

# Software version
protonpack_version: str = '0.9'

# Update this to match the number of NeoPixel LEDs connected to your boards
neopixel_stick_num_pixels: int = 20
neopixel_ring_num_pixels: int = 60

# Which pins are the stick and ring connected to?
# (These should be different, but you do you.)
neopixel_stick_pin = board.GP27
neopixel_ring_pin = board.GP28

# Input pin numbers
trigger_input_pin = board.GP26
select_input_pin = board.GP22

# Pixel brightness
neopixel_stick_brightness: float = 0.02  # 0.008 is the dimmest I can make the stick
neopixel_ring_brightness: float = 0.3  # 0.008 is the dimmest I can make them

# How fast should the neopixel cycle?
# This is (similar to) microseconds per increment so: Higher is slower
neopixel_stick_speed = 20
neopixel_ring_speed_current = 80  # Start this high to emulate spin-up
neopixel_ring_speed_cruise = 10
change_speed = 30  # How often should we change speed?

# how many LEDs should the ring light at one time?
ring_cursor_width = 3

# Print startup info
print(f"-=< protonpack v{protonpack_version} - https://github.com/algrym/protonpack/ >=-")
print(f" - uname: {os.uname()}")
print(f" - python v{sys.version}")
print(f" - neopixel v{neopixel.__version__}")

# Color constants
RED = fancyled.gamma_adjust(CRGB(255, 0, 0))
ORANGE = fancyled.gamma_adjust(CRGB(255, 165, 0))
YELLOW = fancyled.gamma_adjust(CRGB(255, 255, 0))
GREEN = fancyled.gamma_adjust(CRGB(0, 255, 0))
BLUE = fancyled.gamma_adjust(CRGB(0, 0, 255))
PURPLE = fancyled.gamma_adjust(CRGB(128, 0, 128))
WHITE = fancyled.gamma_adjust(CRGB(255, 255, 255))
OFF = (0, 0, 0)

ring_on_color = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, WHITE]

# initialize neopixels
print(f" - NeoPixel stick size {neopixel_stick_num_pixels} on {neopixel_stick_pin}")
stick_pixels = neopixel.NeoPixel(neopixel_stick_pin,
                                 neopixel_stick_num_pixels,
                                 brightness=neopixel_stick_brightness)
print(f" - NeoPixel ring  size {neopixel_ring_num_pixels} on {neopixel_ring_pin}")
ring_pixels = neopixel.NeoPixel(neopixel_ring_pin,
                                neopixel_ring_num_pixels,
                                brightness=neopixel_ring_brightness)

# initialize buttons
print(f" - Input trigger on {trigger_input_pin}")
trigger_button_pin = digitalio.DigitalInOut(trigger_input_pin)
trigger_button_pin.direction = digitalio.Direction.INPUT
trigger_button_pin.pull = digitalio.Pull.UP
trigger_button = Debouncer(trigger_button_pin)

print(f" - Input select on {select_input_pin}")
select_button_pin = digitalio.DigitalInOut(select_input_pin)
select_button_pin.direction = digitalio.Direction.INPUT
select_button_pin.pull = digitalio.Pull.UP
select_button = Debouncer(select_button_pin)

# callback to turn everything off on exit
def all_off():
    print("Exiting: all pixels off.")
    stick_pixels.fill(OFF)
    ring_pixels.fill(OFF)
    sys.exit(0)

# turn everything off on exit
atexit.register(all_off)

# set up main driver loop
ring_cursor_on = ring_cursor_off = ring_color_index = 0
stick_cursor = stick_max_previous = stick_max = 0
stick_pixel_max = 1
stick_clock_next = ring_clock_next = adjust_clock_next = 0

# main driver loop
while True:
    clock = supervisor.ticks_ms()

    # check trigger button
    trigger_button.update()
    if trigger_button.rose:
        ring_pixels.fill(WHITE)
        print(f" - Trigger   up at {clock}")
    elif trigger_button.fell:
        ring_pixels.fill(OFF)
        print(f" - Trigger down at {clock}")

    # check select button
    select_button.update()
    if select_button.fell:
        ring_color_index += 1
        if ring_color_index >= len(ring_on_color):
            ring_color_index = 0
        print(f" - Ring color set to {ring_on_color[ring_color_index]}")

    # increment speeds
    if clock > adjust_clock_next:
        # calculate time of next speed update
        adjust_clock_next = clock + change_speed

        # adjust stick max if its too low
        if stick_pixel_max < len(stick_pixels):
            stick_pixel_max += 1

        # adjust ring speed if its too low
        if (neopixel_ring_speed_current > neopixel_ring_speed_cruise):
            neopixel_ring_speed_current -= 1
            ring_pixels[ring_cursor_off] = WHITE  # spark when we change speed

    # increment the ring
    if clock > ring_clock_next:
        # Calculate time of next ring update
        ring_clock_next = clock + neopixel_ring_speed_current

        # turn on the appropriate pixels
        ring_pixels[ring_cursor_on] = ring_on_color[ring_color_index]
        ring_pixels[ring_cursor_off] = OFF

        # increment cursors
        ring_cursor_off = ring_cursor_on - ring_cursor_width
        ring_cursor_on += 1

        # Reset the ring_cursor if it goes out of bounds
        if ring_cursor_on >= len(ring_pixels):
            ring_cursor_on = 0
        if ring_cursor_off >= len(ring_pixels):
            ring_cursor_off = 0

    # increment the power cell
    if clock > stick_clock_next:
        # calculate time of next stick update
        stick_clock_next = clock + neopixel_stick_speed

        # reset if the cursor is over the max
        if stick_cursor > stick_max:
            ring_pixels[ring_cursor_off] = BLUE  # spark when we hit max
            stick_max_previous = stick_max
            stick_max = random.randrange(0, stick_pixel_max)
            stick_cursor = 0
            stick_pixels.fill(OFF)

        stick_pixels[stick_cursor] = BLUE
        stick_pixels[stick_max_previous] = GREEN
        stick_cursor += 1

    pass
