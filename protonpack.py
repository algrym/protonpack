import os
import random
import sys
import time

import board
import digitalio
import microcontroller
import neopixel

# We know there's at least one, we'll discover if more
number_cpus = 1

# Update this to match the number of NeoPixel LEDs connected to your board.
neopixel_stick_num_pixels = 20

# Which pin is the stick DIN connected to?
neopixel_stick_pin = board.GP0

# How fast should the neopixel stick cycle?
neopixel_stick_speed = 40

# Color constants
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)


def print_startup():
    print("-=< protonpack v0.1 - https://github.com/algrym/protonpack/ >=-")
    print(f" - uname: {os.uname()}")
    print(f" - python v{sys.version}")
    print(f" - cpu count: {number_cpus}")
    print(f" - neopixel v{neopixel.__version__}")


def neopixel_run():
    pixels = neopixel.NeoPixel(neopixel_stick_pin, neopixel_stick_num_pixels)
    pixels.brightness = 0.008  # 0.008 is the dimmest I can make them
    sleep_duration = 1 / neopixel_stick_speed

    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT

    # Make sure all the pixels are working
    for c in (OFF, RED, GREEN, BLUE, WHITE):
        pixels.fill(c)
        time.sleep(30 * sleep_duration)

    while True:
        max_pixel = random.randrange(0, len(pixels))
        # for i in range(len(pixels)):
        for i in range(max_pixel):
            pixels[i] = BLUE
            led.value = i % 2
            time.sleep(sleep_duration)
        pixels.fill(OFF)


def update_cpu_count() -> int:
    global number_cpus
    count = 0
    for cpu in microcontroller.cpus:
        count += 1
    number_cpus = count
    return count


def main() -> int:
    update_cpu_count()
    print_startup()
    neopixel_run()
    return 0


# main
if __name__ == '__main__':
    sys.exit(main())
