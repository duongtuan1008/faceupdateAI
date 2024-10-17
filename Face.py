import cv2
import pickle
from picamera2 import Picamera2
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time
import threading
import queue
from email.message import EmailMessage
import mimetypes
import smtplib
import imghdr

# Cấu hình GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
TILT_PIN =24
RELAY_PIN = 17
PIR_PIN=18
GPIO.setup(PIR_PIN,GPIO.IN)
GPIO.setup(TILT_PIN,GPIO.IN)
GPIO.setup(RELAY_PIN, GPIO.OUT)
# Định nghĩa chân GPIO cho hàng và cột
ROW_PINS = [6, 13, 19, 26]  # Các chân cho hàng R1, R2, R3, R4
COL_PINS = [12, 16, 20, 21]  # Các chân cho cột C1, C2, C3, C4

# khai bao sender_email Reciever_Email và pass_sender 
Sender_email = "duongtuan10082003@gmail.com"
Reciever_Email ="duongtuan1008@gmail.com"
pass_sender = "vrrw tsqa aljl nbrk"
# Ngưỡng khoảng cách tối đa để coi là trùng khớp
face_recognition_threshold = 0.45  # Bạn có thể điều chỉnh ngưỡng này
camera_on = False
# Định nghĩa mật khẩu và biến
password = "11111"
pass_def = "12345"
mode_changePass = '*#01#'
mode_resetPass = '*#02#'
password_input = ''
key_queue = queue.Queue()
new_pass1 = [''] * 5
new_pass2 = [''] * 5
data_input = []

# định nghĩa các biến khơi tạo
prevTime = 0  # Biến để theo dõi thời gian trước đó
motion_detected_time = 0
in_num=0
doorUnlock = False  # Trạng thái mở cửa ban đầu là False
is_checking_password = False

# Bảng bàn phím 4x4
KEYPAD = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]


# Thiết lập các chân hàng là output
for row in ROW_PINS:
    GPIO.setup(row, GPIO.OUT)

# Thiết lập các chân cột là input với pull-down resistor
for col in COL_PINS:
    GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


#------------------- xử lý dữ liệu nhập từ matrix phím ---------------------

#get dữ liệu từ bàn phím 
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
    print('nhap mat khau de mo cua')
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
    global password_input, is_checking_password ,Sender_email, pass_sender, Reciever_Email
    while True:
        if len(data_input) < 5:  # Giả sử mật khẩu có 5 ký tự
            for row in ROW_PINS:
                read_line(row)  # Gọi hàm để đọc ký tự từ bàn phím ma trận
            print(f'Dữ liệu đầu vào: {data_input}')  # Kiểm tra quá trình nhập liệu
            time.sleep(0.1)  # Tạm dừng một chút để tránh việc lặp quá nhanh
        else:
            is_checking_password = True  # Đặt cờ là True để cho biết đang kiểm tra mật khẩu
            password_input = ''.join(data_input)
            print(f'Nhập mật khẩu: {password_input}')

            if password_input == password:
                print('Mật khẩu đúng!')
                GPIO.output(RELAY_PIN, GPIO.HIGH)  # Kích hoạt relay
                time.sleep(5)  # Giữ cửa mở trong 5 giây
                GPIO.output(RELAY_PIN, GPIO.LOW)  # Đóng cửa
            elif password_input == mode_changePass:
                changePass()
            elif password_input == mode_resetPass:
                resetPass()
            else:
                print('Mật khẩu không đúng!')
                GPIO.output(RELAY_PIN, GPIO.LOW)  # Tắt relay
                # Gửi email với ảnh đã chụp
                SendEmail(Sender_email, pass_sender, Reciever_Email) 
            is_checking_password = False  # Đặt cờ là False sau khi kiểm tra xong
            clear_data_input()  # Xóa dữ liệu nhập sau khi kiểm tra
