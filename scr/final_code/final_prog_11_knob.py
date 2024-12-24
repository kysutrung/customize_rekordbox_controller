import time
import board
import usb_midi
from analogio import AnalogIn
import digitalio
import adafruit_midi
from adafruit_midi.control_change import ControlChange

# Thiết lập các chân điều khiển cho 74HC4067
s0 = digitalio.DigitalInOut(board.GP0)
s1 = digitalio.DigitalInOut(board.GP1)
s2 = digitalio.DigitalInOut(board.GP2)
s3 = digitalio.DigitalInOut(board.GP3)
control_pins = [s0, s1, s2, s3]

for pin in control_pins:
    pin.direction = digitalio.Direction.OUTPUT

# Cấu hình chân ADC
adc = AnalogIn(board.A0)  # GP26 (ADC0)

# Thiết lập MIDI USB
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

# Hàm chọn kênh trên 74HC4067
def select_channel(channel):
    s0.value = channel & 0b0001
    s1.value = (channel & 0b0010) >> 1
    s2.value = (channel & 0b0100) >> 2
    s3.value = (channel & 0b1000) >> 3

# Hàm chuyển đổi giá trị ADC sang giá trị MIDI (0-127)
def adc_to_midi(value):
    return int(value / 65535 * 127)

# Lưu giá trị của các biến trở trước đó
last_values = [-1] * 11  # Mảng cho 11 biến trở

# Vòng lặp chính
while True:
    for channel in range(11):  # Đọc lần lượt từ 11 biến trở
        select_channel(channel)  # Chọn kênh trên 74HC4067
        time.sleep(0.001)  # Đợi tín hiệu ổn định

        raw_value = adc.value  # Đọc giá trị ADC
        midi_value = adc_to_midi(raw_value)  # Chuyển đổi sang giá trị MIDI (0-127)

        # Gửi tín hiệu MIDI nếu giá trị thay đổi
        if midi_value != last_values[channel]:
            print(f"Sending MIDI CC {channel + 1}: {midi_value}")
            midi.send(ControlChange(channel + 1, midi_value))  # CC 1 đến CC 11
            last_values[channel] = midi_value

    time.sleep(0.01)  # Lặp nhanh để cập nhật liên tục
