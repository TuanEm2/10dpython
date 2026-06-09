import cv2
import mediapipe as mp
import pickle
import os
import threading
import time


def chen_anh_png_mo(frame, anh_png, x, y, do_mo=0.5):
    """Hàm chèn ảnh nền trong suốt lên camera (tránh lỗi tràn viền)"""
    if anh_png is None: return frame

    h, w, _ = anh_png.shape
    frame_h, frame_w, _ = frame.shape

    if y + h > frame_h or x + w > frame_w:
        return frame

    vung_hien_tai = frame[y:y + h, x:x + w]
    alpha_png = (anh_png[:, :, 3] / 255.0) * do_mo
    alpha_frame = 1.0 - alpha_png

    for c in range(0, 3):
        vung_hien_tai[:, :, c] = (alpha_png * anh_png[:, :, c] + alpha_frame * vung_hien_tai[:, :, c])
    return frame


class BoXuLyNhanDien:
    def __init__(self, duong_dan_model='KhoDuLieu/model_tinh.pkl'):
        # 1. Khởi tạo công cụ vẽ
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands

        # 2. Nạp bộ não AI
        if not os.path.exists(duong_dan_model):
            print(f"[CẢNH BÁO] Không tìm thấy model tại: {duong_dan_model}")
            self.model = None
        else:
            with open(duong_dan_model, 'rb') as f:
                self.model = pickle.load(f)
            print("-> Đã nạp thành công bộ não AI vào Engine Đa Luồng!")

        # 3. Biến quản lý Đa luồng (Multi-threading)
        self.frame_to_process = None
        self.lock = threading.Lock()
        self.is_running = True

        # Biến chứa kết quả do luồng ngầm tính toán ra
        self.ket_qua_chu = "..."
        self.ket_qua_tin_cay = 0.0
        self.ket_qua_landmarks = None

        # Khởi động "Anh công nhân AI" chạy ngầm
        self.thread = threading.Thread(target=self._ai_worker, daemon=True)
        self.thread.start()

    def trich_xuat_toa_do(self, hand_landmarks):
        """Đã nâng cấp: Chuẩn hóa tỉ lệ (Tránh lỗi tay to/nhỏ do khoảng cách)"""
        goc_x = hand_landmarks.landmark[0].x
        goc_y = hand_landmarks.landmark[0].y
        goc_z = hand_landmarks.landmark[0].z

        toa_do_tam_thoi = []
        for diem in hand_landmarks.landmark:
            toa_do_tam_thoi.extend([diem.x - goc_x, diem.y - goc_y, diem.z - goc_z])

        # Chuẩn hóa
        max_value = max(list(map(abs, toa_do_tam_thoi)))
        if max_value == 0: max_value = 1.0

        toa_do_chuan_hoa = [val / max_value for val in toa_do_tam_thoi]
        return toa_do_chuan_hoa

    def _ai_worker(self):
        """Hàm chạy ngầm: Chỉ chuyên tập trung tính toán MediaPipe và RF Model"""
        # Khởi tạo MediaPipe bên TRONG luồng riêng để tránh lỗi
        hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

        while self.is_running:
            frame_xu_ly = None
            with self.lock:
                if self.frame_to_process is not None:
                    frame_xu_ly = self.frame_to_process
                    self.frame_to_process = None  # Đã lấy ra, chờ frame tiếp theo

            if frame_xu_ly is not None:
                rgb_frame = cv2.cvtColor(frame_xu_ly, cv2.COLOR_BGR2RGB)
                result = hands.process(rgb_frame)

                chu_tam = "..."
                tin_cay_tam = 0.0
                landmarks_tam = None

                if result.multi_hand_landmarks:
                    landmarks_tam = result.multi_hand_landmarks[0]
                    toa_do = self.trich_xuat_toa_do(landmarks_tam)

                    if len(toa_do) == 63 and self.model is not None:
                        xac_suat = self.model.predict_proba([toa_do])[0]
                        vi_tri = xac_suat.argmax()
                        chu_tam = self.model.classes_[vi_tri]
                        tin_cay_tam = xac_suat[vi_tri]

                # Cập nhật kết quả an toàn để App lấy ra hiển thị
                with self.lock:
                    self.ket_qua_chu = chu_tam
                    self.ket_qua_tin_cay = tin_cay_tam
                    self.ket_qua_landmarks = landmarks_tam
            else:
                time.sleep(0.01)  # Nghỉ ngơi nếu chưa có frame mới

    def xu_ly_frame(self, frame, anh_mau=None):
        """Hàm giao tiếp với App: Nhận ảnh gốc, trả ảnh đã vẽ"""
        # 1. Quăng frame cho luồng ngầm xử lý
        with self.lock:
            self.frame_to_process = frame.copy()

        # 2. Lấy kết quả mà luồng ngầm ĐÃ TÍNH XONG ra để xài
        with self.lock:
            chu_hien_tai = self.ket_qua_chu
            do_tin_cay = self.ket_qua_tin_cay
            landmarks = self.ket_qua_landmarks

        # 3. Chèn ảnh mẫu tay mờ (Nếu đang ở chế độ học)
        if anh_mau is not None:
            frame = chen_anh_png_mo(frame, anh_mau, x=50, y=50, do_mo=0.6)

        # 4. Vẽ khung xương tay
        if landmarks:
            self.mp_draw.draw_landmarks(frame, landmarks, self.mp_hands.HAND_CONNECTIONS)

        return frame, chu_hien_tai, do_tin_cay