# Hàm thay đổi mật khẩu
def changePass():
    global password, new_pass1, new_pass2
    print('--- Đổi mật khẩu ---')
    clear_data_input()

    while True:
        if len(data_input) < 5:  # Giả sử mật khẩu có 4 ký tự
            for row in ROW_PINS:
                read_line(row)  # Gọi hàm để đọc ký tự từ bàn phím ma trận
            print(f'Data input: {data_input}')  # Kiểm tra quá trình nhập liệu
            time.sleep(0.1)  # Tạm dừng một chút để tránh việc lặp quá nhanh
        if isBufferdata(data_input):
            insertData(new_pass1, data_input)
            clear_data_input()
            print("--- Nhập lại mật khẩu ---")
            break
    
    while True:
        if len(data_input) < 5:  # Giả sử mật khẩu có 4 ký tự
            for row in ROW_PINS:
                read_line(row)  # Gọi hàm để đọc ký tự từ bàn phím ma trận
            print(f'Data input: {data_input}')  # Kiểm tra quá trình nhập liệu
            time.sleep(0.1)  # Tạm dừng một chút để tránh việc lặp quá nhanh
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
def resetPass():
    global password
    print('--- Reset Pass ---')
    clear_data_input()

    while True:
        if len(data_input) < 5:  # Giả sử mật khẩu có 4 ký tự
            for row in ROW_PINS:
                read_line(row)  # Gọi hàm để đọc ký tự từ bàn phím ma trận
            print(f'Data input: {data_input}')  # Kiểm tra quá trình nhập liệu
            time.sleep(0.1)  # Tạm dừng một chút để tránh việc lặp quá nhanh
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
                # Gửi email với ảnh đã chụp
                SendEmail(Sender_email, pass_sender, Reciever_Email) 
                clear_data_input()  # Xóa dữ liệu nhập khi sai mật khẩu
                break  # Kết thúc nếu mật khẩu nhập sai
# -------------xử lý dữ liệu từ cảm biến nghiêng --------------
def Tilt_Handle():
    global is_checking_password,Sender_email,Reciever_Email,pass_sender
    tilt_sensor = GPIO.input(TILT_PIN)  # Đọc giá trị từ cảm biến nghiêng
    
    # Kiểm tra nếu không đang kiểm tra mật khẩu và cảm biến ở trạng thái kích hoạt
    if not is_checking_password and tilt_sensor:  
        global i
        i += 1  # Tăng biến đếm ảnh
        
        # Tạo đường dẫn cho ảnh
        image_path = f"/home/Tun/Desktop/FacePass2/image/image_{i}.jpg"
        
        picam2.capture(image_path)  # Chụp ảnh và lưu vào đường dẫn đã tạo
        print('A photo has been taken')  # In thông báo đã chụp ảnh
        
        time.sleep(10)  # Chờ 10 giây trước khi có thể chụp tiếp
        
         

# ------------- send email khi phát hiện xâm nhập -------------
def SendEmail (sender,pass_sender ,receiver):
    # Tạo tên và đường dẫn lưu ảnh
    image_path = f"/home/Tun/Desktop/FacePass2/image/path_to_image.jpg"

    # Chụp ảnh trực tiếp từ camera
    picam2.capture_file(image_path)
    print(f'A photo has been taken and saved at {image_path}')  # Thông báo ảnh đã được chụp
    newMessage = EmailMessage()
    newMessage['Subject'] = "CANH BAO !!!"
    newMessage['From'] = sender
    newMessage['To'] = receiver
    newMessage.set_content('CANH BAO AN NINH')
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
        image_type = imghdr.what(f)
        # Đặt định dạng mặc định là 'jpeg' nếu không xác định được định dạng
        if image_type is None:
            image_type = 'jpeg'
        image_name = f.name
        newMessage.add_attachment(image_data, maintype='image', subtype=image_type, filename=image_name)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, pass_sender)
        smtp.send_message(newMessage)
    print("Email đã được gửi với ảnh đính kèm.")
#-------------- hàm chính -------------------
print("Cửa khóa")
GPIO.output(RELAY_PIN, GPIO.LOW)

# Khởi tạo camera với Picamera2
picam2 = Picamera2()
picam2.start()  # Bật camera ngay lập tức

# Tải mô hình Haar Cascade để nhận diện khuôn mặt
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
# Hàm kiểm tra chuyển động

