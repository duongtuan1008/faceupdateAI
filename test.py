from email.message import EmailMessage
import mimetypes
import smtplib

def SendEmail(sender, pass_sender, reciever, image):
    Sender_Email = sender
    Reciever_Email = reciever
    Password = pass_sender 
    
    # T?o m?t EmailMessage m?i
    newMessage = EmailMessage() 
    newMessage['Subject'] = "C?NH BÁO !!!" 
    newMessage['From'] = Sender_Email 
    newMessage['To'] = Reciever_Email 
    
    # Thi?t l?p n?i dung email v?i van b?n
    text_content = 'C?NH BÁO AN NINH: Du?i dây là hình ?nh c?n xem xét.'
    newMessage.set_content(text_content) 
    
    # M? t?p hình ?nh và d?c d? li?u
    try:
        with open(image, 'rb') as f:
            image_data = f.read()
            image_type, _ = mimetypes.guess_type(f.name)  # Xác d?nh lo?i hình ?nh
            image_name = f.name.split("/")[-1]  # L?y tên t?p hình ?nh
            
            # Thêm t?p hình ?nh vào email
            newMessage.add_attachment(image_data, maintype='image', subtype=image_type.split('/')[1], filename=image_name)
    
        # K?t n?i d?n server SMTP và g?i email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(Sender_Email, Password)  # Ðang nh?p
            smtp.send_message(newMessage)  # G?i email
        
        print('Email sent successfully!')
    
    except FileNotFoundError:
        print(f"Error: File not found - {image}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Ví d? g?i hàm
# Hãy thay th? 'path_to_image.jpg' b?ng du?ng d?n chính xác d?n t?p hình ?nh c?a b?n.
# Ví dụ gọi hàm
SendEmail("duongtuan10082003@gmail.com", "vrrw tsqa aljl nbrk", "duongtuan1008@gmail.com", "/home/Tun/Desktop/FacePass2/image/path_to_image.jpg")
