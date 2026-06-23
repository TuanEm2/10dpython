import cv2
import mediapipe as mp
import pickle
import os
import threading
import time
import math
import numpy as np
from collections import Counter, deque
import traceback

import torch
import torch.nn as nn

MODEL_TINH_PATH = 'KhoDuLieu/model_tinh.pkl'
MODEL_DONG_PATH = 'KhoDuLieu/model_dong_pytorch.pth'
NHAN_DONG_PATH = 'KhoDuLieu/model_dong_labels.npy'

SO_FRAME_LSTM = 45
SO_TOA_DO_DONG = 252
SO_TOA_DO_TINH = 126
NGUONG_TIN_CAY_TINH = 0.55
NGUONG_TIN_CAY_DONG = 0.80
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


class DynamicLandmarkStabilizer:
    def __init__(self):
        self.prev_pts = None

    def lam_muot(self, hand_lm):
        curr_pts = np.array([[lm.x, lm.y, lm.z] for lm in hand_lm.landmark])
        if self.prev_pts is None:
            self.prev_pts = curr_pts.copy()
            return curr_pts

        speed = np.linalg.norm(curr_pts[0][:2] - self.prev_pts[0][:2])
        if speed > 0.08:
            alpha = 1.0
        else:
            alpha = np.clip(speed * 12.0, 0.03, 0.5)

        smoothed = alpha * curr_pts + (1.0 - alpha) * self.prev_pts
        self.prev_pts = smoothed.copy()
        return smoothed


def trich_xuat_toa_do_tu_matran(smoothed_pts):
    centered = smoothed_pts - smoothed_pts[0]
    max_v = np.max(np.abs(centered))
    if max_v < 1e-5: max_v = 1.0
    norm = centered / max_v
    return norm.flatten().tolist()


def get_finger_states_chuan(smoothed_pts):
    states = []
    if abs(smoothed_pts[4][0] - smoothed_pts[0][0]) > abs(smoothed_pts[3][0] - smoothed_pts[0][0]):
        states.append(1)
    else:
        states.append(0)
    for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        if smoothed_pts[tip][1] < smoothed_pts[pip][1]:
            states.append(1)
        else:
            states.append(0)
    return states


def kiem_duyet_giai_phau_hoc(chu_du_doan, finger_states):
    if chu_du_doan in ["?", "...", ""]: return False, 1.0
    so_ngon_duoi = sum(finger_states)
    QUY_TAC = {'A': [0, 1], 'B': [4], 'C': [4, 5], 'D': [1], 'E': [0], 'F': [3], 'G': [1, 2], 'H': [2], 'I': [1],
               'K': [2], 'L': [2], 'M': [0, 3], 'N': [0, 2], 'O': [0, 1], 'P': [2], 'Q': [1, 2], 'R': [2], 'S': [0],
               'T': [0, 1], 'U': [2], 'V': [2], 'W': [3], 'X': [1], 'Y': [2], 'Z': [1], 'SPACE': [5]}
    chu = chu_du_doan.upper()
    if chu in QUY_TAC:
        if so_ngon_duoi in QUY_TAC[chu]:
            return True, 1.35
        else:
            return False, 0.40
    return True, 1.0


def xu_ly_matran_2_tay_muot(multi_hand_landmarks, multi_handedness, dict_stabilizers):
    tay_trai, tay_phai = [0.0] * 63, [0.0] * 63
    co_tay_chinh, raw_muot_chinh = None, None
    danh_sach_ve_hud = []

    if not multi_hand_landmarks:
        return tay_trai + tay_phai, None, None, []

    tays_tho = []
    for i, lm in enumerate(multi_hand_landmarks):
        score = multi_handedness[i].classification[0].score
        label = multi_handedness[i].classification[0].label
        if score < 0.65: continue

        if label not in dict_stabilizers:
            dict_stabilizers[label] = DynamicLandmarkStabilizer()

        pts_3d_muot = dict_stabilizers[label].lam_muot(lm)
        tays_tho.append({
            "x_root": pts_3d_muot[0][0], "y_root": pts_3d_muot[0][1],
            "norm": trich_xuat_toa_do_tu_matran(pts_3d_muot), "pts_3d": pts_3d_muot, "label": label
        })

    tays_tho.sort(key=lambda x: x["x_root"])
    for t in tays_tho: danh_sach_ve_hud.append(t["pts_3d"])

    if len(tays_tho) == 1:
        t = tays_tho[0]
        co_tay_chinh, raw_muot_chinh = (t["x_root"], t["y_root"]), t["pts_3d"]
        if t["label"] == 'Left':
            tay_phai = t["norm"]
        else:
            tay_trai = t["norm"]
    elif len(tays_tho) >= 2:
        t0, t1 = tays_tho[0], tays_tho[1]
        co_tay_chinh, raw_muot_chinh = (t0["x_root"], t0["y_root"]), t0["pts_3d"]
        tay_trai, tay_phai = t0["norm"], t1["norm"]

    return tay_trai + tay_phai, co_tay_chinh, raw_muot_chinh, danh_sach_ve_hud


