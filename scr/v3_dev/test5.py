import time
import board
import usb_midi
import digitalio
from analogio import AnalogIn
import adafruit_midi
from adafruit_midi.control_change import ControlChange

# --- CD4051 Control Pins (A = GP15, B = GP14, C = GP13) ---
s0 = digitalio.DigitalInOut(board.GP15)
s1 = digitalio.DigitalInOut(board.GP14)
s2 = digitalio.DigitalInOut(board.GP13)
for pin in [s0, s1, s2]:
    pin.direction = digitalio.Direction.OUTPUT

def select_channel(ch):
    s0.value = ch & 1
    s1.value = (ch >> 1) & 1
    s2.value = (ch >> 2) & 1

# --- ADC Inputs ---
adc_mux = AnalogIn(board.A0)     # GP26 → CD4051
adc_direct1 = AnalogIn(board.A1) # GP27
adc_direct2 = AnalogIn(board.A2) # GP28

# --- MIDI Setup ---
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

def adc_to_midi(value):
    return min(127, max(0, 127 - int((value / 65535) * 127)))

# --- Biến trở: Lưu giá trị MIDI trước đó ---
last_values = [-1] * 9

button_left = digitalio.DigitalInOut(board.GP5)
button_right = digitalio.DigitalInOut(board.GP2)
for button in [button_left, button_right]:
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP  # Nút nối xuống GND

last_left = True
last_right = True

# --- Thêm các nút ở IO0, IO1, IO3, IO4, IO6, IO7 ---
button_pins = [board.GP0, board.GP1, board.GP3, board.GP4, board.GP6, board.GP7]
buttons = []
last_button_states = []

for pin in button_pins:
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    buttons.append(btn)
    last_button_states.append(True)  # True nghĩa là chưa bấm

# --- MAIN LOOP ---
while True:
    # Đọc biến trở CD4051: channel 1 đến 7 → CC 1 đến 7
    for i, ch in enumerate(range(1, 8)):
        select_channel(ch)
        time.sleep(0.002)  # CD4051 ổn định
        raw = adc_mux.value
        midi_val = adc_to_midi(raw)

        if midi_val != last_values[i]:
            midi.send(ControlChange(i + 1, midi_val))
            print(f"MIDI CC {i+1}: {midi_val}")
            last_values[i] = midi_val

    # Biến trở trực tiếp 1 → CC 8
    raw = adc_direct1.value
    midi_val = adc_to_midi(raw)
    if midi_val != last_values[7]:
        midi.send(ControlChange(8, midi_val))
        print(f"MIDI CC 8: {midi_val}")
        last_values[7] = midi_val

    # Biến trở trực tiếp 2 → CC 9
    raw = adc_direct2.value
    midi_val = adc_to_midi(raw)
    if midi_val != last_values[8]:
        midi.send(ControlChange(9, midi_val))
        print(f"MIDI CC 9: {midi_val}")
        last_values[8] = midi_val

    # --- Mô phỏng encoder vô cực bằng nút ---
    current_left = button_left.value
    current_right = button_right.value

    if not current_left and last_left:
        midi.send(ControlChange(10, 127))  # Giảm
        print("Encoder Left → MIDI CC 10: -1")

    if not current_right and last_right:
        midi.send(ControlChange(10, 1))  # Tăng
        print("Encoder Right → MIDI CC 10: +1")

    last_left = current_left
    last_right = current_right

    # --- Gửi MIDI khi nhấn các nút IO0, IO1, IO3, IO4, IO6, IO7 ---
    for i, btn in enumerate(buttons):
        current_state = btn.value
        if not current_state and last_button_states[i]:  # Phát hiện cạnh xuống
            midi.send(ControlChange(20 + i, 127))  # CC 20 → 25, giá trị 127 = nhấn
            print(f"Nút GP{i if i < 2 else i+1}: MIDI CC {20 + i} = 127")
        elif current_state and not last_button_states[i]:  # Phát hiện nhả nút
            midi.send(ControlChange(20 + i, 0))  # Trả về 0 khi nhả
            print(f"Nút GP{i if i < 2 else i+1} nhả: MIDI CC {20 + i} = 0")
        last_button_states[i] = current_state

    time.sleep(0.01)  # Debounce đơn giản

