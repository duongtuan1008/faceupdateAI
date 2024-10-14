import os
import cv2
import pickle
import face_recognition
import numpy as np
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Đường dẫn đến thư mục chứa hình ảnh khuôn mặt
dataset_dir = '/home/Tun/Desktop/FacePass2/dataset'

# Khởi tạo danh sách để lưu trữ encoding và ID
all_face_encodings = []
all_face_ids = []

# Duyệt qua tất cả các thư mục trong dataset_dir
for user_id in os.listdir(dataset_dir):
    user_folder = os.path.join(dataset_dir, user_id)
    
    if os.path.isdir(user_folder):  # Kiểm tra xem có phải là thư mục không
        for image_name in os.listdir(user_folder):
            image_path = os.path.join(user_folder, image_name)
            
            # Chỉ xử lý các tệp hình ảnh
            if image_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    # Đọc hình ảnh và trích xuất encoding khuôn mặt
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)

                    # Nếu tìm thấy encoding, thêm vào danh sách
                    if face_encodings:
                        all_face_encodings.append(face_encodings[0])
                        all_face_ids.append(user_id)

                except Exception as e:
                    print(f"Không thể xử lý {image_path}: {e}")

# Chia dữ liệu thành tập huấn luyện và tập kiểm tra
X_train, X_test, y_train, y_test = train_test_split(
    all_face_encodings, all_face_ids, test_size=0.2, random_state=42)

# Huấn luyện mô hình SVM
clf = svm.SVC(gamma='scale', probability=True)
clf.fit(X_train, y_train)

# Dự đoán trên tập kiểm tra
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Độ chính xác của mô hình: {accuracy:.2f}")

# Lưu mô hình đã huấn luyện
with open('face_recognition_model.pkl', 'wb') as model_file:
    pickle.dump(clf, model_file)

print("Mô hình đã được lưu thành công!")