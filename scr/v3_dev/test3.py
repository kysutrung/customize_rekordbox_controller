import time
import board
import digitalio
import usb_midi
from analogio import AnalogIn
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

# --- Bảng bit hiển thị số (Q7-Q1 = A–G) ---
SEGMENTS = {
    0: 0b11111100,
    1: 0b01100000,
    2: 0b11011010,
    3: 0b11110010,
    4: 0b01100110,
    5: 0b10110110,
    6: 0b10111110,
    7: 0b11100000,
    8: 0b11111110,
    9: 0b11110110,
    10: 0b11101110,
    11: 0b10011100,
    12: 0b10001110,
    13: 0b00011100,
    14: 0b11001110,
    15: 0b01111100,
    16: 0b01101110
}

MODE_VAR = 0

# --- Ánh xạ MODE_VAR sang CC number cho biến trở đầu tiên ---
CC_MAP = [20, 21, 22, 23, 24, 25, 26, 27, 28]

# --- Shift Register ---
class ShiftRegister:
    def __init__(self, stcp, shcp, ds):
        self.latch = digitalio.DigitalInOut(stcp)
        self.clock = digitalio.DigitalInOut(shcp)
        self.data = digitalio.DigitalInOut(ds)
        for pin in [self.latch, self.clock, self.data]:
            pin.direction = digitalio.Direction.OUTPUT
            pin.value = False

    def write_byte(self, value):
        self.latch.value = False
        for i in range(8):  # LSB first
            self.clock.value = False
            self.data.value = (value >> i) & 1
            self.clock.value = True
        self.latch.value = True

# --- Khởi tạo shift register ---
sr2 = ShiftRegister(board.GP9, board.GP10, board.GP11)
sr3 = ShiftRegister(board.GP16, board.GP17, board.GP18)
sr1 = ShiftRegister(board.GP19, board.GP20, board.GP21)

def light_ic1_led(index):
    if 0 <= index <= 7:
        value = 1 << index
    else:
        value = 0x00
    sr1.write_byte(value)

def display_number_on_led(ic_index, number):
    value = SEGMENTS.get(number, 0x00)
    if ic_index == 2:
        sr2.write_byte(value)
    elif ic_index == 3:
        sr3.write_byte(value)

def create_button(pin):
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    return btn

def handle_button_press(button, last_state):
    current_state = button.value
    if not current_state and last_state:
        return True, current_state
    return False, current_state

# --- MIDI setup ---
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

def send_midi_note_on(note, velocity=64):
    midi.send(NoteOn(note, velocity))

def send_midi_note_off(note, velocity=64):
    midi.send(NoteOff(note, velocity))

def adc_to_midi(value):
    return min(127, max(0, 127 - int((value / 65535) * 127)))

def get_note_number(mode, button_index):
    return 12 * mode + button_index

mode_button = create_button(board.GP8)
last_mode_button_state = True

button_pins = [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7]
buttons = [create_button(pin) for pin in button_pins]
last_states = [True] * 8

def mode_display(mode_num):
    display = [(14, 13), (14, 0), (13, 0), (16, 11), (14, 10), (12, 1), (12, 2), (11, 12), (13, 14)]
    left, right = display[mode_num] if mode_num < len(display) else (0, 0)
    display_number_on_led(2, left)
    display_number_on_led(3, right)

def key_light_press(gpio_num):
    if MODE_VAR == 4 or MODE_VAR == 0 or MODE_VAR == 3:
        light_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 7, 5: 6, 6: 5, 7: 4}
        if gpio_num in light_map:
            light_ic1_led(light_map[gpio_num])

# --- Biến trở analog ---
s0 = digitalio.DigitalInOut(board.GP15)
s1 = digitalio.DigitalInOut(board.GP14)
s2 = digitalio.DigitalInOut(board.GP13)
for pin in [s0, s1, s2]:
    pin.direction = digitalio.Direction.OUTPUT

def select_channel(ch):
    s0.value = ch & 1
    s1.value = (ch >> 1) & 1
    s2.value = (ch >> 2) & 1

adc_mux = AnalogIn(board.A0)     # GP26
adc_direct1 = AnalogIn(board.A1) # GP27
adc_direct2 = AnalogIn(board.A2) # GP28
last_values = [-1] * 9

# --- Khởi động: chớp đèn nền ---
for i in range(9):
    light_ic1_led(i)
    time.sleep(0.2)

# --- Vòng lặp chính ---
while True:
    mode_display(MODE_VAR)
    
    # Xử lý chuyển chế độ
    pressed, last_mode_button_state = handle_button_press(mode_button, last_mode_button_state)
    if pressed:
        MODE_VAR = (MODE_VAR + 1) % 9
        print("MODE_VAR =", MODE_VAR)

    # Xử lý nút nhấn
    for i, btn in enumerate(buttons):
        current_state = btn.value
        if not current_state and last_states[i]:
            note = get_note_number(MODE_VAR, i)
            print(f"Note ON: {note}")
            key_light_press(7 - i)
            send_midi_note_on(note)
        elif current_state and not last_states[i]:
            note = get_note_number(MODE_VAR, i)
            print(f"Note OFF: {note}")
            light_ic1_led(9)
            send_midi_note_off(note)
        last_states[i] = current_state

    # Đọc biến trở CD4051: channel 1–7 → CC
    for i, ch in enumerate(range(1, 8)):
        select_channel(ch)
        time.sleep(0.002)
        raw = adc_mux.value
        midi_val = adc_to_midi(raw)

        if midi_val != last_values[i]:
            cc_num = CC_MAP[MODE_VAR] if i == 0 else i + 1  # Chỉ biến trở đầu tiên thay đổi theo MODE_VAR
            midi.send(ControlChange(cc_num, midi_val))
            print(f"MIDI CC {cc_num}: {midi_val}")
            last_values[i] = midi_val

    # Biến trở trực tiếp → CC 8
    raw = adc_direct1.value
    midi_val = adc_to_midi(raw)
    if midi_val != last_values[7]:
        midi.send(ControlChange(8, midi_val))
        print(f"MIDI CC 8: {midi_val}")
        last_values[7] = midi_val

    # Biến trở trực tiếp → CC 9
    raw = adc_direct2.value
    midi_val = adc_to_midi(raw)
    if midi_val != last_values[8]:
        midi.send(ControlChange(9, midi_val))
        print(f"MIDI CC 9: {midi_val}")
        last_values[8] = midi_val

    time.sleep(0.01)

