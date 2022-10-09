# This works for Macs.  Need to update for other platforms.
UF2_DIR=/Volumes/RPI-RP2
CIRCUIT_PYTHON_DIR=/Volumes/CIRCUITPY
CODEPY_PATH=$(CIRCUIT_PYTHON_DIR)/code.py
CODEPY_LIB_DIR=$(CIRCUIT_PYTHON_DIR)/lib

# These shouldn't need changing, but eh ...
CURLFLAGS="--location"

all: venv downloads .gitignore

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install --upgrade pip
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

test: venv
	. venv/bin/activate; nosetests project/test

.gitignore:
	curl https://www.toptal.com/developers/gitignore/api/python,circuitpython,git,virtualenv,macos,vim -o .gitignore
	printf "\n# Also ignore the downloads directory\ndownloads\n" >> .gitignore

downloads: \
	downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2 \
	downloads/adafruit-circuitpython-bundle-7.x-mpy-20221007.zip

downloads/adafruit-circuitpython-bundle-7.x-mpy-20221007.zip:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/20221007/adafruit-circuitpython-bundle-7.x-mpy-20221007.zip -o $(@)
	unzip $(@) -d downloads/

downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://downloads.circuitpython.org/bin/raspberry_pi_pico/en_US/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2 -o $(@)

install_circuit_python: downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2
	cp downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2 $(UF2_DIR)/

install: all
	cp protonpack.py $(CODEPY_PATH)
	rsync -avlC downloads/adafruit-circuitpython-bundle-7.x-mpy-20221007/lib/neopixel* $(CODEPY_LIB_DIR)

clean:
	rm -rf venv downloads
	find . -iname '*.pyc' -delete
