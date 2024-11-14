from machine import Pin
import time

# Khai báo chân LED tích hợp
led = Pin(25, Pin.OUT)

while True:
    led.value(1)  # Bật LED
    time.sleep(0.5)  # Giữ LED sáng trong 1 giây
    led.value(0)  # Tắt LED
    time.sleep(0.5)  # Giữ LED tắt trong 1 giây
