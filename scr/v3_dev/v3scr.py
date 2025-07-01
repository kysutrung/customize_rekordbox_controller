import time
import board
import digitalio
import usb_midi
from analogio import AnalogIn
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

# -------------------- Cấu hình hiển thị LED 7 đoạn --------------------
SEGMENTS = {
    0: 0b11111100,  1: 0b01100000,  2: 0b11011010,  3: 0b11110010,
    4: 0b01100110,  5: 0b10110110,  6: 0b10111110,  7: 0b11100000,
    8: 0b11111110,  9: 0b11110110, 10: 0b11101110, 11: 0b10011100,
    12: 0b10001110, 13: 0b00011100, 14: 0b11001110, 15: 0b01111100,
    16: 0b01101110
}

# -------------------- Biến toàn cục --------------------
MODE_VAR = 0
CC_MAP = [20, 21, 22, 23, 24, 25, 26, 27, 28]
last_values = [-1] * 9  # MIDI CC cache

# Delta Control
cc1_value, cc10_value = 64, 64
ref_adc1 = ref_adc10 = None
prev_button1 = prev_button2 = True

# Encoder State
last_encoder_left = last_encoder_right = True

# -------------------- Cấu hình Shift Register --------------------
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
        for i in range(8):
            self.clock.value = False
            self.data.value = (value >> i) & 1
            self.clock.value = True
        self.latch.value = True

# IC LED
sr1 = ShiftRegister(board.GP19, board.GP20, board.GP21)
sr2 = ShiftRegister(board.GP9, board.GP10, board.GP11)
sr3 = ShiftRegister(board.GP16, board.GP17, board.GP18)

def light_ic1_led(index):
    sr1.write_byte(1 << index if 0 <= index <= 7 else 0x00)
    
def light_ic1_leds(indices):
    bitmask = 0x00
    for idx in indices:
        if 0 <= idx <= 7:
            bitmask |= 1 << idx
    sr1.write_byte(bitmask)

def display_number_on_led(ic_index, number):
    value = SEGMENTS.get(number, 0x00)
    if ic_index == 2:
        sr2.write_byte(value)
    elif ic_index == 3:
        sr3.write_byte(value)

# -------------------- MIDI và ADC --------------------
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

def send_midi_note_on(note, velocity=127):
    midi.send(NoteOn(note, velocity))

def send_midi_note_off(note, velocity=0):
    midi.send(NoteOff(note, velocity))

def adc_to_midi(value):
    return max(0, min(127, 127 - int((value / 65535) * 127)))

# -------------------- Multiplexer --------------------
s0, s1, s2 = digitalio.DigitalInOut(board.GP15), digitalio.DigitalInOut(board.GP14), digitalio.DigitalInOut(board.GP13)
for s in (s0, s1, s2):
    s.direction = digitalio.Direction.OUTPUT

def select_channel(ch):
    s0.value, s1.value, s2.value = ch & 1, (ch >> 1) & 1, (ch >> 2) & 1

adc_mux = AnalogIn(board.A0)
adc_direct1 = AnalogIn(board.A1)
adc_direct2 = AnalogIn(board.A2)

# -------------------- Button & Mode --------------------
def create_button(pin):
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    return btn

def handle_button_press(button, last_state):
    current = button.value
    return (not current and last_state), current

mode_button = create_button(board.GP8)
last_mode_button_state = True

button_pins = [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7]
buttons = [create_button(pin) for pin in button_pins]
last_states = [True] * len(buttons)

# GP mapping
delta_button1 = buttons[0]  # GP0
delta_button2 = buttons[3]  # GP2
encoder_button_left = buttons[5]  # GP5
encoder_button_right = buttons[2] # GP2 (dual function)

# -------------------- Display chế độ --------------------
def mode_display(mode):
    pattern = [(14,13), (14,0), (13,0), (16,11), (14,10), (12,1), (12,2), (11,12), (13,14)]
    left, right = pattern[mode] if mode < len(pattern) else (0, 0)
    display_number_on_led(2, left)
    display_number_on_led(3, right)

# -------------------- MIDI Logic --------------------
def get_note_number(mode, index):
    return 12 * mode + index

