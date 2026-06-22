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
SO_TOA_DO_DONG = 252  # 126 tĩnh + 126 vận tốc
SO_TOA_DO_TINH = 126  # 63 trái + 63 phải
NGUONG_TIN_CAY_TINH = 0.55  # Hạ nhẹ để nhận diện các chữ khó như R, X, V mượt hơn
NGUONG_TIN_CAY_DONG = 0.80
NGUONG_DICH_CHUYEN_CO_TAY = 0.025  # Cổ tay phải tịnh tiến > 2.5% màn hình mới gọi là múa Động
THOI_GIAN_DONG_BANG = 1.2


class SignLanguageLSTM(nn.Module):
    def __init__(self, num_classes):
        super(SignLanguageLSTM, self).__init__()
        self.lstm1 = nn.LSTM(252, 128, bidirectional=True, batch_first=True)
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


def trich_xuat_1_tay_chuan(hand_lm):
    """Trích xuất 63 con số chuẩn hóa tuyệt đối của đúng 1 bàn tay"""
    gx, gy, gz = hand_lm.landmark[0].x, hand_lm.landmark[0].y, hand_lm.landmark[0].z
    toa_do = []
    for p in hand_lm.landmark:
        toa_do.extend([p.x - gx, p.y - gy, p.z - gz])
    max_v = max(abs(v) for v in toa_do) if toa_do else 1.0
    if max_v == 0: max_v = 1.0
    return [v / max_v for v in toa_do]


def sap_xep_ban_tay_khong_gian(multi_hand_landmarks, multi_handedness):
    """
    BỘ LỌC KHÔNG GIAN BỌC LÓT:
    Sắp xếp tay chặt chẽ theo tọa độ X từ Trái sang Phải màn hình để chống lộn hộc tủ.
    """
    if not multi_hand_landmarks:
        return [0.0] * 126, None

    tays = []
    for i, lm in enumerate(multi_hand_landmarks):
        # Bỏ qua các bàn tay mờ ảo (tránh bóng ma)
        if multi_handedness[i].classification[0].score < 0.55:
            continue
        tays.append({
            "x_root": lm.landmark[0].x,
            "y_root": lm.landmark[0].y,
            "norm": trich_xuat_1_tay_chuan(lm)
        })

    # Sắp xếp theo trục X ngang màn hình
    tays.sort(key=lambda item: item["x_root"])

    tay_trai = [0.0] * 63
    tay_phai = [0.0] * 63
    co_tay_chinh = None

    if len(tays) == 1:
        t = tays[0]
        co_tay_chinh = (t["x_root"], t["y_root"])
        if t["x_root"] < 0.5:
            tay_trai = t["norm"]
        else:
            tay_phai = t["norm"]
    elif len(tays) >= 2:
        t0, t1 = tays[0], tays[1]
        tay_trai = t0["norm"]
        tay_phai = t1["norm"]
        co_tay_chinh = (t0["x_root"], t0["y_root"])  # Lấy tay trái làm mốc đo tịnh tiến

    return tay_trai + tay_phai, co_tay_chinh


