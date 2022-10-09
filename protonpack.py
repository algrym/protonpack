import os
import sys
import time

import board
import digitalio
import microcontroller
import neopixel

# We know there's at least one
number_cpus = 1


def print_startup():
    print("-=< protonpack v0.1 - https://github.com/algrym/protonpack/ >=-")
    print(f" - uname: {os.uname()}")
    print(f" - python v{sys.version}")
    print(f" - cpu count: {number_cpus}")
    print(f" - neopixel v{neopixel.__version__}")


def update_cpu_count() -> int:
    global number_cpus
    count = 0
    for cpu in microcontroller.cpus:
        count += 1
    number_cpus = count
    return count


def heartbeat_led():
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    while True:
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.1)
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.5)


def main() -> int:
    update_cpu_count()
    print_startup()
    heartbeat_led()
    return 0;


# main
if __name__ == '__main__':
    sys.exit(main())

# pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, auto_write=False)
# pixels[0] = (10, 0, 0)
# pixels[9] = (0, 10, 0)
# pixels.show()
