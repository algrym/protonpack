import sys
import board
import digitalio
import neopixel
import time

def print_startup ():
    print("-=< protonpack v0.1 - https://github.com/algrym/protonpack/ >=-")
    print(f" - platform: {sys.platform} v{sys.version}")
    print(f" - neopixel v{neopixel.__version__}")

def heartbeat_led ():
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
    print_startup()
    heartbeat_led()
    return 0;

# main
if __name__ == '__main__':
    sys.exit(main())

#pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, auto_write=False)
#pixels[0] = (10, 0, 0)
#pixels[9] = (0, 10, 0)
#pixels.show()