def ve_khung_xuong_sieu_bam(frame, pts_3d):
    h, w, _ = frame.shape
    pts_px = [(int(x * w), int(y * h)) for x, y, z in pts_3d]
    KET_NOI = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12),
               (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]
    for a, b in KET_NOI: cv2.line(frame, pts_px[a], pts_px[b], (240, 240, 245), 2, cv2.LINE_AA)
    for i, pt in enumerate(pts_px):
        if i in [4, 8, 12, 16, 20]:
            cv2.circle(frame, pt, 5, (0, 200, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 8, (0, 200, 255), 1, cv2.LINE_AA)
        elif i == 0:
            cv2.circle(frame, pt, 6, (255, 255, 255), -1, cv2.LINE_AA)
        else:
            cv2.circle(frame, pt, 4, (0, 230, 115), -1, cv2.LINE_AA)


class BoXuLyNhanDienKetHop:
    def __init__(self, model_tinh_path=MODEL_TINH_PATH, model_dong_path=MODEL_DONG_PATH, nhan_dong_path=NHAN_DONG_PATH):
        self.model_tinh_path = model_tinh_path
        self.model_dong_path = model_dong_path
        self.nhan_dong_path = nhan_dong_path

        self.mp_hands = mp.solutions.hands
        self.model_tinh = None
        self.model_dong = None
        self.nhan_dong = []

        self.trang_thai = "TINH"
        self.frames_rec = []
        self.co_tay_truoc = None
        self.toa_do_frame_truoc = None
        self.thoi_diem_dong_bang = 0
        self.dict_stabilizers = {}

        self.chu_dang_tich_luy = None
        self.so_frame_da_giu = 0
        self.bo_dem_tha_thu = 0
        self.bo_dem_dung_tay = 0  # Bộ đếm hỗ trợ ngắt sớm

        self.che_do_turbo = False
        self.moc_frame_can_giu = 12
        self.thoi_gian_dong_bang = 1.2

        self.quy_dao_co_tay = deque(maxlen=5)
        self.ket_qua_chu = "..."
        self.ket_qua_tin_cay = 0.0
        self.ket_qua_nguon = "..."
        self.last_rendered_frame = None

        self.frame_to_process = None
        self.lock = threading.Lock()
        self.is_running = True

        self.thread = threading.Thread(target=self._ai_worker, daemon=True)
        self.thread.start()

    def cai_dat_che_do_nhanh(self, bat=True):
        with self.lock:
            self.che_do_turbo = bat
            if bat:
                self.moc_frame_can_giu = 2
                self.thoi_gian_dong_bang = 0.0
            else:
                self.moc_frame_can_giu = 12
                self.thoi_gian_dong_bang = 1.2

    def reset_ket_qua(self):
        with self.lock:
            self.ket_qua_chu = "..."
            self.ket_qua_tin_cay = 0.0
            self.ket_qua_nguon = "..."
            self.last_rendered_frame = None
            self.dict_stabilizers.clear()
            self.chu_dang_tich_luy = None
            self.so_frame_da_giu = 0
            self.trang_thai = "TINH"
            self.frames_rec = []
            self.bo_dem_dung_tay = 0

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

        hands = self.mp_hands.Hands(max_num_hands=2, model_complexity=1, min_detection_confidence=0.70,
                                    min_tracking_confidence=0.75)

        while self.is_running:
            try:
                frame_xu_ly = None
                with self.lock:
                    if self.frame_to_process is not None:
                        frame_xu_ly = self.frame_to_process
                        self.frame_to_process = None

                if frame_xu_ly is None:
                    time.sleep(0.005);
                    continue

                frame_ve_san = frame_xu_ly.copy()
                h_f, w_f, _ = frame_xu_ly.shape
                rgb = cv2.cvtColor(frame_xu_ly, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                result = hands.process(rgb)
                rgb.flags.writeable = True

                chu_tam, tin_cay_tam, nguon_tam = self.ket_qua_chu, self.ket_qua_tin_cay, self.ket_qua_nguon
                thoi_gian_hien_tai = time.time()

                if result.multi_hand_landmarks:
                    toa_do_126, co_tay_hien_tai, raw_muot, ds_ve_hud = xu_ly_matran_2_tay_muot(
                        result.multi_hand_landmarks, result.multi_handedness, self.dict_stabilizers
                    )
                    for pts_3d in ds_ve_hud: ve_khung_xuong_sieu_bam(frame_ve_san, pts_3d)

                    dich_chuyen_co_tay = 0.0
                    if co_tay_hien_tai:
                        self.quy_dao_co_tay.append(co_tay_hien_tai)
                        if len(self.quy_dao_co_tay) == 5:
                            dx = self.quy_dao_co_tay[-1][0] - self.quy_dao_co_tay[0][0]
                            dy = self.quy_dao_co_tay[-1][1] - self.quy_dao_co_tay[0][1]
                            dich_chuyen_co_tay = math.sqrt(dx ** 2 + dy ** 2)

                    if self.toa_do_frame_truoc is None:
                        van_toc_126 = [0.0] * 126
                    else:
                        van_toc_126 = [toa_do_126[i] - self.toa_do_frame_truoc[i] for i in range(126)]

                    dac_trung_252 = toa_do_126 + van_toc_126
                    self.toa_do_frame_truoc = toa_do_126.copy()

                    # --- TÍNH TOÁN DỰ ĐOÁN TĨNH TRƯỚC ĐỂ LÀM THAM CHIẾU QUYẾT ĐỊNH ---
                    chu_thô, conf_thô = "?", 0.0
                    finger_states = get_finger_states_chuan(raw_muot) if raw_muot is not None else [0] * 5

                    if self.model_tinh is not None and any(v != 0.0 for v in toa_do_126):
                        try:
                            t_trai, t_phai = toa_do_126[:63], toa_do_126[63:]
                            p1, p2 = self.model_tinh.predict_proba([toa_do_126])[0], \
                            self.model_tinh.predict_proba([t_phai + t_trai])[0]
                            i1, i2 = p1.argmax(), p2.argmax()
                            if p1[i1] >= p2[i2]:
                                c_raw, f_conf = self.model_tinh.classes_[i1], float(p1[i1])
                            else:
                                c_raw, f_conf = self.model_tinh.classes_[i2], float(p2[i2])
                            hop_le, he_so = kiem_duyet_giai_phau_hoc(c_raw, finger_states)
                            chu_thô = c_raw if hop_le else f"{c_raw} (Sai Dáng)"
                            conf_thô = min(0.99, f_conf * he_so)
                        except ValueError:
                            chu_thô = "[Sai Cột Tĩnh]"

                    # --- PHẢN XẠ 1: BẺ KHÓA ĐÓNG BĂNG KHI GIƠ CHỮ TĨNH NÉT ---
                    if self.trang_thai == "DONG_BANG":
                        if conf_thô >= 0.80 or (
                                thoi_gian_hien_tai - self.thoi_diem_dong_bang > self.thoi_gian_dong_bang):
                            self.trang_thai = "TINH"
                            self.frames_rec = []
                            self.bo_dem_dung_tay = 0
                        else:
                            with self.lock:
                                self.last_rendered_frame = frame_ve_san
                            continue

                    # --- PHẢN XẠ 2: CƠ CHẾ NGẮT SỚM (EARLY EXIT) TRONG KHI ĐANG GHI VIDEO ĐỘNG ---
                    if self.trang_thai == "DANG_REC":
                        self.frames_rec.append(dac_trung_252)
                        so_frame_da_ghi = len(self.frames_rec)

                        # Nếu tay đã dừng di chuyển và đang tạo dáng chữ Tĩnh nét -> Ngắt lập tức!
                        if dich_chuyen_co_tay < 0.022 and conf_thô >= 0.65:
                            self.bo_dem_dung_tay += 1
                            if self.bo_dem_dung_tay >= 4:  # Chỉ cần 4 frame đứng im là bẻ lái sang Tĩnh
                                self.trang_thai = "TINH"
                                self.frames_rec = []
                                self.bo_dem_dung_tay = 0
                        else:
                            self.bo_dem_dung_tay = 0

                        # Nếu sau khi kiểm tra mà vẫn tiếp tục ghi hình
                        if self.trang_thai == "DANG_REC":
                            chu_tam, tin_cay_tam, nguon_tam = "...", 0.0, f"REC: {so_frame_da_ghi}/{SO_FRAME_LSTM}"
                            if so_frame_da_ghi == SO_FRAME_LSTM:
                                if self.model_dong is not None:
                                    try:
                                        X_tensor = torch.tensor([self.frames_rec], dtype=torch.float32).to(self.device)
                                        with torch.no_grad():
                                            outputs = self.model_dong(X_tensor)
                                        vi_tri_dong = torch.softmax(outputs, dim=1).cpu().numpy()[0].argmax()
                                        tin_cay_dong, nhan_du_doan = float(
                                            torch.softmax(outputs, dim=1).cpu().numpy()[0][vi_tri_dong]), \
                                        self.nhan_dong[vi_tri_dong]

                                        if tin_cay_dong >= NGUONG_TIN_CAY_DONG and nhan_du_doan.upper() not in ["NONE",
                                                                                                                ""]:
                                            chu_tam, tin_cay_tam, nguon_tam = nhan_du_doan, tin_cay_dong, "DONG"
                                            self.trang_thai, self.thoi_diem_dong_bang = "DONG_BANG", time.time()
                                        else:
                                            self.trang_thai, self.frames_rec = "TINH", []
                                            chu_tam, tin_cay_tam, nguon_tam = chu_thô, conf_thô, "TINH (Drop)"
                                    except Exception:
                                        self.trang_thai, self.frames_rec = "TINH", []
                                else:
                                    self.trang_thai, self.frames_rec = "TINH", []

                            with self.lock:
                                self.ket_qua_chu, self.ket_qua_tin_cay, self.ket_qua_nguon = chu_tam, tin_cay_tam, nguon_tam
                                self.last_rendered_frame = frame_ve_san
                            continue

                    # --- TRẠNG THÁI CHỮ TĨNH GỐC ---
                    if self.trang_thai == "TINH":
                        # Ngưỡng vận tốc được siết chặt và bổ sung điều kiện lọc tự tin chữ Tĩnh
                        if not self.che_do_turbo and dich_chuyen_co_tay > 0.085 and conf_thô < 0.70:
                            self.trang_thai = "DANG_REC"
                            self.frames_rec = [dac_trung_252]
                            self.bo_dem_dung_tay = 0
                            chu_tam, nguon_tam, tin_cay_tam = "...", "REC: 1", 0.0
                        else:
                            if conf_thô >= NGUONG_TIN_CAY_TINH and "(Sai" not in chu_thô and "[" not in chu_thô:
                                if chu_thô == self.chu_dang_tich_luy:
                                    self.so_frame_da_giu += 1
                                    self.bo_dem_tha_thu = 2
                                else:
                                    if self.bo_dem_tha_thu > 0:
                                        self.bo_dem_tha_thu -= 1
                                    else:
                                        self.chu_dang_tich_luy, self.so_frame_da_giu, self.bo_dem_tha_thu = chu_thô, 1, 2

                                phan_tram = min(100, int((self.so_frame_da_giu / self.moc_frame_can_giu) * 100))
                                if self.so_frame_da_giu < self.moc_frame_can_giu:
                                    chu_tam, tin_cay_tam, nguon_tam = self.chu_dang_tich_luy, 0.50, f"HOLDING... [{phan_tram}%]"
                                else:
                                    chu_tam, tin_cay_tam, nguon_tam = self.chu_dang_tich_luy, 1.0, "TINH"
                                    self.trang_thai, self.thoi_diem_dong_bang = "DONG_BANG", time.time()
                                    self.chu_dang_tich_luy, self.so_frame_da_giu = None, 0
                            else:
                                if self.bo_dem_tha_thu > 0:
                                    self.bo_dem_tha_thu -= 1
                                else:
                                    self.so_frame_da_giu = max(0, self.so_frame_da_giu - 1)
                                    if self.so_frame_da_giu == 0: self.chu_dang_tich_luy = None
                                chu_tam, nguon_tam, tin_cay_tam = chu_thô if "[" in chu_thô else "?", "..." if "[" not in chu_thô else "ERR", 0.0

                else:
                    self.dict_stabilizers.clear();
                    self.quy_dao_co_tay.clear();
                    self.toa_do_frame_truoc = None
                    self.trang_thai, self.frames_rec = "TINH", []
                    self.chu_dang_tich_luy, self.so_frame_da_giu = None, 0
                    self.bo_dem_dung_tay = 0
                    chu_tam, tin_cay_tam, nguon_tam = "...", 0.0, "..."

                with self.lock:
                    self.ket_qua_chu, self.ket_qua_tin_cay, self.ket_qua_nguon = chu_tam, tin_cay_tam, nguon_tam
                    self.last_rendered_frame = frame_ve_san

            except Exception:
                time.sleep(0.01)

    def xu_ly_frame(self, frame, anh_mau=None):
        with self.lock:
            self.frame_to_process = frame.copy()
        with self.lock:
            chu, tin_cay, nguon, frame_baked = self.ket_qua_chu, self.ket_qua_tin_cay, self.ket_qua_nguon, self.last_rendered_frame
        if frame_baked is not None:
            h_f, w_f, _ = frame.shape
            frame_ket_qua = cv2.resize(frame_baked, (w_f, h_f))
        else:
            frame_ket_qua = frame.copy()
        if anh_mau is not None: frame_ket_qua = chen_anh_png_mo(frame_ket_qua, anh_mau, x=50, y=50, do_mo=0.6)
        return frame_ket_qua, chu, tin_cay, nguon

    def dung(self):
        self.is_running = False