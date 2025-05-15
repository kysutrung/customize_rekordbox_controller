![Photo01](https://github.com/kysutrung/customize_rekordbox_controller/blob/main/mediaaa/repo_cover.jpg)

# DJ Controller for Rekordbox using Raspberry Pi Pico
# Bàn DJ điều khiển phần mềm Rekordbox sử dụng Raspberry Pi Pico

## Introduction | Giới thiệu
This project is a DIY DJ controller that interfaces with Pioneer’s Rekordbox software using the MIDI protocol. The controller is built using a Raspberry Pi Pico and programmed with CircuitPython. It allows users to control Rekordbox features such as tempo adjustment, effects, EQ.....

Dự án hướng tới chế tạo ra một nhạc cụ điện tử điều khiển được phần mềm DJ chuyên dụng Rekordbox. Thiết bị này được cấu tạo với Raspberry Pi Pico là bộ điều khiển trung tâm và được lập trình với thư viện CircuitPython. Cho phép người dùng điều chỉnh được các thông số như EQ, Tempo, Effects, Play, Cue....

## Features | Chức năng cần tạo ra
- USB MIDI communication with Rekordbox | Giao tiếp được với Rekordbox bằng dây USB
- Customizable knob mappings | Tùy chỉnh gán núm vặn, thanh trượt, nút bấm
- CircuitPython-based for easy development | Lập trình được bằng CircuitPython
- Compatible with Windows computers | Chạy được với máy tính Windows

## Hardware Requirements | Phần cứng
- Raspberry Pi Pico | Vi xử lý trung tâm
- Analog Multiplexer | Bộ chia tạo ra thêm các kênh analog
- Potentiometers | Biến trở núm xoay hoặc biến trở thanh trượt
- USB cable (to connect the Pico to a computer) | Cáp usb để kết nối với máy tính

This is electrical diagram | Về cơ bản các linh kiện được đấu như vậy:
![Photo01](https://github.com/kysutrung/customize_rekordbox_controller/blob/main/mediaaa/so_do_noi_day.png)


## Software Requirements | Phần mềm
- [CircuitPython](https://circuitpython.org/) installed on Raspberry Pi Pico
- [Adafruit MIDI Library](https://github.com/adafruit/Adafruit_CircuitPython_MIDI)
- Rekordbox software from Pioneer | Phần mềm Rekordbox (BẢN QUYỀN)

## Installation | Hướng dẫn cài đặt
### 1. Set up CircuitPython Library | Cài thư viện
1. Copy the uf2 file in folder A to the disk of the brand new Raspberry Pi Pico | Copy file có đuôi uf2 ở folder A vào ổ đĩa của bo Raspberry Pico mới mua từ quán về
2. Wait for the board to reboot | Đợi mạch khởi động lại

### 2. Install Program | Nạp code
1. Delete everything on the Raspberry Pico board's hard drive | Xóa hết các thư mục có trong ổ đĩa của bo Pico
2. Copy all the files in folder B to the disk of the Raspberry Pi Pico | Copy hết các thư mục có trong folder B vào ổ đĩa của bo Raspberry Pico

## Usage | Hướng dẫn sử dụng
1. Connect the Raspberry Pi Pico to your computer via USB | Cắm bàn vào máy tính
2. Open Rekordbox and open MIDI menu | Mở menu MIDI ở RekordBox lên (nó nằm ở trên cùng bên tay phải)
3. Map the MIDI controls in Rekordbox to match your hardware layout | Gán nút cho bàn
4. Start mixing and enjoy | Quẩy đê ae ơi

## Troubleshooting | Sửa lỗi
- If the Pico is not recognized as a MIDI device, ensure CircuitPython and the MIDI library are installed correctly.
- Check the USB cable (some cables are power-only and do not support data transfer).
- If controls are not responding, verify that Rekordbox is set to receive MIDI input from the Pico.

