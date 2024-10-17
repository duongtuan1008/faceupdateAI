import cv2
import pickle
from picamera2 import Picamera2
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time
import multiprocessing
from email.message import EmailMessage
import mimetypes
import smtplib
from RPLCD.i2c import CharLCD

# Cấu hình GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
TILT_PIN = 24
RELAY_PIN = 17
PIR_PIN = 18
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(TILT_PIN, GPIO.IN)
GPIO.setup(RELAY_PIN, GPIO.OUT)
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)

# Định nghĩa chân GPIO cho hàng và cột
ROW_PINS = [6, 13, 19, 26]  # Các chân cho hàng R1, R2, R3, R4
COL_PINS = [12, 16, 20, 21]  # Các chân cho cột C1, C2, C3, C4

# khai bao sender_email Reciever_Email và pass_sender 
Sender_email = "duongtuan10082003@gmail.com"
Reciever_Email = "duongtuan1008@gmail.com"
pass_sender = "vrrw tsqa aljl nbrk"
face_recognition_threshold = 0.45  # Bạn có thể điều chỉnh ngưỡng này
camera_on = multiprocessing.Value('b', False)
password = "11111"
pass_def = "12345"
mode_changePass = '*#01#'
mode_resetPass = '*#02#'
password_input = multiprocessing.Manager().list()
new_pass1 = [''] * 5
new_pass2 = [''] * 5
data_input = multiprocessing.Manager().list()
x = multiprocessing.Value('i', 0)
prevTime = multiprocessing.Value('d', 0.0)
motion_detected_time = multiprocessing.Value('d', 0.0)
doorUnlock = multiprocessing.Value('b', False)
is_checking_password = multiprocessing.Value('b', False)
picam2 = Picamera2()
picam2.start()  # Bật camera ngay lập tức
haarcascade_path = '/home/Tun/Desktop/FacePass2/haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haarcascade_path)
if face_cascade.empty():
    print("Không thể tải mô hình Haar Cascade.")
    exit()

# Đọc mô hình đã huấn luyện từ tệp
try:
    with open('face_recognition_model.pkl', 'rb') as model_file:
        clf = pickle.load(model_file)
except FileNotFoundError:
    print("Tệp mô hình nhận diện khuôn mặt không tồn tại.")
    exit()

# Đọc dữ liệu khuôn mặt đã lưu
try:
    with open('dataset_faces.dat', 'rb') as file:
        all_face_encodings = pickle.load(file)
except FileNotFoundError:
    print("Tệp dữ liệu khuôn mặt không tồn tại.")
    exit()

# Chuyển đổi từ điển thành danh sách các encoding và ID
known_face_encodings = list(all_face_encodings.values())
known_face_ids = list(all_face_encodings.keys())
# Tải mô hình Haar Cascade để nhận diện khuôn mặt
haarcascade_path = '/home/Tun/Desktop/FacePass2/haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haarcascade_path)
# Bảng bàn phím 4x4
KEYPAD = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Thiết lập GPIO cho các chân hàng và cột
for row in ROW_PINS:
    GPIO.setup(row, GPIO.OUT)
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
        data1[i] = data2[i]

# Hàm so sánh hai danh sách dữ liệu
def compareData(data1=[], data2=[]):
    for i in range(5):
        if data1[i] != data2[i]:
            return False
    return True

# Hàm xóa dữ liệu đầu vào
def clear_data_input(data_input, lcd):
    data_input[:] = []
    for i in range(5):
        lcd.cursor_pos = (1, 6 + i)
        lcd.write_string(' ')  # Xóa từng ký tự bằng cách in khoảng trắng
    lcd.cursor_pos = (1, 6)  # Đặt lại con trỏ về vị trí ban đầu

# Hàm ghi mật khẩu mới vào EEPROM (giả lập)
def writeEpprom(new_pass):
    print(f"Ghi mật khẩu mới vào EEPROM: {new_pass}")

# Hàm đọc từng dòng của bàn phím
def read_line(row, data_input, x, lcd):
    lcd.cursor_pos = (0, 1)
    lcd.write_string("Enter Password")
    GPIO.output(row, GPIO.HIGH)
    for i, col in enumerate(COL_PINS):
        if GPIO.input(col) == GPIO.HIGH:
            key = KEYPAD[ROW_PINS.index(row)][i]
            if len(data_input) < 5:
                data_input.append(key)
                lcd.cursor_pos = (1, 6 + x.value)
                lcd.write_string(key)
                time.sleep(0.3)
                lcd.cursor_pos = (1, 6 + x.value)
                lcd.write_string("*")
                x.value += 1
            else:
                print(f"Đã nhập đủ: {''.join(data_input)}")
    GPIO.output(row, GPIO.LOW)

# Hàm kiểm tra mật khẩu
def check_pass(password, data_input, is_checking_password, lcd):
    while True:
        if len(data_input) < 5:
            for row in ROW_PINS:
                read_line(row, data_input, x, lcd)
            print(f'Dữ liệu đầu vào: {data_input}')
            time.sleep(0.1)
        else:
            is_checking_password.value = True
            password_input = ''.join(data_input)
            print(f'Nhập mật khẩu: {password_input}')

            if password_input == password:
                print('Mật khẩu đúng!')
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                time.sleep(5)
                GPIO.output(RELAY_PIN, GPIO.LOW)
            else:
                print('Mật khẩu không đúng!')
                GPIO.output(RELAY_PIN, GPIO.LOW)

            is_checking_password.value = False
            clear_data_input(data_input, lcd)

