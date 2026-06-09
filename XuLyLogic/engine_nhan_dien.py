import cv2
import mediapipe as mp
import pickle
import os


class BoXuLyNhanDien:
    def __init__(self, duong_dan_model='KhoDuLieu/model_tinh.pkl'):
        # 1. Nạp bộ não AI
        if not os.path.exists(duong_dan_model):
            print(f"[CẢNH BÁO] Không tìm thấy model tại: {duong_dan_model}")
            self.model = None
        else:
            with open(duong_dan_model, 'rb') as f:
                self.model = pickle.load(f)
            print("-> Đã nạp thành công bộ não AI vào Engine!")

        # 2. Khởi tạo MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

    def trich_xuat_toa_do(self, hand_landmarks):
        """Trích xuất 63 tọa độ chuẩn hóa"""
        goc_x = hand_landmarks.landmark[0].x
        goc_y = hand_landmarks.landmark[0].y
        goc_z = hand_landmarks.landmark[0].z

        toa_do = []
        for diem in hand_landmarks.landmark:
            toa_do.extend([diem.x - goc_x, diem.y - goc_y, diem.z - goc_z])
        return toa_do

    def xu_ly_frame(self, frame):
        """Nhận ảnh gốc -> Trả về ảnh đã vẽ xương và kết quả AI đoán"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_frame)

        chu_hien_tai = "..."
        do_tin_cay = 0.0

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Vẽ khung xương tay lên frame
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                # Trích xuất và dự đoán
                toa_do = self.trich_xuat_toa_do(hand_landmarks)
                if len(toa_do) == 63 and self.model is not None:
                    # Lấy xác suất
                    xac_suat = self.model.predict_proba([toa_do])[0]
                    vi_tri_max = xac_suat.argmax()

                    chu_hien_tai = self.model.classes_[vi_tri_max]
                    do_tin_cay = xac_suat[vi_tri_max]

        return frame, chu_hien_tai, do_tin_cay