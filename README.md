![Photo01](https://github.com/kysutrung/customize_rekordbox_controller/blob/main/mediaaa/repo_cover.jpg)


# DJ Controller for Rekordbox using Raspberry Pi Pico

## Introduction
This project is a DIY DJ controller that interfaces with Pioneer’s Rekordbox software using the MIDI protocol. The controller is built using a Raspberry Pi Pico and programmed with CircuitPython. It allows users to control Rekordbox features such as tempo adjustment, effects, EQ.....

## Features
- USB MIDI communication with Rekordbox
- Customizable knob mappings
- CircuitPython-based for easy development
- Compatible with Windows computers

## Hardware Requirements
- Raspberry Pi Pico
- Analog Multiplexer
- Potentiometers (optional for volume/EQ controls)
- USB cable (to connect the Pico to a computer)

## Software Requirements
- [CircuitPython](https://circuitpython.org/) installed on Raspberry Pi Pico
- [Adafruit MIDI Library](https://github.com/adafruit/Adafruit_CircuitPython_MIDI)
- Rekordbox software installed on your computer

## Installation
### 1. Set up CircuitPython on Raspberry Pi Pico
1. Download and install CircuitPython for the Raspberry Pi Pico from [CircuitPython Downloads](https://circuitpython.org/board/raspberry_pi_pico/).
2. Copy the downloaded UF2 file onto the Pico.
3. Once installed, the Pico will appear as a USB drive named `CIRCUITPY`.

### 2. Install Required Libraries
1. Download the `Adafruit_CircuitPython_MIDI` library from Adafruit.
2. Copy the `midi` folder from the downloaded library into the `lib` folder on the Pico.

### 3. Upload the Code
1. Clone this repository
2. Rename final code into `code.py` and copy file into the `CIRCUITPY` drive.
3. Restart the Pico if needed.

## Usage
1. Connect the Raspberry Pi Pico to your computer via USB.
2. Open Rekordbox and open MIDI menu.
3. Map the MIDI controls in Rekordbox to match your hardware layout.
4. Start mixing and enjoy!

## Customization
- Modify `code.py` to adjust button mappings and MIDI messages.
- Add more controls by expanding the hardware setup.
- Implement LED feedback for visual cues.

## Troubleshooting
- If the Pico is not recognized as a MIDI device, ensure CircuitPython and the MIDI library are installed correctly.
- Check the USB cable (some cables are power-only and do not support data transfer).
- If controls are not responding, verify that Rekordbox is set to receive MIDI input from the Pico.

