import cv2
import pickle
from picamera2 import Picamera2
import face_recognition
import RPi.GPIO as GPIO
import time

# Kh?i t?o camera v?i Picamera2
picam2 = Picamera2()
picam2.start()

# T?i mô hình Haar Cascade d? nh?n di?n khuôn m?t
haarcascade_path = '/home/Tun/Desktop/FacePass2/haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haarcascade_path)

if face_cascade.empty():
    print("Không th? t?i mô hình Haar Cascade.")
    exit()

# Ð?c d? li?u khuôn m?t dã luu
try:
    with open('dataset_faces.dat', 'rb') as file:
        all_face_encodings = pickle.load(file)
except FileNotFoundError:
    print("T?p d? li?u khuôn m?t không t?n t?i.")
    exit()

# Chuy?n d?i t? di?n thành danh sách các encoding và ID
known_face_encodings = list(all_face_encodings.values())
known_face_ids = list(all_face_encodings.keys())

while True:
    # Ch?p frame t? Picamera2
    frame = picam2.capture_array()

    # Chuy?n d?i frame sang d?nh d?ng BGR
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Chuy?n frame sang ?nh xám d? nh?n di?n khuôn m?t
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    # Phát hi?n khuôn m?t trong ?nh
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # V? hình ch? nh?t quanh các khuôn m?t du?c phát hi?n và nh?n di?n
    for (x, y, w, h) in faces:
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # C?t khuôn m?t t? frame
        face_image = frame[y:y+h, x:x+w]
        face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

        # Trích xu?t d?c trung khuôn m?t
        face_encoding = face_recognition.face_encodings(face_rgb)

        if len(face_encoding) > 0:  # Ki?m tra xem có encoding không
            # So sánh v?i các encoding dã luu
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding[0])
            name = "Unknown"
            # N?u có m?t s? trùng kh?p, l?y ID tuong ?ng
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_ids[first_match_index]
                print(f"M? khóa c?a cho ngu?i dùng: {name}")
            # Hi?n th? ID trên khung hình
            cv2.putText(frame_bgr, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    # Hi?n th? frame v?i các khuôn m?t du?c dánh d?u
    cv2.imshow("Camera - Face Detection and Recognition", frame_bgr)
    # Nh?n 'q' d? thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# Gi?i phóng tài nguyên và dóng các c?a s?
picam2.stop()
cv2.destroyAllWindows()