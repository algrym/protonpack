#!/usr/bin/env python3
import atexit
import os
import random
import sys
import time

import audiomp3
import audiopwmio
import rotaryio
import supervisor

import adafruit_fancyled.adafruit_fancyled as fancyled
import board
import digitalio
import microcontroller
import neopixel
import version
from adafruit_debouncer import Debouncer

# Software version
protonpack_version: str = version.__version__

# Update this to match the number of NeoPixel LEDs connected to your boards
neopixel_stick_num_pixels: int = 20
neopixel_ring_num_pixels: int = 60

# Which pins are the stick and ring connected to?
# (These should be different, but you do you.)
neopixel_stick_pin = board.GP27
neopixel_ring_pin = board.GP28

# Audio data out pin
audio_out_pin = board.GP21

# Rotary encoder pins
rotary_encoder_button_pin = board.GP10
rotary_encoder_dt_pin = board.GP11
rotary_encoder_clock_pin = board.GP12

# Pixel brightness
neopixel_stick_brightness: float = 0.5  # 0.008 is the dimmest I can make the stick
neopixel_ring_brightness: float = 0.7  # 0.008 is the dimmest I can make them
brightness_levels = (0.25, 0.3, 0.15)  # balance the colors better so white doesn't appear blue-tinged

# how many LEDs should the ring light at one time?
ring_cursor_width: int = 3

# Startup sound MP3 path
startup_mp3_filename = 'lib/KJH_PackstartCombo.mp3'

#
###################################################################
# No config beyond this point
###################################################################
#

