import time
import board
import usb_midi
from analogio import AnalogIn
import digitalio
import adafruit_midi
from adafruit_midi.control_change import ControlChange

# Thiết lập chân điều khiển CD4051: A = GP15, B = GP14, C = GP13
s0 = digitalio.DigitalInOut(board.GP15)  # A (S1)
s1 = digitalio.DigitalInOut(board.GP14)  # B (S2)
s2 = digitalio.DigitalInOut(board.GP13)  # C (S3)
control_pins = [s0, s1, s2]

for pin in control_pins:
    pin.direction = digitalio.Direction.OUTPUT

# Cấu hình ADC:
adc_mux = AnalogIn(board.A0)     # GP26: đầu vào từ CD4051
adc_direct1 = AnalogIn(board.A1) # GP27: biến trở trực tiếp 1
adc_direct2 = AnalogIn(board.A2) # GP28: biến trở trực tiếp 2

# Thiết lập MIDI USB
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

# Hàm chọn kênh CD4051 (0–7)
def select_channel(channel):
    s0.value = channel & 0b0001       # bit 0 -> A (S1)
    s1.value = (channel >> 1) & 0b1   # bit 1 -> B (S2)
    s2.value = (channel >> 2) & 0b1   # bit 2 -> C (S3)

# Hàm chuyển giá trị ADC sang MIDI (0–127)
def adc_to_midi(value):
    return 127 - int(value / 65535 * 127)

# Lưu giá trị trước đó để phát hiện thay đổi
last_values = [-1] * 10  # 8 qua CD4051 + 2 trực tiếp

while True:
    # Đọc 8 biến trở qua CD4051
    for channel in range(8):
        select_channel(channel)
        time.sleep(0.001)
        raw_value = adc_mux.value
        midi_value = adc_to_midi(raw_value)

        if midi_value != last_values[channel]:
            print(f"MIDI CC {channel + 1}: {midi_value}")
            midi.send(ControlChange(channel + 1, midi_value))
            last_values[channel] = midi_value

    # Đọc 2 biến trở trực tiếp
    raw_value = adc_direct1.value
    midi_value = adc_to_midi(raw_value)
    if midi_value != last_values[8]:
        print(f"MIDI CC 9: {midi_value}")
        midi.send(ControlChange(9, midi_value))
        last_values[8] = midi_value

    raw_value = adc_direct2.value
    midi_value = adc_to_midi(raw_value)
    if midi_value != last_values[9]:
        print(f"MIDI CC 10: {midi_value}")
        midi.send(ControlChange(10, midi_value))
        last_values[9] = midi_value

    time.sleep(0.01)