def motion_detection():
    global camera_on, motion_detected_time
    while True:
        if GPIO.input(PIR_PIN):  # Nếu phát hiện chuyển động
            if not camera_on:
                picam2.start()  # Bật camera
                camera_on = True
                motion_detected_time = time.time()  # Cập nhật thời gian phát hiện chuyển động
                print("Chuyển động phát hiện, bật camera...")
            else:
                motion_detected_time = time.time()  # Cập nhật thời gian nếu vẫn phát hiện chuyển động

        # Kiểm tra xem có chuyển động trong vòng 10 giây không
        if camera_on and time.time() - motion_detected_time > 10:
            picam2.stop()  # Tắt camera nếu không có chuyển động
            camera_on = False
            print("Không có chuyển động trong 10 giây, tắt camera...")
def recognize_faces():
    global doorUnlock, camera_on, is_checking_password
    no_face_detected_time = 0
    while True:
        if camera_on and not is_checking_password:
            # Chụp frame từ Picamera2
            frame = picam2.capture_array()

            # Chuyển đổi frame sang định dạng BGR
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Chuyển frame sang ảnh xám để nhận diện khuôn mặt
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

            # Phát hiện khuôn mặt trong ảnh
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    # Cắt khuôn mặt từ frame
                    face_image = frame[y:y + h, x:x + w]
                    face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

                    # Trích xuất đặc trưng khuôn mặt
                    face_encoding = face_recognition.face_encodings(face_rgb)

                    if len(face_encoding) > 0:  # Kiểm tra xem có encoding không
                        # Sử dụng mô hình đã huấn luyện để dự đoán người dùng
                        prediction = clf.predict([face_encoding[0]])
                        predicted_name = prediction[0]  # Lấy tên từ dự đoán mô hình

                        # So sánh với các encoding đã lưu trong dataset
                        distances = face_recognition.face_distance(known_face_encodings, face_encoding[0])
                        best_match_index = np.argmin(distances)  # Lấy chỉ số của khoảng cách nhỏ nhất

                        # Kiểm tra khoảng cách có nhỏ hơn ngưỡng không
                        if distances[best_match_index] < face_recognition_threshold:
                            dataset_name = known_face_ids[best_match_index]
                        else:
                            dataset_name = "Unknown"

                        # Kết hợp cả mô hình và so sánh khoảng cách
                        if predicted_name == dataset_name and predicted_name != "Unknown":
                            print(f"Mở khóa cửa cho người dùng: {predicted_name}")
                            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Kích hoạt relay để mở cửa
                            prevTime = time.time()  # Lưu thời gian hiện tại
                            doorUnlock = True  # Đặt trạng thái cửa mở là True
                        else:
                            # Nếu không phát hiện khuôn mặt trong 10 giây, yêu cầu nhập mật khẩu
                            print("Không phát hiện khuôn mặt. Nhập mật khẩu để mở cửa.")
                            password_thread = threading.Thread(target=check_pass)
                            password_thread.start()
                            # Tạo luồng mới để thực hiện hàm nhập mật khẩu
                              
                        # Hiển thị ID trên khung hình
                        cv2.putText(frame_bgr, predicted_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    
            else:
                print("Không phát hiện khuôn mặt. Cửa khóa.")
                # is_checking_password = True  # Đặt cờ kiểm tra mật khẩu
                # check_pass()  # Gọi hàm kiểm tra mật khẩu
                # # GPIO.output(RELAY_PIN, GPIO.LOW)
            # Khóa cửa sau 5 giây nếu cửa đang mở
            if doorUnlock and time.time() - prevTime > 5:
                doorUnlock = False  # Đặt trạng thái cửa mở là False
                GPIO.output(RELAY_PIN, GPIO.LOW)  # Tắt relay để khóa cửa
                print("Cửa đã khóa")
            # Hiển thị frame với các khuôn mặt được đánh dấu
            cv2.imshow("Camera - Face Detection and Recognition", frame_bgr)

            # Nhấn 'q' để thoát
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
motion_thread = threading.Thread(target=motion_detection)
face_thread = threading.Thread(target=recognize_faces)
password_thread = threading.Thread(target=check_pass)

password_thread.start()
motion_thread.start()
face_thread.start()

motion_thread.join()
face_thread.join()

# chuong trình chính 

# Giải phóng tài nguyên và đóng các cửa sổ
picam2.stop()  # Dừng camera
GPIO.output(RELAY_PIN, GPIO.LOW)  # Đảm bảo cửa khóa khi dừng camera
cv2.destroyAllWindows()