def main_event_loop():
    # Print startup info
    print(f"-=< protonpack v{protonpack_version} - https://github.com/algrym/protonpack/ >=-")
    print(f" - uname: {os.uname()}")
    print(f" - cpu uid: {microcontroller.cpu.uid}")
    print(f" -- freq: {microcontroller.cpu.frequency / 1e6} MHz")
    print(f" -- reset reason: {microcontroller.cpu.reset_reason}")
    print(f" -- nvm: {len(microcontroller.nvm)} bytes")
    print(f" - python v{sys.version}")
    print(f" - Adafruit fancyled v{fancyled.__version__}")

    # initialize neopixels
    #   Note: you may need to change pixel_order if you have an RGB, RGBW, GRBW, etc.
    print(f" - neopixel v{neopixel.__version__}")
    print(f"   - NeoPixel stick size {neopixel_stick_num_pixels} on {neopixel_stick_pin}")
    stick_pixels = neopixel.NeoPixel(neopixel_stick_pin,
                                     neopixel_stick_num_pixels,
                                     brightness=neopixel_stick_brightness,
                                     pixel_order=neopixel.GRBW)
    print(f"   - NeoPixel ring  size {neopixel_ring_num_pixels} on {neopixel_ring_pin}")
    ring_pixels = neopixel.NeoPixel(neopixel_ring_pin,
                                    neopixel_ring_num_pixels,
                                    brightness=neopixel_ring_brightness)

    # initialize rotary encoder button
    print(" - Rotary encoder:")
    print(f"   - button on {rotary_encoder_button_pin}")
    rotary_encoder_button_input = digitalio.DigitalInOut(rotary_encoder_button_pin)
    rotary_encoder_button_input.direction = digitalio.Direction.INPUT
    rotary_encoder_button_input.pull = digitalio.Pull.UP
    rotary_encoder_button = Debouncer(rotary_encoder_button_input)

    # initialize rotary encoder
    print(f"   -  clock on {rotary_encoder_clock_pin}")
    print(f"   -     dt on {rotary_encoder_dt_pin}")
    rotary_encoder = rotaryio.IncrementalEncoder(rotary_encoder_clock_pin,
                                                 rotary_encoder_dt_pin)

    print(f" - Audio out on {audio_out_pin}")
    audio = audiopwmio.PWMAudioOut(audio_out_pin)

    print(f" - Loading startup MP3: {startup_mp3_filename}")
    decoder = audiomp3.MP3Decoder(open(startup_mp3_filename, 'rb'))

    # How fast should the neopixel cycle?
    # This is (similar to) microseconds per increment so: Higher is slower
    neopixel_stick_speed: int = 20
    neopixel_ring_speed_current: int = 80  # Start this high to emulate spin-up
    neopixel_ring_speed_cruise: int = 10
    change_speed: int = 30  # How often should we change speed?

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

    # set up for main loop
    ring_cursor_on = ring_cursor_off = ring_color_index = 0
    stick_cursor = stick_max_previous = stick_max = 0
    stick_pixel_max = 1
    stick_clock_next = ring_clock_next = adjust_clock_next = 0
    rotary_encoder_last_position = None

    # set up timers
    next_stat_clock: int = supervisor.ticks_ms() + 5000
    start_time: int = int(time.time())
    last_loop_time: int = start_time
    loop_count: int = 0

    # Setup hardware watchdog in case things go wrong
    watch_dog = microcontroller.watchdog
    watch_dog.timeout = 8       # Hardware maximum of 8 secs
    watch_dog.mode = watchdog.WatchDogMode.RESET
    if supervisor.runtime.serial_connected:
        print(f' - Watchdog: feed me every {watch_dog.timeout} seconds or face {watch_dog.mode}')

    print(f" - Playing {decoder.file}")
    audio.play(decoder)

    # main driver loop
    print(' - Entering main event loop.')
    while True:
        clock = supervisor.ticks_ms()
        loop_count += 1

        # Print the average runs per second ever 10secs
        if clock > next_stat_clock:
            next_stat_clock: int = clock + 5000
            print(f" - Running {time.time() - start_time}s at {loop_count / (time.time() - last_loop_time)} loops/second")
            loop_count = 0
            last_loop_time = int(time.time())

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
        rotary_encoder_button.update()
        if rotary_encoder_button.rose:  # Handle trigger release
            ring_pixels.fill(OFF)
            print(f"   - Trigger rose at {clock}")
        elif rotary_encoder_button.fell:  # Handle trigger engage
            ring_pixels.fill(WHITE)
            print(f"   - Trigger fell at {clock}")

        if not rotary_encoder_button.value:
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
            watch_dog.feed()
            # calculate time of next stick update
            stick_clock_next = clock + neopixel_stick_speed

            # reset if the cursor is over the max
            if stick_cursor > stick_max:
                ring_pixels[ring_cursor_off] = WHITE  # spark when we hit max
                stick_max_previous = stick_max
                stick_max = random.randrange(0, stick_pixel_max - 1)
                stick_cursor = 0
                stick_pixels.fill(OFF)

            # turn on the appropriate pixels
            stick_pixels[stick_cursor] = BLUE
            stick_pixels[stick_max_previous] = GREEN
            stick_cursor += 1

        # modify color as rotary encoder is turned
        rotary_encoder_current_position = rotary_encoder.position
        if rotary_encoder_last_position is None or rotary_encoder_current_position != rotary_encoder_last_position:
            ring_color_index = rotary_encoder_current_position % len(ring_on_color)
            print(f" - Ring color set to {ring_on_color[ring_color_index]} from encoder {rotary_encoder_current_position}")
        rotary_encoder_last_position = rotary_encoder_current_position

        # increment the ring
        if clock > ring_clock_next:
            watch_dog.feed()
            # Calculate time of next ring update
            ring_clock_next = clock + neopixel_ring_speed_current

            # turn on the appropriate pixels
            ring_pixels[ring_cursor_on] = ring_on_color[ring_color_index]
            ring_pixels[ring_cursor_off] = OFF

            # increment cursors
            ring_cursor_off = (ring_cursor_on - ring_cursor_width) % len(ring_pixels)
            ring_cursor_on = (ring_cursor_on + 1) % len(ring_pixels)

        time.sleep(0.001)

if __name__ == "__main__":
    main_event_loop()