# Hàm phát hiện chuyển động và bật camera
def motion_detection(camera_on, motion_detected_time, picam2):
    while True:
        if GPIO.input(PIR_PIN):
            if not camera_on.value:
                picam2.start()
                camera_on.value = True
                motion_detected_time.value = time.time()
                print("Phát hiện chuyển động, bật camera...")
            else:
                motion_detected_time.value = time.time()

        if camera_on.value and time.time() - motion_detected_time.value > 10:
            picam2.stop()
            camera_on.value = False
            print("Không có chuyển động trong 10 giây, tắt camera...")
        time.sleep(0.1)

# Hàm nhận diện khuôn mặt
def recognize_faces():
    global doorUnlock, camera_on, is_checking_password
    no_face_detected_time = 0
    while True:
        if camera_on and not is_checking_password:
            # Ch?p frame t? Picamera2
            frame = picam2.capture_array()

            # Chuy?n d?i frame sang d?nh d?ng BGR
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Chuy?n frame sang ?nh xám d? nh?n di?n khuôn m?t
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

            # Phát hi?n khuôn m?t trong ?nh
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    # C?t khuôn m?t t? frame
                    face_image = frame[y:y + h, x:x + w]
                    face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

                    # Trích xu?t d?c trung khuôn m?t
                    face_encoding = face_recognition.face_encodings(face_rgb)

                    if len(face_encoding) > 0:  # Ki?m tra xem có encoding không
                        # S? d?ng mô hình dã hu?n luy?n d? d? doán ngu?i dùng
                        prediction = clf.predict([face_encoding[0]])
                        predicted_name = prediction[0]  # L?y tên t? d? doán mô hình

                        # So sánh v?i các encoding dã luu trong dataset
                        distances = face_recognition.face_distance(known_face_encodings, face_encoding[0])
                        best_match_index = np.argmin(distances)  # L?y ch? s? c?a kho?ng cách nh? nh?t

                        # Ki?m tra kho?ng cách có nh? hon ngu?ng không
                        if distances[best_match_index] < face_recognition_threshold:
                            dataset_name = known_face_ids[best_match_index]
                        else:
                            dataset_name = "Unknown"

                        # K?t h?p c? mô hình và so sánh kho?ng cách
                        if predicted_name == dataset_name and predicted_name != "Unknown":
                            print(f"M? khóa c?a cho ngu?i dùng: {predicted_name}")
                            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Kích ho?t relay d? m? c?a
                            prevTime = time.time()  # Luu th?i gian hi?n t?i
                            doorUnlock = True  # Ð?t tr?ng thái c?a m? là True
                        else:
                            # N?u không phát hi?n khuôn m?t trong 10 giây, yêu c?u nh?p m?t kh?u
                            print("Không phát hi?n khuôn m?t. Nh?p m?t kh?u d? m? c?a.")
                            # T?o lu?ng m?i d? th?c hi?n hàm nh?p m?t kh?u
                              
                        # Hi?n th? ID trên khung hình
                        cv2.putText(frame_bgr, predicted_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    
            else:
                print("Không phát hi?n khuôn m?t. C?a khóa.")
                # is_checking_password = True  # Ð?t c? ki?m tra m?t kh?u
                # check_pass()  # G?i hàm ki?m tra m?t kh?u
                # # GPIO.output(RELAY_PIN, GPIO.LOW)
            # Khóa c?a sau 5 giây n?u c?a dang m?
            if doorUnlock and time.time() - prevTime > 5:
                doorUnlock = False  # Ð?t tr?ng thái c?a m? là False
                GPIO.output(RELAY_PIN, GPIO.LOW)  # T?t relay d? khóa c?a
                print("C?a dã khóa")
            # Hi?n th? frame v?i các khuôn m?t du?c dánh d?u
            cv2.imshow("Camera - Face Detection and Recognition", frame_bgr)

            # Nh?n 'q' d? thoát
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
# Khởi tạo camera và các thông số
picam2 = Picamera2()
picam2.start()

haarcascade_path = '/home/Tun/Desktop/FacePass2/haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haarcascade_path)

try:
    with open('face_recognition_model.pkl', 'rb') as model_file:
        clf = pickle.load(model_file)
except FileNotFoundError:
    print("Tệp mô hình không tồn tại.")
    exit()

try:
    with open('dataset_faces.dat', 'rb') as file:
        all_face_encodings = pickle.load(file)
except FileNotFoundError:
    print("Tệp dữ liệu khuôn mặt không tồn tại.")
    exit()

known_face_encodings = list(all_face_encodings.values())
known_face_ids = list(all_face_encodings.keys())

# Khởi tạo các tiến trình
motion_process = multiprocessing.Process(target=motion_detection, args=(camera_on, motion_detected_time, picam2))
face_process = multiprocessing.Process(target=recognize_faces, args=(camera_on, picam2, face_cascade, clf, known_face_encodings, known_face_ids, face_recognition_threshold, prevTime, doorUnlock))
password_process = multiprocessing.Process(target=check_pass, args=(password, data_input, is_checking_password, lcd))
read_pass = multiprocessing.Process(target=read_line,args=(row, data_input, x, lcd))
# Chạy các tiến trình
motion_process.start()
face_process.start()
password_process.start()
read_pass.start()

# Đợi các tiến trình hoàn thành
motion_process.join()
face_process.join()
read_pass.join()

# Dừng camera và giải phóng tài nguyên
picam2.stop()
GPIO.output(RELAY_PIN, GPIO.LOW)
cv2.destroyAllWindows()
