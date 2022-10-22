# protonpack

This is a MicroPython script to drive NeoPixels in a
Ghostbusters-style proton pack.

Specificially it will drive:
- Four "Neopixel Ring 60" quarters for the cyclotron
  (https://www.adafruit.com/product/1768)
- Two "Neopixel Stick" segments in the power cell
  (https://www.adafruit.com/product/1426)

I'm using the following pins on the Raspberry PI Pico:
- Pin 32/GP27 to DIN+ on NeoPixel Stick
- Pin 33/GND to GND on both Neopixel boards (via black wire)
- Pin 34/GP28 to DIN+ on Neopixel Ring
- Pin 39/VSYS to +DC on both Neopixel boards (via red wire)

That's based on the pin diagram from adafruit:
https://learn.adafruit.com/assets/99339
