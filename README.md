# protonpack

This is a MicroPython script to drive NeoPixels in a
Ghostbusters-style proton pack.

Specificially it will drive:
- Neopixel Ring 60 in the cyclotron
- Neopixel Stick in the power cell

Not all features are implemented yet.

I'm using the following pins on the Raspberry PI Pico:
- Pin 32/GP27 to DIN+ on NeoPixel Stick
- Pin 33/GND to GND on both Neopixel boards (via black wire)
- Pin 34/GP28 to DIN+ on Neopixel Ring
- Pin 39/VSYS to +DC on both Neopixel boards (via red wire)
