import RPi.GPIO as GPIO
import time

# Định nghĩa mật khẩu và biến
password = "11111"
pass_def = "12345"
mode_changePass = '*#01#'
mode_resetPass = '*#02#'
password_input = ''
new_pass1 = [''] * 5
new_pass2 = [''] * 5
data_input = []
RELAY_PIN = 17

# Định nghĩa chân GPIO cho hàng và cột
ROW_PINS = [6, 13, 19, 26]  # Các chân cho hàng R1, R2, R3, R4
COL_PINS = [12, 16, 20, 21]  # Các chân cho cột C1, C2, C3, C4

# Bảng bàn phím 4x4
KEYPAD = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Cấu hình GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)

# Thiết lập các chân hàng là output
for row in ROW_PINS:
    GPIO.setup(row, GPIO.OUT)

# Thiết lập các chân cột là input với pull-down resistor
for col in COL_PINS:
    GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Hàm kiểm tra dữ liệu đầu vào
def isBufferdata(data=[]):
    if len(data) < 5:
        return 0
    for i in range(5):
        if data[i] == '\0':
            return 0
    return 1

# Hàm ghi dữ liệu vào biến new_pass1 và new_pass2
def insertData(data1, data2):
    if len(data1) != len(data2):
        print("Lỗi: Kích thước của data1 và data2 không khớp.")
        return  # Thoát nếu kích thước không khớp
    for i in range(len(data1)):
        data1[i] = data2[i]  # Gán giá trị từ data2 vào data1

# Hàm so sánh hai danh sách dữ liệu
def compareData(data1=[], data2=[]):
    for i in range(5):
        if data1[i] != data2[i]:
            return False
    return True

# Hàm xóa dữ liệu đầu vào
def clear_data_input():
    global data_input
    data_input = []

# Hàm ghi mật khẩu mới vào EEPROM (giả lập)
def writeEpprom(new_pass):
    print(f"Ghi mật khẩu mới vào EEPROM: {new_pass}")
    # Thực hiện ghi vào EEPROM ở đây

# Hàm đọc từng dòng của bàn phím
def read_line(row):
    GPIO.output(row, GPIO.HIGH)  # Kích hoạt hàng hiện tại
    for i, col in enumerate(COL_PINS):
        if GPIO.input(col) == 1:
            key_pressed = KEYPAD[ROW_PINS.index(row)][i]  # Lấy ký tự tương ứng
            print(f"Key pressed: {key_pressed}")
            data_input.append(key_pressed)  # Thêm ký tự vào data_input
            time.sleep(0.3)  # Tạm dừng để tránh trùng lặp
    GPIO.output(row, GPIO.LOW)  # Tắt hàng hiện tại

# Hàm kiểm tra mật khẩu
def check_pass():
    global password_input
    password_input = ''.join(data_input)
    print(f'Nhập mật khẩu: {password_input}')

    if password_input == password:
        print('Mật khẩu đúng!')
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Kích hoạt relay
    elif password_input == mode_changePass:
        changePass()
    elif password_input == mode_resetPass:
        resretPass()
    else:
        print('Mật khẩu không đúng!')
        GPIO.output(RELAY_PIN, GPIO.LOW)  # Tắt relay

    clear_data_input()  # Xóa dữ liệu nhập sau khi kiểm tra

# Hàm thay đổi mật khẩu
def changePass():
    global password, new_pass1, new_pass2
    print('--- Đổi mật khẩu ---')
    clear_data_input()

    while True:
        for row in ROW_PINS:
            read_line(row)
        if isBufferdata(data_input):
            insertData(new_pass1, data_input)
            clear_data_input()
            print("--- Nhập lại mật khẩu ---")
            break
    
    while True:
        for row in ROW_PINS:
            read_line(row)
        if isBufferdata(data_input):
            insertData(new_pass2, data_input)
            break

    time.sleep(1)
    if compareData(new_pass1, new_pass2):
        print("--- Mật khẩu khớp ---")
        time.sleep(1)
        writeEpprom(new_pass2)
        password = ''.join(new_pass2)  # Gán mật khẩu mới
    else:
        print("--- Mật khẩu không khớp ---")
# reset lai password
def resretPass():
    global password
    print('--- Reset Pass ---')
    clear_data_input()

    while True:
        for row in ROW_PINS:
            read_line(row)
        if isBufferdata(data_input):  # Kiểm tra xem người dùng đã nhập đủ 5 ký tự
            if compareData(data_input, password):  # So sánh với mật khẩu hiện tại
                clear_data_input()  # Xóa dữ liệu nhập sau khi xác nhận thành công
                print('Mật khẩu đúng, sẵn sàng reset!')

                while True:
                    key = None  # Đặt mặc định key là None để kiểm tra
                    for row in ROW_PINS:
                        GPIO.output(row, GPIO.HIGH)
                        for i, col in enumerate(COL_PINS):
                            if GPIO.input(col) == 1:
                                key = KEYPAD[ROW_PINS.index(row)][i]
                                print(f"Key pressed: {key}")
                                time.sleep(0.3)  # Tránh trùng lặp khi nhấn
                        GPIO.output(row, GPIO.LOW)

                    if key == '#':  # Khi người dùng nhấn phím '#'
                        # Chuyển đổi mật khẩu và mật khẩu mặc định thành danh sách
                        new_default_pass = list(pass_def)  # Chuyển đổi mật khẩu mặc định thành danh sách
                        new_password = list(password)  # Chuyển đổi mật khẩu thành danh sách
                        insertData(new_password, new_default_pass)  # Reset lại mật khẩu mặc định
                        print('--- Reset mật khẩu thành công ---')
                        writeEpprom(pass_def)  # Giả lập ghi vào EEPROM
                        password = ''.join(new_password)  # Chuyển đổi danh sách trở lại chuỗi
                        clear_data_input()  # Xóa dữ liệu nhập
                        return  # Thoát hàm reset sau khi hoàn thành
            else:
                print('Mật khẩu không đúng!')
                clear_data_input()  # Xóa dữ liệu nhập khi sai mật khẩu
                break  # Kết thúc nếu mật khẩu nhập sai
# Chương trình chính
try:
    while True:
        for row in ROW_PINS:
            read_line(row)
        if len(data_input) >= len(password):
            check_pass()  # Kiểm tra mật khẩu khi đủ ký tự
        time.sleep(0.3)

except KeyboardInterrupt:
    print("\nChương trình đã dừng")
finally:
    GPIO.cleanup()  # Dọn dẹp các chân GPIO khi kết thúc chương trình
