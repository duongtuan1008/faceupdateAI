import time
import cv2
import pickle
from picamera2 import Picamera2
import face_recognition
import RPi.GPIO as GPIO  # Đảm bảo đã import thư viện GPIO
from email.message import EmailMessage
import smtplib
import imghdr

# Cấu hình GPIO
TILT_PIN = 17  # Chân GPIO cho cảm biến nghiêng (tùy chỉnh theo kết nối của bạn)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TILT_PIN, GPIO.IN)
picam2 = Picamera2()
picam2.start()  # Bật camera ngay lập tức
# Biến toàn cục
is_checking_password = False
i = 0
Sender_email = "your_sender_email@gmail.com"  # Địa chỉ email gửi
pass_sender = "your_app_password"  # Mật khẩu ứng dụng
Reciever_Email = "recipient_email@gmail.com"  # Địa chỉ email nhận

# Hàm gửi email
def SendEmail(sender, password, receiver):
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
        smtp.login(sender, password)
        smtp.send_message(newMessage)
    print("Email đã được gửi với ảnh đính kèm.")

# Hàm xử lý cảm biến nghiêng

# Chạy hàm trong vòng lặp hoặc khi có sự kiện
try:
    while True:
        SendEmail("duongtuan10082003@gmail.com", "vrrw tsqa aljl nbrk", "duongtuan1008@gmail.com")
        # Gọi hàm xử lý cảm biến nghiêng
        time.sleep(1)  # Thời gian chờ giữa các lần kiểm tra
except KeyboardInterrupt:
    print("Program stopped")
finally:
    GPIO.cleanup()  # Dọn dẹp cấu hình GPIO khi thoát
