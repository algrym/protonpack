# This works for Macs.  Need to update for other platforms.
PRE-CIRCUIT_PYTHON_DIR=/Volumes/RPI-RP2
CIRCUIT_PYTHON_DIR=/Volumes/CIRCUITPY
CODEPY_PATH=$(CIRCUIT_PYTHON_DIR)/code.py
CODEPY_LIB_DIR=$(CIRCUIT_PYTHON_DIR)/lib

all: venv downloads

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install --upgrade pip
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

test: venv
	. venv/bin/activate; nosetests project/test

downloads: downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2

downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2:
	test -d downloads || mkdir downloads
	curl https://downloads.circuitpython.org/bin/raspberry_pi_pico/en_US/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2 -o $(@)

install_circuit_python: downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2
	cp downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-7.3.3.uf2 $(PRE-CIRCUIT_PYTHON_DIR)/

install: all
	cp protonpack.py $(CODEPY_PATH)

clean:
	rm -rf venv downloads
	find . -iname '*.pyc' -delete
