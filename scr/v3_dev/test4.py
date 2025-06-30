import time
import board
import usb_midi
import digitalio
from analogio import AnalogIn
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

class MidiController:
    def __init__(self):
        # --- CD4051 Multiplexer control pins ---
        self.s0 = digitalio.DigitalInOut(board.GP15)
        self.s1 = digitalio.DigitalInOut(board.GP14)
        self.s2 = digitalio.DigitalInOut(board.GP13)
        for pin in [self.s0, self.s1, self.s2]:
            pin.direction = digitalio.Direction.OUTPUT

        # --- Analog Inputs ---
        self.adc_mux = AnalogIn(board.A0)     # MUX input
        self.adc_direct1 = AnalogIn(board.A1) # CC8
        self.adc_direct2 = AnalogIn(board.A2) # CC9

        # --- Buttons ---
        self.button1 = self.setup_button(board.GP0)  # CC1 delta control
        self.button2 = self.setup_button(board.GP2)  # CC10 delta control

        # --- Additional Buttons IO1, IO3–IO7 (mapped to GP1, GP3–GP7) ---
        self.extra_buttons = [self.setup_button(getattr(board, f"GP{i}")) for i in [1, 3, 4, 5, 6, 7]]
        self.extra_buttons_prev = [True] * len(self.extra_buttons)

        # --- MIDI Interface ---
        self.midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

        # --- State Variables ---
        self.last_values = [-1] * 9
        self.cc1_value = 64
        self.cc10_value = 64
        self.cc1_reference_adc = None
        self.cc10_reference_adc = None
        self.cc1_prev_button = True
        self.cc10_prev_button = True

    def setup_button(self, pin):
        btn = digitalio.DigitalInOut(pin)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.UP
        return btn

    def select_mux_channel(self, ch):
        self.s0.value = ch & 1
        self.s1.value = (ch >> 1) & 1
        self.s2.value = (ch >> 2) & 1

    def adc_to_midi(self, value):
        return min(127, max(0, 127 - int((value / 65535) * 127)))

    def send_cc(self, cc_number, value):
        self.midi.send(ControlChange(cc_number, value))
        print(f"MIDI CC {cc_number}: {value}")

    def send_note_on(self, note, velocity=127):
        self.midi.send(NoteOn(note, velocity))
        print(f"Note On: {note}")

    def send_note_off(self, note, velocity=0):
        self.midi.send(NoteOff(note, velocity))
        print(f"Note Off: {note}")

    def handle_delta_control(self, raw_adc, cc_num, value_ref, ref_adc, prev_state, button_pressed):
        if button_pressed and not prev_state:
            ref_adc = raw_adc

        if button_pressed and ref_adc is not None:
            delta_adc = ref_adc - raw_adc
            delta_midi = int(delta_adc / 512)
            if abs(delta_midi) >= 1:
                new_val = value_ref + delta_midi
                if 0 <= new_val <= 127 and new_val != value_ref:
                    value_ref = new_val
                    self.send_cc(cc_num, value_ref)
                    ref_adc = raw_adc

        return value_ref, ref_adc, button_pressed

    def handle_extra_buttons(self):
        for idx, btn in enumerate(self.extra_buttons):
            current_state = not btn.value  # True when pressed
            prev_state = self.extra_buttons_prev[idx]

            if current_state and not prev_state:
                note_number = 60 + idx  # MIDI notes 60–65 (C4 and up)
                self.send_note_on(note_number)
            elif not current_state and prev_state:
                note_number = 60 + idx
                self.send_note_off(note_number)

            self.extra_buttons_prev[idx] = current_state

    def update(self):
        # Handle extra buttons first
        self.handle_extra_buttons()

        # CC1–CC7 from MUX
        for i, ch in enumerate(range(1, 8)):
            self.select_mux_channel(ch)
            time.sleep(0.002)
            raw = self.adc_mux.value

            if i == 0:
                # CC1 – delta control with button1
                button_state = not self.button1.value
                self.cc1_value, self.cc1_reference_adc, self.cc1_prev_button = self.handle_delta_control(
                    raw, 1, self.cc1_value, self.cc1_reference_adc, self.cc1_prev_button, button_state
                )

                # CC10 – delta control with button2
                button2_state = not self.button2.value
                self.cc10_value, self.cc10_reference_adc, self.cc10_prev_button = self.handle_delta_control(
                    raw, 10, self.cc10_value, self.cc10_reference_adc, self.cc10_prev_button, button2_state
                )

            else:
                cc_num = i + 1
                midi_val = self.adc_to_midi(raw)
                if midi_val != self.last_values[i]:
                    self.send_cc(cc_num, midi_val)
                    self.last_values[i] = midi_val

        # CC8 – direct analog
        raw = self.adc_direct1.value
        midi_val = self.adc_to_midi(raw)
        if midi_val != self.last_values[7]:
            self.send_cc(8, midi_val)
            self.last_values[7] = midi_val

        # CC9 – direct analog
        raw = self.adc_direct2.value
        midi_val = self.adc_to_midi(raw)
        if midi_val != self.last_values[8]:
            self.send_cc(9, midi_val)
            self.last_values[8] = midi_val

# --- MAIN LOOP ---
controller = MidiController()
while True:
    controller.update()
    
