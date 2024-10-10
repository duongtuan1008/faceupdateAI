import os
import cv2
import pickle
import face_recognition

# Đường dẫn đến thư mục chứa hình ảnh
dataset_dir = '/home/Tun/Desktop/FacePass2/dataset'


# Khởi tạo từ điển để lưu trữ encoding và ID
all_face_encodings = {}

# Duyệt qua tất cả các thư mục trong dataset_dir
for user_id in os.listdir(dataset_dir):
    user_folder = os.path.join(dataset_dir, user_id)
    
    if os.path.isdir(user_folder):  # Kiểm tra xem có phải là thư mục không
        for image_name in os.listdir(user_folder):
            image_path = os.path.join(user_folder, image_name)

            # Đọc hình ảnh
            image = face_recognition.load_image_file(image_path)

            # Trích xuất encoding khuôn mặt
            face_encodings = face_recognition.face_encodings(image)

            # Nếu tìm thấy encoding, thêm vào từ điển
            if len(face_encodings) > 0:
                # Lưu trữ encoding với user_id
                all_face_encodings[user_id] = all_face_encodings.get(user_id, [])
                all_face_encodings[user_id].append(face_encodings[0])

# Chuyển đổi danh sách encoding thành một từ điển
final_face_encodings = {}
for user_id, encodings in all_face_encodings.items():
    # Lấy trung bình của các encoding cho mỗi user_id
    average_encoding = sum(encodings) / len(encodings)
    final_face_encodings[user_id] = average_encoding

# Lưu trữ encoding vào tệp dataset_faces.dat
with open('dataset_faces.dat', 'wb') as file:
    pickle.dump(final_face_encodings, file)

print("Đã thêm dữ liệu huấn luyện thành công!")
