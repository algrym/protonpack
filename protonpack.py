import board
import neopixel

pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, auto_write=False)
pixels[0] = (10, 0, 0)
pixels[9] = (0, 10, 0)
pixels.show()
