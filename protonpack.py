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

# Update this to match the number of NeoPixel LEDs connected to your boards
neopixel_stick_num_pixels = 20
neopixel_ring_num_pixels = 20

# Which pins are the stick and ring connected to?
# (These should be different, but you do you.)
neopixel_stick_pin = board.GP1
neopixel_ring_pin = board.GP0

neopixel_stick_brightness = 0.008  # 0.008 is the dimmest I can make them
neopixel_ring_brightness = 0.02  # 0.008 is the dimmest I can make them

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
    print("-=< protonpack v0.3 - https://github.com/algrym/protonpack/ >=-")
    print(f" - uname: {os.uname()}")
    print(f" - python v{sys.version}")
    print(f" - cpu count: {number_cpus}")
    print(f" - neopixel v{neopixel.__version__}")


def neopixel_run():
    stick_pixels = neopixel.NeoPixel(neopixel_stick_pin, neopixel_stick_num_pixels)
    ring_pixels = neopixel.NeoPixel(neopixel_ring_pin, neopixel_ring_num_pixels)

    stick_pixels.brightness = neopixel_stick_brightness
    ring_pixels.brightness = neopixel_ring_brightness

    stick_sleep_duration = 1 / neopixel_stick_speed
    ring_sleep_duration = 1 / neopixel_ring_speed

    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT

    # Make sure all the pixels are working
    for c in (OFF, RED, GREEN, BLUE, WHITE):
        stick_pixels.fill(c)
        time.sleep(30 * stick_sleep_duration)

    while True:
        previous = len(ring_pixels) - 1
        for i in range(len(ring_pixels)):
            ring_pixels[i] = RED
            ring_pixels[previous] = RED
            led.value = i % 2
            time.sleep(ring_sleep_duration)
            ring_pixels[previous] = OFF
            previous = i

    # this loop works just for the blue power meter
    # while True:
    #     max_pixel = random.randrange(0, len(stick_pixels))
    #     for i in range(max_pixel):
    #         stick_pixels[i] = BLUE
    #         led.value = i % 2
    #         time.sleep(stick_sleep_duration)
    #     stick_pixels.fill(OFF)


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
