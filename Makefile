# This works for Macs.  Need to update for other platforms.
UF2_DIR=/Volumes/RPI-RP2
CIRCUIT_PYTHON_DIR=/Volumes/CIRCUITPY
CIRCUIT_PYTHON_VER=8.2.7
CIRCUIT_PYTHON_LIB_VER=8.x
CIRCUIT_PYTHON_LIB_DATE=20231024
CODEPY_DIR=$(CIRCUIT_PYTHON_DIR)/
CODEPY_LIB_DIR=$(CIRCUIT_PYTHON_DIR)/lib

# These shouldn't need changing, but eh ...
CURLFLAGS="--location"

all: venv downloads .gitignore version.py

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || virtualenv venv
	. venv/bin/activate; pip install --upgrade pip
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

version.py: code.py
	date -r code.py "+__version__ = %'%Y-%m-%d %H:%M:%S%'" > version.py

test: venv
	. venv/bin/activate; nosetests project/test

.gitignore:
	curl https://www.toptal.com/developers/gitignore/api/python,circuitpython,git,virtualenv,macos,vim,pycharm -o .gitignore
	printf "\n# ignore the downloads directory\ndownloads\n" >> .gitignore
	printf "\n# ignore .idea/ directory\n.idea/\n" >> .gitignore
	printf "\n# ignore mp3 files\n*.mp3\n" >> .gitignore
	printf "\n# ignore version.py that updates each install\nversion.py\n" >> .gitignore

downloads: \
	downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2 \
	downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip \
	KJH_PackstartCombo.mp3

KJH_PackstartCombo.mp3:
	curl -LO http://hprops.com/sounds/KJH_PackstartCombo.mp3

downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/$(CIRCUIT_PYTHON_LIB_DATE)/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE).zip -o $(@)
	unzip $(@) -d downloads/

downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2:
	test -d downloads || mkdir downloads
	curl $(CURLFLAGS) https://downloads.circuitpython.org/bin/raspberry_pi_pico/en_US/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2 -o $(@)

install_circuit_python: downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2
	cp downloads/adafruit-circuitpython-raspberry_pi_pico-en_US-$(CIRCUIT_PYTHON_VER).uf2 $(UF2_DIR)/

install: all
	rsync -avlcC \
		version.py code.py \
			$(CODEPY_DIR)
	rsync -avlcC \
		KJH_PackstartCombo.mp3 \
		downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE)/lib/neopixel* \
		downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE)/lib/*ticks* \
		downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE)/lib/*debouncer* \
		downloads/adafruit-circuitpython-bundle-$(CIRCUIT_PYTHON_LIB_VER)-mpy-$(CIRCUIT_PYTHON_LIB_DATE)/lib/*adafruit_fancyled* \
			$(CODEPY_LIB_DIR)

clean:
	rm -rf venv downloads
	find . -iname '*.pyc' -delete
