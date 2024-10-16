import time
import picamera2
import RPi.GPIO as GPIO  # Đảm bảo đã import thư viện GPIO
from email.message import EmailMessage
import smtplib

# Cấu hình GPIO
TILT_PIN = 17  # Chân GPIO cho cảm biến nghiêng (tùy chỉnh theo kết nối của bạn)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TILT_PIN, GPIO.IN)

# Biến toàn cục
is_checking_password = False
i = 0
Sender_email = "your_sender_email@gmail.com"  # Địa chỉ email gửi
pass_sender = "your_app_password"  # Mật khẩu ứng dụng
Reciever_Email = "recipient_email@gmail.com"  # Địa chỉ email nhận

# Hàm gửi email
def SendEmail(sender, password, receiver, image_path):
    newMessage = EmailMessage()
    newMessage['Subject'] = "CANH BAO !!!"
    newMessage['From'] = sender
    newMessage['To'] = receiver
    newMessage.set_content('CANH BAO AN NINH')
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
        image_type = imghdr.what(f.name)
        image_name = f.name
        newMessage.add_attachment(image_data, maintype='image', subtype=image_type, filename=image_name)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(newMessage)

# Hàm xử lý cảm biến nghiêng
def Tilt_Handle():
    global is_checking_password
    tilt_sensor = GPIO.input(TILT_PIN)  # Đọc giá trị từ cảm biến nghiêng
    if not is_checking_password and tilt_sensor:  # Nếu không kiểm tra mật khẩu và cảm biến ở trạng thái kích hoạt
        global i
        i += 1  # Tăng biến đếm ảnh
        image_path = f"/home/Tun/Desktop/FacePass2/image/image_{i}.jpg"  # Tạo đường dẫn lưu ảnh
        picam2.capture(image_path)  # Chụp ảnh và lưu vào thư mục
        print('A photo has been taken')  # In thông báo đã chụp ảnh
        time.sleep(10)  # Chờ 10 giây trước khi có thể chụp tiếp
        SendEmail(Sender_email, pass_sender, Reciever_Email, image_path)  # Gửi email với ảnh đã chụp

# Chạy hàm trong vòng lặp hoặc khi có sự kiện
try:
    while True:
        Tilt_Handle()  # Gọi hàm xử lý cảm biến nghiêng
        time.sleep(1)  # Thời gian chờ giữa các lần kiểm tra
except KeyboardInterrupt:
    print("Program stopped")
finally:
    GPIO.cleanup()  # Dọn dẹp cấu hình GPIO khi thoát

SendEmail("duongtuan10082003@gmail.com", "vrrw tsqa aljl nbrk", "duongtuan1008@gmail.com", "/home/Tun/Desktop/FacePass2/image/path_to_image.jpg")