def handle_delta_control(raw_adc, cc_num, value_ref, ref_adc, prev_state, button_pressed):
    if button_pressed and not prev_state:
        ref_adc = raw_adc
    if button_pressed and ref_adc is not None:
        delta = int((ref_adc - raw_adc) / 512)
        if abs(delta) >= 1:
            new_val = max(0, min(127, value_ref + delta))
            if new_val != value_ref:
                midi.send(ControlChange(cc_num, new_val))
                print(f"Delta CC{cc_num} = {new_val}")
                value_ref = new_val
                ref_adc = raw_adc
    return value_ref, ref_adc, button_pressed

# đèn phím
def key_light_press(gpio_num):
    if MODE_VAR in (0, 3, 4):
        mapping = {0: 0, 1: 1, 2: 2, 3: 3, 4: 7, 5: 6, 6: 5, 7: 4}
        light_ic1_led(mapping.get(gpio_num, 9))
        
        
def key_light_still():
    if MODE_VAR == 1:
        light_ic1_leds([4, 7])
    elif MODE_VAR == 2:
        light_ic1_leds([2, 4, 5, 6, 7])
    elif MODE_VAR == 8:
        light_ic1_leds([0, 1, 2, 3, 4, 6])
    else:
        light_ic1_leds([8])

last_mode_var = -1

# -------------------- Khởi động --------------------
for i in range(9):
    light_ic1_led(i)
    time.sleep(0.15)

# -------------------- Main loop --------------------
while True:
    # đèn đóm
    mode_display(MODE_VAR)
    if MODE_VAR != last_mode_var:
        key_light_still()
        last_mode_var = MODE_VAR
    # Xử lý chuyển chế độ
    pressed, last_mode_button_state = handle_button_press(mode_button, last_mode_button_state)
    if pressed:
        MODE_VAR = (MODE_VAR + 1) % 9
        print(f">>> MODE_VAR = {MODE_VAR}")

    # Xử lý nút nhấn
    for i, btn in enumerate(buttons):
        current = btn.value
        if not current and last_states[i]:
            if not (MODE_VAR == 1 and i in (0, 2)):  # GP0, GP2 dùng cho delta control
                note = get_note_number(MODE_VAR, i)
                send_midi_note_on(note)
                print(f"Note ON: {note}")
                key_light_press(7 - i)
        elif current and not last_states[i]:
            if not (MODE_VAR == 1 and i in (0, 2)):
                note = get_note_number(MODE_VAR, i)
                send_midi_note_off(note)
                print(f"Note OFF: {note}")
                if MODE_VAR != 1 and MODE_VAR !=2 and MODE_VAR != 8:
                    light_ic1_led(9)
        last_states[i] = current

    # Đọc MUX (CC1–CC7)
    for i, ch in enumerate(range(1, 8)):
        select_channel(ch)
        time.sleep(0.002)
        raw = adc_mux.value
        midi_val = adc_to_midi(raw)

        if i == 0 and MODE_VAR == 1:
            b1 = not delta_button1.value
            b2 = not delta_button2.value
            cc1_value, ref_adc1, prev_button1 = handle_delta_control(raw, 1, cc1_value, ref_adc1, prev_button1, b1)
            cc10_value, ref_adc10, prev_button2 = handle_delta_control(raw, 30, cc10_value, ref_adc10, prev_button2, b2)
        elif midi_val != last_values[i]:
            cc = CC_MAP[MODE_VAR] if i == 0 else i + 1
            midi.send(ControlChange(cc, midi_val))
            print(f"CC {cc} = {midi_val}")
            last_values[i] = midi_val

    # Analog trực tiếp → CC8, CC9
    for idx, adc, cc_num in [(7, adc_direct1, 8), (8, adc_direct2, 9)]:
        raw = adc.value
        midi_val = adc_to_midi(raw)
        if midi_val != last_values[idx]:
            midi.send(ControlChange(cc_num, midi_val))
            print(f"CC {cc_num} = {midi_val}")
            last_values[idx] = midi_val

    # Mô phỏng encoder khi MODE_VAR == 2
    if MODE_VAR == 2:
        l_state = encoder_button_left.value
        r_state = encoder_button_right.value

        if not l_state and last_encoder_left:
            midi.send(ControlChange(10, 127))  # Giảm
            print("Encoder LEFT → CC10: -1")

        if not r_state and last_encoder_right:
            midi.send(ControlChange(10, 1))  # Tăng
            print("Encoder RIGHT → CC10: +1")

        last_encoder_left = l_state
        last_encoder_right = r_state

    time.sleep(0.01)

