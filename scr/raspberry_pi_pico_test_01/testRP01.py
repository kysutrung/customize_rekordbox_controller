from machine import ADC, Pin
from time import sleep

# Khởi tạo chân ADC để đọc tín hiệu từ biến trở
potentiometer = ADC(Pin(26))  # GP26 (ADC0)

while True:
    # Đọc giá trị ADC (0–65535)
    raw_value = potentiometer.read_u16()
    
    # Chuyển đổi giá trị ADC sang điện áp (0–3.3V)
    voltage = raw_value * 3.3 / 65535
    if voltage > 1.3 :
        voltage = 1.3
    # In giá trị thô và điện áp ra màn hình
    print(f"High Channel: {voltage:.2f} V")
    
    sleep(0.1)  # Dừng 100ms trước khi đọc lại
