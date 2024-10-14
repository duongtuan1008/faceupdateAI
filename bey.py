import RPi.GPIO as GPIO
import time

# Cấu hình GPIO cho relay
RELAY_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)  # Mặc định là tắt relay

# Cấu hình ma trận phím 4x4
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

# Các chân GPIO của ma trận phím
ROW_PINS = [26, 19, 13, 6]  # Chân hàng của ma trận phím
COL_PINS = [12, 16, 20, 21]  # Chân cột của ma trận phím

# Thiết lập chân hàng là đầu ra
for row in ROW_PINS:
    GPIO.setup(row, GPIO.OUT)
    GPIO.output(row, GPIO.HIGH)

# Thiết lập chân cột là đầu vào
for col in COL_PINS:
    GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Trạng thái relay ban đầu
relay_on = False

def check_keypad():
    global relay_on
    for i in range(4):  # Kiểm tra từng hàng
        # Bật hàng i
        GPIO.output(ROW_PINS[i], GPIO.LOW)

        for j in range(4):  # Kiểm tra từng cột
            if GPIO.input(COL_PINS[j]) == GPIO.HIGH:  # Nếu phím được nhấn
                key = KEYPAD[i][j]
                print_key(key)  # Gọi hàm xử lý phím nhấn

        # Tắt hàng i
        GPIO.output(ROW_PINS[i], GPIO.HIGH)

def print_key(key):
    global relay_on

    # Nhấn phím "1" để bật relay
    if key == "1" and not relay_on:
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        relay_on = True

        print("Relay bật")

    # Nhấn phím "0" để tắt relay
    elif key == "0" and relay_on:
        GPIO.output(RELAY_PIN, GPIO.LOW)
        relay_on = False
        print("Relay tắt")

    # Thêm chức năng cho các phím khác nếu cần thiết
    if key == "*":
        print("Phím đặc biệt * được nhấn.")
    elif key == "#":
        print("Phím đặc biệt # được nhấn.")

try:
    while True:
        check_keypad()  # Kiểm tra ma trận phím
        time.sleep(0.1)  # Chờ để xử lý nhấn phím
except KeyboardInterrupt:
    print("Kết thúc chương trình")
finally:
    GPIO.cleanup()
