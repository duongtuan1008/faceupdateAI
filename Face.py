import cv2
import pickle
from picamera2 import Picamera2
import face_recognition
import RPi.GPIO as GPIO
import time

# Cấu hình GPIO cho cảm biến chuyển động PIR
PIR_PIN = 18  # Pin kết nối với cảm biến chuyển động
RELAY = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(RELAY, GPIO.OUT)
GPIO.output(RELAY, GPIO.LOW)

# Khởi tạo camera với Picamera2
picam2 = Picamera2()

# Tải mô hình Haar Cascade để nhận diện khuôn mặt
haarcascade_path = '/home/Tun/Desktop/FacePass2/haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haarcascade_path)

if face_cascade.empty():
    print("Không thể tải mô hình Haar Cascade.")
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

# Biến theo dõi thời gian phát hiện chuyển động
motion_detected_time = 0
camera_on = False
unlock_start_time = None  # Biến để theo dõi thời gian mở khóa

while True:
    # Kiểm tra trạng thái cảm biến PIR
    if GPIO.input(PIR_PIN):  # Nếu phát hiện chuyển động
        if not camera_on:
            picam2.start()  # Bật camera
            camera_on = True
            print("Chuyển động phát hiện, bật camera...")
        
        # Cập nhật thời gian phát hiện chuyển động
        motion_detected_time = time.time()
    
    # Nếu không có chuyển động sau 10 giây, tắt camera
    elif camera_on and time.time() - motion_detected_time > 10:
        picam2.stop()  # Tắt camera
        camera_on = False
        print("Không có chuyển động trong 10 giây, tắt camera...")

    # Nếu camera đang bật, thực hiện nhận diện khuôn mặt
    if camera_on:
        # Chụp frame từ Picamera2
        frame = picam2.capture_array()

        # Chuyển đổi frame sang định dạng BGR
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Chuyển frame sang ảnh xám để nhận diện khuôn mặt
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # Phát hiện khuôn mặt trong ảnh
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Vẽ hình chữ nhật quanh các khuôn mặt được phát hiện và nhận diện
        for (x, y, w, h) in faces:
            cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Cắt khuôn mặt từ frame
            face_image = frame[y:y+h, x:x+w]
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

            # Trích xuất đặc trưng khuôn mặt
            face_encoding = face_recognition.face_encodings(face_rgb)

            if len(face_encoding) > 0:  # Kiểm tra xem có encoding không
                # So sánh với các encoding đã lưu
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding[0])
                name = "Unknown"
                # Nếu có số trùng khớp, lấy ID tương ứng
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_ids[first_match_index]

                    # Kích hoạt relay để mở khóa cửa
                    if not GPIO.input(RELAY):  # Kiểm tra nếu relay đang tắt
                        GPIO.output(RELAY, GPIO.HIGH)  # Kích hoạt relay
                        print(f"Mở khóa cửa cho người dùng: {name}")

                        # Ghi lại thời gian mở khóa
                        unlock_start_time = time.time()

                # Hiển thị ID trên khung hình
                cv2.putText(frame_bgr, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Kiểm tra thời gian mở khóa
        if unlock_start_time is not None and time.time() - unlock_start_time > 10:
            GPIO.output(RELAY, GPIO.LOW)  # Tắt relay
            print("Đã khóa cửa sau 10 giây.")
            unlock_start_time = None  # Đặt lại thời gian mở khóa

        # Hiển thị frame với các khuôn mặt được đánh dấu
        cv2.imshow("Camera - Face Detection and Recognition", frame_bgr)

        # Nhấn 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Giải phóng tài nguyên và đóng các cửa sổ
picam2.stop()
cv2.destroyAllWindows()
GPIO.cleanup()
