import os
import sys
import warnings
import cv2
import mediapipe as mp
import numpy as np

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

# Khớp tuyệt đối với tên thư mục của bạn
KY_HIEU_DONG = ['J', 'Z', 'TEN', 'TUOI', 'XIN_CHAO', 'CAM_ON', 'XIN_LOI', 'NONE']
SO_FRAME = 45
SO_MAU_MOI_KY_HIEU = 100
THU_MUC_DATASET = 'dataset_dong'


# ============================================================================
# 1. BỘ NHÚN DYNAMIC KALMAN: CHỐNG RUNG (ĐỒNG NHẤT VỚI ENGINE_V2)
# ============================================================================
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


# ============================================================================
# 2. LÕI TOÁN HỌC KAZUHITO TAKAHASHI (Tịnh tiến & Chuẩn hóa Absolute)
# ============================================================================
def trich_xuat_1_tay_kazuhito(smoothed_pts, w_img, h_img):
    temp_pts = []
    for p in smoothed_pts:
        px = min(int(p[0] * w_img), w_img - 1)
        py = min(int(p[1] * h_img), h_img - 1)
        pz = int(p[2] * w_img)
        temp_pts.append([px, py, pz])

    base_x, base_y, base_z = temp_pts[0][0], temp_pts[0][1], temp_pts[0][2]
    flat_list = []
    for x, y, z in temp_pts:
        flat_list.extend([x - base_x, y - base_y, z - base_z])

    max_val = max(list(map(abs, flat_list)))
    if max_val < 1.0: max_val = 1.0

    return [float(v) / max_val for v in flat_list]


# ============================================================================
# 3. LOGIC HANDSIDE: Phân rẽ Trái - Phải Chuẩn Mực
# ============================================================================
def trich_xuat_toa_do_2_tay_kazuhito(multi_hand_landmarks, multi_handedness, w_img, h_img, dict_stab):
    tay_trai, tay_phai = [0.0] * 63, [0.0] * 63
    if not multi_hand_landmarks:
        return tay_trai + tay_phai

    tays = []
    for i, lm in enumerate(multi_hand_landmarks):
        if multi_handedness[i].classification[0].score < 0.65: continue

        label = multi_handedness[i].classification[0].label
        if label not in dict_stab:
            dict_stab[label] = DynamicLandmarkStabilizer()

        pts_muot = dict_stab[label].lam_muot(lm)
        norm_63 = trich_xuat_1_tay_kazuhito(pts_muot, w_img, h_img)

        tays.append({
            "x_root": pts_muot[0][0],
            "norm": norm_63,
            "label": label,
            "pts_3d": pts_muot
        })

    tays.sort(key=lambda x: x["x_root"])

    if len(tays) == 1:
        if tays[0]["label"] == 'Left':
            tay_phai = tays[0]["norm"]
        else:
            tay_trai = tays[0]["norm"]
    elif len(tays) >= 2:
        t0, t1 = tays[0], tays[1]
        tay_trai, tay_phai = t0["norm"], t1["norm"]

    return tay_trai + tay_phai, tays


