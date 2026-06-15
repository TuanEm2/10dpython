import cv2
import mediapipe as mp
import pickle
import os
import threading
import time
import numpy as np
from collections import deque, Counter
import traceback

try:
    import tensorflow as tf

    TENSORFLOW_CO_SAN = True
except ImportError:
    TENSORFLOW_CO_SAN = False

# ============================================================
# CẤU HÌNH ĐƯỜNG DẪN & NGƯỠNG NHẬN DIỆN
# ============================================================
MODEL_TINH_PATH = 'KhoDuLieu/model_tinh.pkl'
MODEL_DONG_PATH = 'KhoDuLieu/model_dong.h5'
NHAN_DONG_PATH = 'KhoDuLieu/model_dong_labels.npy'

SO_FRAME_LSTM = 30
NGUONG_TIN_CAY_TINH = 0.60
NGUONG_TIN_CAY_DONG = 0.50


def chen_anh_png_mo(frame, anh_png, x, y, do_mo=0.5):
    if anh_png is None: return frame
    h, w, _ = anh_png.shape
    frame_h, frame_w, _ = frame.shape
    if y + h > frame_h or x + w > frame_w: return frame
    vung = frame[y:y + h, x:x + w]
    alpha = (anh_png[:, :, 3] / 255.0) * do_mo
    for c in range(3):
        vung[:, :, c] = alpha * anh_png[:, :, c] + (1 - alpha) * vung[:, :, c]
    return frame


def trich_xuat_toa_do(hand_landmarks):
    goc_x = hand_landmarks.landmark[0].x
    goc_y = hand_landmarks.landmark[0].y
    goc_z = hand_landmarks.landmark[0].z
    toa_do = []
    for diem in hand_landmarks.landmark:
        toa_do.extend([diem.x - goc_x, diem.y - goc_y, diem.z - goc_z])
    max_val = max(abs(v) for v in toa_do)
    if max_val == 0: max_val = 1.0
    return [v / max_val for v in toa_do]


