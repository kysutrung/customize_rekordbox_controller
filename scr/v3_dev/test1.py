import time
import board
import digitalio
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

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
    14: 0b11001110
}

MODE_VAR = 0

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

# --- Khởi tạo shift register cho 2 IC ---
sr2 = ShiftRegister(board.GP9, board.GP10, board.GP11)
sr3 = ShiftRegister(board.GP16, board.GP17, board.GP18)
sr1 = ShiftRegister(board.GP19, board.GP20, board.GP21)

# đèn nền phím
def light_ic1_led(index):
    if 0 <= index <= 7:
        value = 1 << index  # chỉ bit index được bật
    else:
        value = 0x00        # tắt hết nếu sai tham số
    sr1.write_byte(value)


# --- Hiển thị số ---
def display_number_on_led(ic_index, number):
    if 0 <= number <= 14:
        value = SEGMENTS[number]
    else:
        value = 0x00
    if ic_index == 2:
        sr2.write_byte(value)
    elif ic_index == 3:
        sr3.write_byte(value)

# --- Nút nhấn ---
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

# --- MIDI qua USB ---
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

def send_midi_note_on(note, velocity=64):
    midi.send(NoteOn(note, velocity))

def send_midi_note_off(note, velocity=64):
    midi.send(NoteOff(note, velocity))

# --- Hàm tạo mapping note ---
def get_note_number(mode, button_index):
    return 12 * mode + button_index

# --- Khởi tạo nút GP8 chuyển chế độ ---
mode_button = create_button(board.GP8)
last_mode_button_state = True

# --- Tạo các nút GP0–GP7 ---
button_pins = [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7]
buttons = [create_button(pin) for pin in button_pins]
last_states = [True] * 8

# ham hien thi
def mode_display(mode_num):
    if mode_num == 0:
        display_number_on_led(2, 14)
        display_number_on_led(3, 13)
    elif mode_num == 1:
        display_number_on_led(2, 14)
        display_number_on_led(3, 0)
    elif mode_num == 2:
        display_number_on_led(2, 13)
        display_number_on_led(3, 0)
    elif mode_num == 3:
        display_number_on_led(2, 14)
        display_number_on_led(3, 10)
    elif mode_num == 4:
        display_number_on_led(2, 12)
        display_number_on_led(3, 1)
    elif mode_num == 5:
        display_number_on_led(2, 12)
        display_number_on_led(3, 2)
    elif mode_num == 6:
        display_number_on_led(2, 11)
        display_number_on_led(3, 12)
    elif mode_num == 7:
        display_number_on_led(2, 13)
        display_number_on_led(3, 14)
    else:
        display_number_on_led(2, 0)
        display_number_on_led(3, 0)

# den nen phim khi nhan
def key_light_press(gpio_num):
    if MODE_VAR == 3:
        if gpio_num == 0:
            light_ic1_led(0)
        elif gpio_num == 1:
            light_ic1_led(1)
        elif gpio_num == 2:
            light_ic1_led(2)        
        elif gpio_num == 3:
            light_ic1_led(3)
        elif gpio_num == 4:
            light_ic1_led(7)
        elif gpio_num == 5:
            light_ic1_led(6)
        elif gpio_num == 6:
            light_ic1_led(5)
        elif gpio_num == 7:
            light_ic1_led(4) 
        


# khoi dong

for i in range(9):
    light_ic1_led(i)
    time.sleep(0.2)
    

# --- Vòng lặp chính ---
while True:
    # hien thi che do phim nhan
    mode_display(MODE_VAR)
    
    # Nút chuyển chế độ
    pressed, last_mode_button_state = handle_button_press(mode_button, last_mode_button_state)
    if pressed:
        MODE_VAR = (MODE_VAR + 1) % 8
        print("MODE_VAR =", MODE_VAR)


    # Kiểm tra các nút GP0–GP7
    for i, btn in enumerate(buttons):
        current_state = btn.value
        if not current_state and last_states[i]:
            note = get_note_number(MODE_VAR, i)
            print(f"Note ON: {note}")
            key_light_press(7-i)
            send_midi_note_on(note)
        elif current_state and not last_states[i]:
            note = get_note_number(MODE_VAR, i)
            print(f"Note OFF: {note}")
            light_ic1_led(9)
            send_midi_note_off(note)
        last_states[i] = current_state

    time.sleep(0.01)  # chống dội phím

