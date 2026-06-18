import cv2
import mediapipe as mp
import pickle
import os
import threading
import time
import numpy as np
from collections import Counter
import traceback

import torch
import torch.nn as nn

MODEL_TINH_PATH = 'KhoDuLieu/model_tinh.pkl'
MODEL_DONG_PATH = 'KhoDuLieu/model_dong_pytorch.pth'
NHAN_DONG_PATH = 'KhoDuLieu/model_dong_labels.npy'

SO_FRAME_LSTM = 45
SO_TOA_DO = 126
NGUONG_TIN_CAY_TINH = 0.60
NGUONG_TIN_CAY_DONG = 0.85
NGUONG_CHUYEN_DONG = 2.0  # Ngưỡng chuyển động (Đã tăng)
THOI_GIAN_DONG_BANG = 1.5


class SignLanguageLSTM(nn.Module):
    def __init__(self, num_classes):
        super(SignLanguageLSTM, self).__init__()
        self.lstm1 = nn.LSTM(126, 128, bidirectional=True, batch_first=True)
        self.bn1 = nn.BatchNorm1d(256)
        self.dropout1 = nn.Dropout(0.3)
        self.lstm2 = nn.LSTM(256, 64, bidirectional=True, batch_first=True)
        self.bn2 = nn.BatchNorm1d(128)
        self.dropout2 = nn.Dropout(0.3)
        self.fc1 = nn.Linear(128, 128)
        self.relu = nn.ReLU()
        self.dropout3 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_classes)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out = out.transpose(1, 2)
        out = self.bn1(out)
        out = out.transpose(1, 2)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = out[:, -1, :]
        out = self.bn2(out)
        out = self.dropout2(out)
        out = self.fc1(out)
        out = self.relu(out)
        out = self.dropout3(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.fc3(out)
        return out


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

        self.trang_thai = "TINH"
        self.frames_rec = []
        self.toa_do_frame_truoc = None
        self.thoi_diem_dong_bang = 0
        self.lich_su_chu = []

        self.ket_qua_chu = "..."
        self.ket_qua_tin_cay = 0.0
        self.ket_qua_nguon = "..."
        self.ket_qua_landmarks = None

        self.frame_to_process = None
        self.lock = threading.Lock()
        self.is_running = True

        self.thread = threading.Thread(target=self._ai_worker, daemon=True)
        self.thread.start()

    def _ai_worker(self):
        try:
            if os.path.exists(self.model_tinh_path):
                with open(self.model_tinh_path, 'rb') as f:
                    self.model_tinh = pickle.load(f)

            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            if os.path.exists(self.model_dong_path) and os.path.exists(self.nhan_dong_path):
                self.nhan_dong = np.load(self.nhan_dong_path, allow_pickle=True).tolist()
                self.model_dong = SignLanguageLSTM(num_classes=len(self.nhan_dong)).to(self.device)
                self.model_dong.load_state_dict(torch.load(self.model_dong_path, map_location=self.device))
                self.model_dong.eval()

            hands = self.mp_hands.Hands(
                max_num_hands=1,
                model_complexity=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6
            )

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

                chu_tam = self.ket_qua_chu
                tin_cay_tam = self.ket_qua_tin_cay
                nguon_tam = self.ket_qua_nguon
                landmarks_tam = None

                thoi_gian_hien_tai = time.time()

                if self.trang_thai == "DONG_BANG":
                    if thoi_gian_hien_tai - self.thoi_diem_dong_bang > THOI_GIAN_DONG_BANG:
                        self.trang_thai = "TINH"
                        self.frames_rec = []
                        self.lich_su_chu = []
                        chu_tam = "..."
                        tin_cay_tam = 0.0
                        nguon_tam = "..."
                    else:
                        if result.multi_hand_landmarks:
                            landmarks_tam = result.multi_hand_landmarks[0]
                        with self.lock:
                            self.ket_qua_landmarks = landmarks_tam
                        continue

                # --- QUY TRÌNH XỬ LÝ CHÍNH ---
                if result.multi_hand_landmarks:
                    landmarks_tam = result.multi_hand_landmarks[0]
                    toa_do = trich_xuat_toa_do(landmarks_tam)

                    if len(toa_do) == 63:
                        if self.toa_do_frame_truoc is None:
                            van_toc = [0.0] * 63
                        else:
                            van_toc = [toa_do[i] - self.toa_do_frame_truoc[i] for i in range(63)]

                        muc_do_chuyen_dong = sum(abs(v) for v in van_toc)
                        dac_trung = toa_do + van_toc
                        self.toa_do_frame_truoc = toa_do.copy()

                        # CHẠY TRƯỚC MODEL TĨNH ĐỂ XEM ĐỘ TIN CẬY
                        chu_tinh_tam = "?"
                        tin_cay_tinh_tam = 0.0
                        if self.model_tinh is not None:
                            xac_suat_tinh = self.model_tinh.predict_proba([toa_do])[0]
                            vi_tri_tinh = xac_suat_tinh.argmax()
                            tin_cay_tinh_tam = float(xac_suat_tinh[vi_tri_tinh])
                            chu_tinh_tam = self.model_tinh.classes_[vi_tri_tinh]

                        # --- TRẠNG THÁI 1: TĨNH ---
                        if self.trang_thai == "TINH":
                            # CƠ CHẾ KHÓA TĨNH
                            nguong_thuc_te = NGUONG_CHUYEN_DONG * 3.0 if tin_cay_tinh_tam > 0.80 else NGUONG_CHUYEN_DONG

                            if muc_do_chuyen_dong > nguong_thuc_te:
                                self.trang_thai = "DANG_REC"
                                self.frames_rec = [dac_trung]
                                chu_tam = "..."
                                nguon_tam = "REC: 1"
                                tin_cay_tam = 0.0
                            else:
                                if tin_cay_tinh_tam >= NGUONG_TIN_CAY_TINH:
                                    self.lich_su_chu.append(chu_tinh_tam)
                                    if len(self.lich_su_chu) > 10:
                                        self.lich_su_chu.pop(0)

                                    chu_pho_bien = Counter(self.lich_su_chu).most_common(1)[0][0]
                                    chu_tam = chu_pho_bien
                                    tin_cay_tam = tin_cay_tinh_tam
                                    nguon_tam = "TINH"
                                else:
                                    chu_tam = "?"
                                    nguon_tam = "..."

                        # --- TRẠNG THÁI 2: ĐANG GHI HÌNH CỬ ĐỘNG ---
                        elif self.trang_thai == "DANG_REC":
                            self.frames_rec.append(dac_trung)
                            so_frame_da_ghi = len(self.frames_rec)
                            chu_tam = "..."
                            tin_cay_tam = 0.0
                            nguon_tam = f"REC: {so_frame_da_ghi}/{SO_FRAME_LSTM}"

                            if so_frame_da_ghi == SO_FRAME_LSTM:
                                # CHỐT CHẶN 2: Kiểm tra tổng vận tốc
                                tong_van_toc_45 = sum(sum(abs(v) for v in f[63:]) for f in self.frames_rec)

                                if tong_van_toc_45 < (SO_FRAME_LSTM * NGUONG_CHUYEN_DONG * 0.8):
                                    self.trang_thai = "TINH"
                                    self.frames_rec = []
                                    chu_tam = chu_tinh_tam
                                    tin_cay_tam = tin_cay_tinh_tam
                                    nguon_tam = "TINH (HỦY ĐỘNG)"
                                else:
                                    if self.model_dong is not None:
                                        X_tensor = torch.tensor([self.frames_rec], dtype=torch.float32).to(self.device)
                                        with torch.no_grad():
                                            outputs = self.model_dong(X_tensor)
                                            xac_suat_dong = torch.softmax(outputs, dim=1).cpu().numpy()[0]

                                        vi_tri_dong = xac_suat_dong.argmax()
                                        tin_cay_dong = float(xac_suat_dong[vi_tri_dong])
                                        nhan_du_doan = self.nhan_dong[vi_tri_dong]

                                        if tin_cay_dong >= NGUONG_TIN_CAY_DONG and nhan_du_doan != "NONE":
                                            chu_tam = nhan_du_doan
                                            tin_cay_tam = tin_cay_dong
                                            nguon_tam = "DONG"

                                            self.trang_thai = "DONG_BANG"
                                            self.thoi_diem_dong_bang = time.time()
                                        else:
                                            self.trang_thai = "TINH"
                                            self.frames_rec = []
                                            chu_tam = "?"
                                            nguon_tam = "HỦY"
                                    else:
                                        self.trang_thai = "TINH"
                                        self.frames_rec = []
                else:
                    self.toa_do_frame_truoc = None
                    self.trang_thai = "TINH"
                    self.frames_rec = []
                    self.lich_su_chu = []
                    chu_tam = "..."
                    tin_cay_tam = 0.0
                    nguon_tam = "..."

                with self.lock:
                    self.ket_qua_chu = chu_tam
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