class BoXuLyNhanDienKetHop:
    def __init__(self, model_tinh_path=MODEL_TINH_PATH, model_dong_path=MODEL_DONG_PATH, nhan_dong_path=NHAN_DONG_PATH):
        self.model_tinh_path = model_tinh_path
        self.model_dong_path = model_dong_path
        self.nhan_dong_path = nhan_dong_path

        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands

        self.model_tinh = None
        self.model_dong = None
        self.nhan_dong = []
        self.buffer_lstm = deque(maxlen=SO_FRAME_LSTM)
        self.mat_tay_count = 0

        # --- BỘ LỌC CHỐNG NHIỄU (SMOOTHING) ---
        self.lich_su_chu = deque(maxlen=10)  # Lưu 10 kết quả gần nhất (~0.3 giây)
        self.chu_on_dinh = "..."  # Chữ sẽ được hiển thị lên màn hình

        self.ket_qua_chu = "..."
        self.ket_qua_tin_cay = 0.0
        self.ket_qua_nguon = "..."
        self.ket_qua_landmarks = None

        self.frame_to_process = None
        self.lock = threading.Lock()
        self.is_running = True

        self.thread = threading.Thread(target=self._ai_worker, daemon=True)
        self.thread.start()
        print("  [OK] Luồng ngầm AI hoàn thành khởi động.")

    def _ai_worker(self):
        try:
            print("  -> Đang nạp Model...")
            if os.path.exists(self.model_tinh_path):
                with open(self.model_tinh_path, 'rb') as f:
                    self.model_tinh = pickle.load(f)

            if TENSORFLOW_CO_SAN and os.path.exists(self.model_dong_path):
                self.model_dong = tf.keras.models.load_model(self.model_dong_path)
                if os.path.exists(self.nhan_dong_path):
                    self.nhan_dong = np.load(self.nhan_dong_path, allow_pickle=True).tolist()

            hands = self.mp_hands.Hands(
                max_num_hands=1,
                model_complexity=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6
            )
            print("  -> Động cơ xử lý đã sẵn sàng!")

            while self.is_running:
                frame_xu_ly = None
                with self.lock:
                    if self.frame_to_process is not None:
                        frame_xu_ly = self.frame_to_process
                        self.frame_to_process = None

                if frame_xu_ly is None:
                    time.sleep(0.005)
                    continue

                rgb = cv2.cvtColor(frame_xu_ly, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                result = hands.process(rgb)
                rgb.flags.writeable = True

                chu_tam = "..."
                tin_cay_tam = 0.0
                nguon_tam = "..."
                landmarks_tam = None

                if result.multi_hand_landmarks:
                    self.mat_tay_count = 0
                    landmarks_tam = result.multi_hand_landmarks[0]
                    toa_do = trich_xuat_toa_do(landmarks_tam)

                    if len(toa_do) == 63:
                        self.buffer_lstm.append(toa_do)

                        # 1. TĨNH
                        chu_tinh = None
                        tin_cay_tinh = 0.0
                        if self.model_tinh is not None:
                            xac_suat_tinh = self.model_tinh.predict_proba([toa_do])[0]
                            vi_tri_tinh = xac_suat_tinh.argmax()
                            tin_cay_tinh = float(xac_suat_tinh[vi_tri_tinh])
                            chu_tinh = self.model_tinh.classes_[vi_tri_tinh]

                        # 2. ĐỘNG
                        chu_dong = None
                        tin_cay_dong = 0.0
                        if self.model_dong is not None and len(self.buffer_lstm) == SO_FRAME_LSTM:
                            X_lstm = np.array(self.buffer_lstm).reshape(1, SO_FRAME_LSTM, 63)
                            xac_suat_dong = self.model_dong(X_lstm, training=False).numpy()[0]
                            vi_tri_dong = xac_suat_dong.argmax()
                            tin_cay_dong = float(xac_suat_dong[vi_tri_dong])
                            chu_dong = self.nhan_dong[vi_tri_dong]

                        # 3. CHỌN LỌC KẾT QUẢ
                        if chu_dong is not None and tin_cay_dong >= NGUONG_TIN_CAY_DONG:
                            chu_tam = chu_dong
                            tin_cay_tam = tin_cay_dong
                            nguon_tam = "DONG"
                        elif chu_tinh is not None and tin_cay_tinh >= NGUONG_TIN_CAY_TINH:
                            chu_tam = chu_tinh
                            tin_cay_tam = tin_cay_tinh
                            nguon_tam = "TINH"
                        else:
                            chu_tam = "?"
                            nguon_tam = "..."

                        # --- THUẬT TOÁN LÀM MƯỢT KẾT QUẢ (MAJORITY VOTING) ---
                        if chu_tam not in ["?", "..."]:
                            self.lich_su_chu.append(chu_tam)

                        if len(self.lich_su_chu) > 0:
                            dem_chu = Counter(self.lich_su_chu)
                            # Lấy ra chữ cái xuất hiện nhiều nhất trong lịch sử
                            chu_pho_bien_nhat, so_lan = dem_chu.most_common(1)[0]

                            # Nếu chữ đó chiếm >= 50% số khung hình, cập nhật hiển thị
                            if so_lan >= len(self.lich_su_chu) * 0.5:
                                self.chu_on_dinh = chu_pho_bien_nhat

                else:
                    self.mat_tay_count += 1
                    if self.mat_tay_count > 5:
                        self.buffer_lstm.clear()
                        self.lich_su_chu.clear()  # Xóa sổ tay khi mất tay
                        self.chu_on_dinh = "..."

                with self.lock:
                    self.ket_qua_chu = self.chu_on_dinh  # Trả về chữ ĐÃ ĐƯỢC LÀM MƯỢT
                    self.ket_qua_tin_cay = tin_cay_tam
                    self.ket_qua_nguon = nguon_tam
                    self.ket_qua_landmarks = landmarks_tam

        except Exception:
            print("\n[LỖI SẬP LUỒNG HỆ THỐNG AI]")
            traceback.print_exc()

    def xu_ly_frame(self, frame, anh_mau=None):
        with self.lock:
            self.frame_to_process = frame.copy()

        with self.lock:
            chu = self.ket_qua_chu
            tin_cay = self.ket_qua_tin_cay
            nguon = self.ket_qua_nguon
            landmarks = self.ket_qua_landmarks

        if anh_mau is not None:
            frame = chen_anh_png_mo(frame, anh_mau, x=50, y=50, do_mo=0.6)

        if landmarks:
            self.mp_draw.draw_landmarks(frame, landmarks, self.mp_hands.HAND_CONNECTIONS)

        return frame, chu, tin_cay, nguon

    def dung(self):
        self.is_running = False


def chay_nhan_dien_don_gian():
    print("\n--- CHẠY THỬ ENGINE KẾT HỢP (STANDALONE) ---")
    engine = BoXuLyNhanDienKetHop()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        frame, chu, tin_cay, nguon = engine.xu_ly_frame(frame)

        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 90), (10, 10, 20), cv2.FILLED)
        mau = (0, 255, 150) if nguon == "TINH" else (0, 165, 255)
        cv2.putText(frame, f"{chu}  ({int(tin_cay * 100)}%)  [{nguon}]", (20, 60), cv2.FONT_HERSHEY_DUPLEX, 1.8, mau, 2)

        cv2.imshow('Nhan Dien Ket Hop', frame)
        if cv2.waitKey(1) & 0xFF in [ord('q'), 27]: break

    engine.dung()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    chay_nhan_dien_don_gian()