def ve_khung_xuong_tay_custom(frame, ds_diem_pixel_mot_tay):
    """Vẽ nét trắng sữa tinh tế miễn nhiễm với lỗi rác con trỏ C++"""
    if not ds_diem_pixel_mot_tay or len(ds_diem_pixel_mot_tay) < 21:
        return

    KET_NOI_BONE = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (17, 18), (18, 19), (19, 20),
        (0, 17)
    ]

    for idx_a, idx_b in KET_NOI_BONE:
        pt1 = ds_diem_pixel_mot_tay[idx_a]
        pt2 = ds_diem_pixel_mot_tay[idx_b]
        cv2.line(frame, pt1, pt2, (245, 245, 250), 2, cv2.LINE_AA)

    for x, y in ds_diem_pixel_mot_tay:
        cv2.circle(frame, (x, y), 4, (0, 0, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), 6, (0, 0, 255), 1, cv2.LINE_AA)


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
        self.co_tay_truoc = None
        self.toa_do_frame_truoc = None
        self.thoi_diem_dong_bang = 0
        self.lich_su_chu = []

        self.ket_qua_chu = "..."
        self.ket_qua_tin_cay = 0.0
        self.ket_qua_nguon = "..."
        self.ket_qua_danh_sach_landmarks = []

        self.frame_to_process = None
        self.lock = threading.Lock()
        self.is_running = True

        self.thread = threading.Thread(target=self._ai_worker, daemon=True)
        self.thread.start()

    def _ai_worker(self):
        if os.path.exists(self.model_tinh_path):
            try:
                with open(self.model_tinh_path, 'rb') as f:
                    self.model_tinh = pickle.load(f)
            except Exception:
                self.model_tinh = None

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if os.path.exists(self.model_dong_path) and os.path.exists(self.nhan_dong_path):
            try:
                self.nhan_dong = np.load(self.nhan_dong_path, allow_pickle=True).tolist()
                self.model_dong = SignLanguageLSTM(num_classes=len(self.nhan_dong)).to(self.device)
                self.model_dong.load_state_dict(torch.load(self.model_dong_path, map_location=self.device))
                self.model_dong.eval()
            except Exception:
                self.model_dong = None

        hands = self.mp_hands.Hands(
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.65
        )

        while self.is_running:
            try:
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
                ds_diem_pixel_tam = []

                thoi_gian_hien_tai = time.time()

                # Trích xuất pixel thuần Python để vẽ mượt
                if result.multi_hand_landmarks:
                    h_img, w_img, _ = frame_xu_ly.shape
                    for hand_lm in result.multi_hand_landmarks:
                        mot_tay = [(int(lm.x * w_img), int(lm.y * h_img)) for lm in hand_lm.landmark]
                        ds_diem_pixel_tam.append(mot_tay)

                if self.trang_thai == "DONG_BANG":
                    if thoi_gian_hien_tai - self.thoi_diem_dong_bang > THOI_GIAN_DONG_BANG:
                        self.trang_thai = "TINH"
                        self.frames_rec = []
                        self.lich_su_chu = []
                        chu_tam = "..."
                        tin_cay_tam = 0.0
                        nguon_tam = "..."
                    else:
                        with self.lock:
                            self.ket_qua_danh_sach_landmarks = ds_diem_pixel_tam
                        continue

                # --- QUY TRÌNH XỬ LÝ CHÍNH ---
                if result.multi_hand_landmarks:
                    toa_do_126, co_tay_hien_tai = sap_xep_ban_tay_khong_gian(result.multi_hand_landmarks,
                                                                             result.multi_handedness)

                    # BƯỚC 1: ĐO TỊNH TIẾN CỔ TAY (CHỐNG NHIỄU RÁC NGÓN TAY)
                    dich_chuyen_co_tay = 0.0
                    if co_tay_hien_tai is not None and self.co_tay_truoc is not None:
                        dx = co_tay_hien_tai[0] - self.co_tay_truoc[0]
                        dy = co_tay_hien_tai[1] - self.co_tay_truoc[1]
                        dich_chuyen_co_tay = (dx ** 2 + dy ** 2) ** 0.5

                    self.co_tay_truoc = co_tay_hien_tai

                    # BƯỚC 2: TÍNH VECTOR ĐẶC TRƯNG 252 CHO PYTORCH
                    if self.toa_do_frame_truoc is None:
                        van_toc_126 = [0.0] * 126
                    else:
                        van_toc_126 = [toa_do_126[i] - self.toa_do_frame_truoc[i] for i in range(126)]

                    dac_trung_252 = toa_do_126 + van_toc_126
                    self.toa_do_frame_truoc = toa_do_126.copy()

                    # BƯỚC 3: SIÊU THUẬT TOÁN BÓI 2 HỘC TỦ (CHỐNG LỆCH TAY)
                    chu_tinh_tam = "?"
                    tin_cay_tinh_tam = 0.0
                    if self.model_tinh is not None and any(v != 0.0 for v in toa_do_126):
                        try:
                            # Tách hộc Trái và hộc Phải ra
                            t_trai = toa_do_126[:63]
                            t_phai = toa_do_126[63:]

                            # Thử cả 2 phương án: Gốc và Đảo hộc
                            pa1 = toa_do_126
                            pa2 = t_phai + t_trai

                            prob1 = self.model_tinh.predict_proba([pa1])[0]
                            prob2 = self.model_tinh.predict_proba([pa2])[0]

                            idx1, idx2 = prob1.argmax(), prob2.argmax()
                            max1, max2 = prob1[idx1], prob2[idx2]

                            if max1 >= max2:
                                tin_cay_tinh_tam = float(max1)
                                chu_tinh_tam = self.model_tinh.classes_[idx1]
                            else:
                                tin_cay_tinh_tam = float(max2)
                                chu_tinh_tam = self.model_tinh.classes_[idx2]
                        except ValueError:
                            chu_tinh_tam = "[Sai Cột Tĩnh]"

                    # --- PHÂN NHÁNH TRẠNG THÁI ---
                    if self.trang_thai == "TINH":
                        # Chỉ kích hoạt REC khi Cổ tay di chuyển một quãng đủ dài across the camera
                        if dich_chuyen_co_tay > NGUONG_DICH_CHUYEN_CO_TAY:
                            self.trang_thai = "DANG_REC"
                            self.frames_rec = [dac_trung_252]
                            chu_tam = "..."
                            nguon_tam = "REC: 1"
                            tin_cay_tam = 0.0
                        else:
                            if tin_cay_tinh_tam >= NGUONG_TIN_CAY_TINH:
                                self.lich_su_chu.append(chu_tinh_tam)
                                if len(self.lich_su_chu) > 7: self.lich_su_chu.pop(0)
                                chu_tam = Counter(self.lich_su_chu).most_common(1)[0][0]
                                tin_cay_tam = tin_cay_tinh_tam
                                nguon_tam = "TINH"
                            else:
                                chu_tam = "?"
                                nguon_tam = "..."

                    elif self.trang_thai == "DANG_REC":
                        self.frames_rec.append(dac_trung_252)
                        so_frame_da_ghi = len(self.frames_rec)
                        chu_tam = "..."
                        tin_cay_tam = 0.0
                        nguon_tam = f"REC: {so_frame_da_ghi}/{SO_FRAME_LSTM}"

                        if so_frame_da_ghi == SO_FRAME_LSTM:
                            if self.model_dong is not None:
                                try:
                                    X_tensor = torch.tensor([self.frames_rec], dtype=torch.float32).to(self.device)
                                    with torch.no_grad():
                                        outputs = self.model_dong(X_tensor)
                                        xac_suat_dong = torch.softmax(outputs, dim=1).cpu().numpy()[0]

                                    vi_tri_dong = xac_suat_dong.argmax()
                                    tin_cay_dong = float(xac_suat_dong[vi_tri_dong])
                                    nhan_du_doan = self.nhan_dong[vi_tri_dong]

                                    # CHỈ KHÓA KHI TỰ TIN VÀ KHÔNG PHẢI LÀ NHẪN 'NONE'
                                    if tin_cay_dong >= NGUONG_TIN_CAY_DONG and nhan_du_doan.upper() not in ["NONE", "",
                                                                                                            "NONE_"]:
                                        chu_tam = nhan_du_doan
                                        tin_cay_tam = tin_cay_dong
                                        nguon_tam = "DONG"
                                        self.trang_thai = "DONG_BANG"
                                        self.thoi_diem_dong_bang = time.time()
                                    else:
                                        # HỦY KẾT QUẢ RÁC: Trả lại quyền chấm điểm Tĩnh ngay lập tức!
                                        self.trang_thai = "TINH"
                                        self.frames_rec = []
                                        chu_tam = chu_tinh_tam
                                        tin_cay_tam = tin_cay_tinh_tam
                                        nguon_tam = "TINH (Drop REC)"
                                except Exception:
                                    self.trang_thai = "TINH";
                                    self.frames_rec = []
                            else:
                                self.trang_thai = "TINH";
                                self.frames_rec = []
                else:
                    self.co_tay_truoc = None;
                    self.toa_do_frame_truoc = None
                    self.trang_thai = "TINH";
                    self.frames_rec = [];
                    self.lich_su_chu = []
                    chu_tam = "...";
                    tin_cay_tam = 0.0;
                    nguon_tam = "..."
                    ds_diem_pixel_tam = []

                with self.lock:
                    self.ket_qua_chu = chu_tam
                    self.ket_qua_tin_cay = tin_cay_tam
                    self.ket_qua_nguon = nguon_tam
                    self.ket_qua_danh_sach_landmarks = ds_diem_pixel_tam

            except Exception as e:
                print(f"[AI Worker] Nuốt 1 frame rác: {e}")
                time.sleep(0.01)

    def xu_ly_frame(self, frame, anh_mau=None):
        with self.lock:
            self.frame_to_process = frame.copy()

        with self.lock:
            chu = self.ket_qua_chu
            tin_cay = self.ket_qua_tin_cay
            nguon = self.ket_qua_nguon
            danh_sach_tay = self.ket_qua_danh_sach_landmarks

        if anh_mau is not None:
            frame = chen_anh_png_mo(frame, anh_mau, x=50, y=50, do_mo=0.6)

        if danh_sach_tay:
            for mot_tay in danh_sach_tay:
                ve_khung_xuong_tay_custom(frame, mot_tay)

        return frame, chu, tin_cay, nguon

    def dung(self):
        self.is_running = False