# ============================================================================
# 4. GIAO DIỆN BỘ KHUNG XƯƠNG CYBERNETIC (GIỐNG ENGINE V2)
# ============================================================================
def ve_khung_xuong_sieu_bam(frame, pts_3d):
    h, w, _ = frame.shape
    pts_px = [(int(x * w), int(y * h)) for x, y, z in pts_3d]

    KET_NOI = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12),
               (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]

    for a, b in KET_NOI:
        cv2.line(frame, pts_px[a], pts_px[b], (240, 240, 245), 2, cv2.LINE_AA)

    for i, pt in enumerate(pts_px):
        if i in [4, 8, 12, 16, 20]:
            cv2.circle(frame, pt, 5, (0, 200, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 8, (0, 200, 255), 1, cv2.LINE_AA)
        elif i == 0:
            cv2.circle(frame, pt, 6, (255, 255, 255), -1, cv2.LINE_AA)
        else:
            cv2.circle(frame, pt, 4, (0, 230, 115), -1, cv2.LINE_AA)


# ============================================================================
# 5. VÒNG LẶP HÚT DATA TRỰC TIẾP
# ============================================================================
def chay_thu_thap_dong():
    print("\n--- THU THẬP DỮ LIỆU ĐỘNG (BẢN KAZUHITO + CHỐNG RUNG) ---")
    for ky_hieu in KY_HIEU_DONG:
        os.makedirs(os.path.join(THU_MUC_DATASET, ky_hieu), exist_ok=True)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=2,
        model_complexity=1,
        min_detection_confidence=0.70,
        min_tracking_confidence=0.75
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    chi_so_ky_hieu = 0
    ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]
    thu_muc_ky_hieu = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai)
    so_mau_hien_co = len([f for f in os.listdir(thu_muc_ky_hieu) if f.endswith('.npy')])

    dang_ghi = False
    buffer_ghi = []
    so_frame_da_ghi = 0
    toa_do_frame_truoc = None
    dict_stab = {}

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        h_f, w_f, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        result = hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        toa_do_126 = []

        if result.multi_hand_landmarks:
            toa_do_126, ds_tays = trich_xuat_toa_do_2_tay_kazuhito(
                result.multi_hand_landmarks, result.multi_handedness, w_f, h_f, dict_stab
            )
            # Vẽ bộ xương Cybernetic
            for t in ds_tays: ve_khung_xuong_sieu_bam(frame, t["pts_3d"])
        else:
            toa_do_126 = [0.0] * 126
            dict_stab.clear()

        co_tay = any(v != 0.0 for v in toa_do_126)

        if dang_ghi:
            if co_tay:
                if toa_do_frame_truoc is None:
                    van_toc_126 = [0.0] * 126
                else:
                    van_toc_126 = [toa_do_126[i] - toa_do_frame_truoc[i] for i in range(126)]

                # MẢNG SIÊU CẤP: 126 tĩnh + 126 vận tốc = 252 CHIỀU!
                dac_trung_252 = toa_do_126 + van_toc_126
                buffer_ghi.append(dac_trung_252)
                toa_do_frame_truoc = toa_do_126.copy()
                so_frame_da_ghi += 1
            else:
                print("[Hủy Ghi] Mất tay giữa chừng")
                dang_ghi = False;
                buffer_ghi = [];
                so_frame_da_ghi = 0;
                toa_do_frame_truoc = None

            if so_frame_da_ghi >= SO_FRAME:
                mang_mau = np.array(buffer_ghi)
                ten_file = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai, f'{so_mau_hien_co}.npy')
                np.save(ten_file, mang_mau)
                so_mau_hien_co += 1
                print(f"  [ĐÃ LƯU] {ky_hieu_hien_tai} — Mẫu {so_mau_hien_co}/{SO_MAU_MOI_KY_HIEU}")
                dang_ghi = False;
                buffer_ghi = [];
                so_frame_da_ghi = 0

                if so_mau_hien_co >= SO_MAU_MOI_KY_HIEU:
                    chi_so_ky_hieu += 1
                    if chi_so_ky_hieu < len(KY_HIEU_DONG):
                        ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]
                        thu_muc_ky_hieu = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai)
                        so_mau_hien_co = len([f for f in os.listdir(thu_muc_ky_hieu) if f.endswith('.npy')])
                        print(f"\n=> ĐỔI SANG: [{ky_hieu_hien_tai}]")
                    else:
                        print("\n=== HOÀN THÀNH ===");
                        break

        cv2.rectangle(frame, (0, 0), (w_f, 115), (10, 10, 20), cv2.FILLED)
        cv2.putText(frame, f"KY HIEU [{ky_hieu_hien_tai}]  |  {so_mau_hien_co}/{SO_MAU_MOI_KY_HIEU} mau", (16, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        if dang_ghi:
            ti_le = so_frame_da_ghi / SO_FRAME
            cv2.putText(frame, f"DANG GHI: {so_frame_da_ghi}/{SO_FRAME} frame", (16, 78), cv2.FONT_HERSHEY_SIMPLEX,
                        0.65, (0, 165, 255), 2)
            cv2.rectangle(frame, (16, 92), (16 + int((w_f - 32) * ti_le), 108), (0, 165, 255), cv2.FILLED)
        else:
            cv2.putText(frame, "Bam SPACE de ghi | Bam N de bo qua", (16, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (180, 180, 180), 1)

        cv2.imshow('Thu Thap LSTM Kazuhito', frame)
        phim = cv2.waitKey(1) & 0xFF
        if phim == 27:
            break
        elif phim == ord('n'):
            chi_so_ky_hieu += 1
            if chi_so_ky_hieu < len(KY_HIEU_DONG): ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]; so_mau_hien_co = 0
        elif phim == 32:
            if not dang_ghi and co_tay: dang_ghi = True; buffer_ghi = []; so_frame_da_ghi = 0

    cap.release();
    cv2.destroyAllWindows()


if __name__ == "__main__":
    chay_thu_thap_dong()