import cv2
import pickle
from picamera2 import Picamera2
import face_recognition
import numpy as np
import RPi.GPIO as GPIO
import time
import threading

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)
RELAY_PIN = 17
PIR_PIN=18
GPIO.setup(PIR_PIN,GPIO.IN)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Cau hình ma tr?n phím 4x4
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

# Các chân GPIO của ma trận phím
ROW_PINS = [6, 13, 19, 26]  # Chân hàng c?a ma tr?n phím
COL_PINS = [12, 16, 20, 21]  # Chân c?t c?a ma tr?n phím

# Kh?i t?o thu vi?n d? d?c ma tr?n phím
for col in COL_PINS:
    GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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

# Ngưỡng khoảng cách tối đa để coi là trùng khớp
face_recognition_threshold = 0.45  # Bạn có thể điều chỉnh ngưỡng này
prevTime = 0  # Biến để theo dõi thời gian trước đó
doorUnlock = False  # Trạng thái mở cửa ban đầu là False
motion_detected_time = 0
camera_on = False
password[6] = "11111"
data_input[6]
in_num=0

# hàm duyệt matrix phim
def check_keypad():
    global relay_on
    for i in range(4):  # Ki?m tra t?ng hàng
        # B?t hàng i
        GPIO.output(ROW_PINS[i], GPIO.LOW)

        for j in range(4):  # Ki?m tra t?ng c?t
            if GPIO.input(COL_PINS[j]) == GPIO.HIGH:  # N?u phím du?c nh?n
                key = KEYPAD[i][j]
                print_key(key)  # G?i hàm x? lý phím nh?n

        # T?t hàng i
        GPIO.output(ROW_PINS[i], GPIO.HIGH)


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
    global doorUnlock, camera_on
    while True:
        if camera_on:
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
                            print("Không khớp giữa mô hình và dataset. Cửa khóa.")
                            # GPIO.output(RELAY_PIN, GPIO.LOW)

                        # Hiển thị ID trên khung hình
                        cv2.putText(frame_bgr, predicted_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    
            else:
                print("Không phát hiện khuôn mặt. Cửa khóa.")
                # GPIO.output(RELAY_PIN, GPIO.LOW)
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

motion_thread.start()
face_thread.start()

motion_thread.join()
face_thread.join()

# Giải phóng tài nguyên và đóng các cửa sổ
picam2.stop()  # Dừng camera
GPIO.output(RELAY_PIN, GPIO.LOW)  # Đảm bảo cửa khóa khi dừng camera
cv2.destroyAllWindows()