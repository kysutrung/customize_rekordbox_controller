import time
import board
import usb_midi
from analogio import AnalogIn
import adafruit_midi
from adafruit_midi.control_change import ControlChange

# Cấu hình biến trở trên GP26 (ADC0) và GP27 (ADC1)
potentiometer1 = AnalogIn(board.A0)  # Biến trở 1
potentiometer2 = AnalogIn(board.A1)  # Biến trở 2

# Thiết lập MIDI USB
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

# Hàm chuyển đổi giá trị ADC sang giá trị MIDI (0-127)
def adc_to_midi(value):
    return int(value / 65535 * 127)

# Lưu giá trị của các biến trở trước đó
last_value1 = -1
last_value2 = -1

while True:
    # Đọc giá trị từ biến trở 1 và biến trở 2
    raw_value1 = potentiometer1.value
    raw_value2 = potentiometer2.value

    midi_value1 = adc_to_midi(raw_value1)  # Chuyển giá trị từ biến trở 1 thành MIDI
    midi_value2 = adc_to_midi(raw_value2)  # Chuyển giá trị từ biến trở 2 thành MIDI

    # Gửi tín hiệu MIDI nếu giá trị biến trở 1 thay đổi
    if midi_value1 != last_value1:
        print(f"Sending MIDI CC 1: {midi_value1}")
        midi.send(ControlChange(1, midi_value1))  # CC 1 cho biến trở 1
        last_value1 = midi_value1

    # Gửi tín hiệu MIDI nếu giá trị biến trở 2 thay đổi
    if midi_value2 != last_value2:
        print(f"Sending MIDI CC 2: {midi_value2}")
        midi.send(ControlChange(2, midi_value2))  # CC 2 cho biến trở 2
        last_value2 = midi_value2

    time.sleep(0.01)
