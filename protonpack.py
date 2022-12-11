#!/usr/bin/env python3
import atexit
import os
import random
import sys
import time

import adafruit_fancyled.adafruit_fancyled as fancyled
import audiomp3
import audiopwmio
import board
import digitalio
import neopixel
import supervisor
from adafruit_debouncer import Debouncer

# Software version
protonpack_version: str = '0.0.10'

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

# Audio data out pin
audio_out_pin = board.GP21

# Pixel brightness
neopixel_stick_brightness: float = 0.3  # 0.008 is the dimmest I can make the stick
neopixel_ring_brightness: float = 0.5  # 0.008 is the dimmest I can make them
brightness_levels = (0.25, 0.3, 0.15)  # balance the colors better so white doesn't appear blue-tinged

# How fast should the neopixel cycle?
# This is (similar to) microseconds per increment so: Higher is slower
neopixel_stick_speed: int = 20
neopixel_ring_speed_current: int = 80  # Start this high to emulate spin-up
neopixel_ring_speed_cruise: int = 10
change_speed: int = 30  # How often should we change speed?

# how many LEDs should the ring light at one time?
ring_cursor_width: int = 3

# Startup sound MP3 path
startup_mp3_filename = 'KJH_PackstartCombo.mp3'

#
###################################################################
# No config beyond this point
###################################################################
#

# Print startup info
print(f"-=< protonpack v{protonpack_version} - https://github.com/algrym/protonpack/ >=-")
print(f" - uname: {os.uname()}")
print(f" - python v{sys.version}")
print(f" - neopixel v{neopixel.__version__}")
print(f" - Adafruit fancyled v{fancyled.__version__}")
print(f" - Adafruit debounce v{Debouncer}")

# Color constants
RED = fancyled.gamma_adjust(fancyled.CRGB(255, 0, 0), brightness=brightness_levels).pack()
ORANGE = fancyled.gamma_adjust(fancyled.CRGB(255, 165, 0), brightness=brightness_levels).pack()
YELLOW = fancyled.gamma_adjust(fancyled.CRGB(255, 255, 0), brightness=brightness_levels).pack()
GREEN = fancyled.gamma_adjust(fancyled.CRGB(0, 255, 0), brightness=brightness_levels).pack()
BLUE = fancyled.gamma_adjust(fancyled.CRGB(0, 0, 255), brightness=brightness_levels).pack()
PURPLE = fancyled.gamma_adjust(fancyled.CRGB(128, 0, 128), brightness=brightness_levels).pack()
WHITE = fancyled.gamma_adjust(fancyled.CRGB(255, 255, 255), brightness=brightness_levels).pack()
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

print(f" - Audio out on {audio_out_pin}")
audio = audiopwmio.PWMAudioOut(audio_out_pin)

print(f" - Loading startup MP3: {startup_mp3_filename}")
decoder = audiomp3.MP3Decoder(startup_mp3_filename)


def all_off():
    # callback to turn everything off on exit
    print(' - Exiting: all pixels off.')
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

print(f" - Playing {decoder.file}")
audio.play(decoder)

# main driver loop
print(' - Entering main event loop.')
while True:
    clock = supervisor.ticks_ms()

    # increment speeds
    if clock > adjust_clock_next:
        # calculate time of next speed update
        adjust_clock_next = clock + change_speed

        # adjust stick max if it's too low
        if stick_pixel_max < len(stick_pixels):
            stick_pixel_max += 1

        # adjust ring speed if it's too low
        if neopixel_ring_speed_current > neopixel_ring_speed_cruise:
            neopixel_ring_speed_current -= 1
            ring_pixels[ring_cursor_off] = WHITE  # spark when we change speed

    # check trigger button
    #   trigger/release/value are inverted from what I'd expect
    trigger_button.update()
    if trigger_button.rose:  # Handle trigger release
        ring_pixels.fill(OFF)
        print(f"   - Trigger rose at {clock}")
    elif trigger_button.fell:  # Handle trigger engage
        ring_pixels.fill(WHITE)
        print(f"   - Trigger fell at {clock}")

    if not trigger_button.value:
        # Trigger active: flash the cyclotron!
        flash_random = random.randrange(0, 20)
        if flash_random < 3:
            ring_pixels.fill(ring_on_color[ring_color_index])
        elif flash_random == 4:
            ring_pixels.fill(WHITE)
        elif flash_random == 5:
            ring_pixels.fill(ring_on_color[random.randrange(0, len(ring_on_color))])
        else:
            ring_pixels.fill(OFF)

        # Trigger active: decrement the power meter!
        if (clock % 150) == 0:
            if stick_cursor > 0:
                stick_pixels[stick_cursor] = OFF
                stick_pixels[stick_max_previous] = GREEN
                stick_cursor -= 1
        continue  # Skip the ring and stick updates if the trigger is down

    # increment the power cell
    if clock > stick_clock_next:
        # calculate time of next stick update
        stick_clock_next = clock + neopixel_stick_speed

        # reset if the cursor is over the max
        if stick_cursor > stick_max:
            ring_pixels[ring_cursor_off] = WHITE  # spark when we hit max
            stick_max_previous = stick_max
            stick_max = random.randrange(0, stick_pixel_max)
            stick_cursor = 0
            stick_pixels.fill(OFF)

        # turn on the appropriate pixels
        stick_pixels[stick_cursor] = BLUE
        stick_pixels[stick_max_previous] = GREEN
        stick_cursor += 1

    # increment cyclotron color if select button is tapped
    select_button.update()
    if select_button.fell:
        ring_color_index = (ring_color_index + 1) % len(ring_on_color)
        print(f" - Ring color set to {ring_on_color[ring_color_index]}")

    # increment the ring
    if clock > ring_clock_next:
        # Calculate time of next ring update
        ring_clock_next = clock + neopixel_ring_speed_current

        # turn on the appropriate pixels
        ring_pixels[ring_cursor_on] = ring_on_color[ring_color_index]
        ring_pixels[ring_cursor_off] = OFF

        # increment cursors
        ring_cursor_off = (ring_cursor_on - ring_cursor_width) % len(ring_pixels)
        ring_cursor_on = (ring_cursor_on + 1) % len(ring_pixels)

    time.sleep(0.001)
