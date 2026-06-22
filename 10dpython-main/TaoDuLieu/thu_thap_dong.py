import os
import warnings
import cv2
import mediapipe as mp
import numpy as np

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

# Khớp tuyệt đối với tên thư mục của bạn
KY_HIEU_DONG = ['J', 'Z', 'TEN' , 'TUOI' , 'XIN_CHAO' , 'CAM_ON' , 'XIN_LOI' , 'NONE']
SO_FRAME = 45
SO_MAU_MOI_KY_HIEU = 100  # Để tạm 100 quay cho nhanh test
THU_MUC_DATASET = 'dataset_dong'

def tao_style_landmark(mp_draw):
    COLOR_PALM   = (255, 255, 255); COLOR_THUMB  = (0,   0,   255)
    COLOR_INDEX  = (0,   255, 255); COLOR_MIDDLE = (0,   255,   0)
    COLOR_RING   = (255,   0,   0); COLOR_PINKY  = (255,   0, 255)
    style_diem = {0: mp_draw.DrawingSpec(color=COLOR_PALM, circle_radius=5)}
    for i in range(1, 5): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_THUMB, circle_radius=4)
    for i in range(5, 9): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_INDEX, circle_radius=4)
    for i in range(9, 13): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, circle_radius=4)
    for i in range(13, 17): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_RING, circle_radius=4)
    for i in range(17, 21): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_PINKY, circle_radius=4)
    style_duong = {}
    for conn in [(0,1),(0,5),(5,9),(9,13),(13,17),(0,17)]: style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_PALM, thickness=2)
    for conn in [(1,2),(2,3),(3,4)]: style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_THUMB, thickness=2)
    for conn in [(5,6),(6,7),(7,8)]: style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_INDEX, thickness=2)
    for conn in [(9,10),(10,11),(11,12)]: style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, thickness=2)
    for conn in [(13,14),(14,15),(15,16)]: style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_RING, thickness=2)
    for conn in [(17,18),(18,19),(19,20)]: style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_PINKY, thickness=2)
    return style_diem, style_duong


def trich_xuat_toa_do_2_tay(multi_hand_landmarks, multi_handedness):
    """HÀM BỌC LÓT: Luôn xuất ra đúng 126 tọa độ tĩnh (63 Trái + 63 Phải)"""
    tay_trai = [0.0] * 63
    tay_phai = [0.0] * 63

    if not multi_hand_landmarks or not multi_handedness:
        return tay_trai + tay_phai

    for i, hand_landmarks in enumerate(multi_hand_landmarks):
        nhan_tay = multi_handedness[i].classification[0].label

        goc_x = hand_landmarks.landmark[0].x
        goc_y = hand_landmarks.landmark[0].y
        goc_z = hand_landmarks.landmark[0].z
        toa_do = []
        for diem in hand_landmarks.landmark:
            toa_do.extend([diem.x - goc_x, diem.y - goc_y, diem.z - goc_z])

        max_val = max(abs(v) for v in toa_do) if toa_do else 1.0
        if max_val == 0: max_val = 1.0
        toa_do_norm = [v / max_val for v in toa_do]

        if nhan_tay == 'Left':
            tay_phai = toa_do_norm
        else:
            tay_trai = toa_do_norm

    return tay_trai + tay_phai


def chay_thu_thap_dong():
    print("\n--- THU THẬP DỮ LIỆU ĐỘNG (BẢN 2 TAY - 252 CHIỀU) ---")
    for ky_hieu in KY_HIEU_DONG:
        os.makedirs(os.path.join(THU_MUC_DATASET, ky_hieu), exist_ok=True)

    mp_hands  = mp.solutions.hands
    hands     = mp_hands.Hands(
        max_num_hands=2,  # <--- Bật 2 tay
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_draw   = mp.solutions.drawing_utils
    style_diem, style_duong = tao_style_landmark(mp_draw)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    chi_so_ky_hieu = 0
    ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]
    thu_muc_ky_hieu = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai)
    so_mau_hien_co  = len([f for f in os.listdir(thu_muc_ky_hieu) if f.endswith('.npy')])

    dang_ghi = False
    buffer_ghi = []
    so_frame_da_ghi = 0
    toa_do_frame_truoc = None

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        result = hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        toa_do_126 = []

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=style_diem, connection_drawing_spec=style_duong
                )
            toa_do_126 = trich_xuat_toa_do_2_tay(result.multi_hand_landmarks, result.multi_handedness)
        else:
            toa_do_126 = [0.0] * 126

        # Chỉ ghi khi có ít nhất 1 bàn tay lọt vào cam
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
                dang_ghi = False; buffer_ghi = []; so_frame_da_ghi = 0; toa_do_frame_truoc = None

            if so_frame_da_ghi >= SO_FRAME:
                mang_mau = np.array(buffer_ghi)  # Kích thước xuất xưởng: (45, 252)
                ten_file = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai, f'{so_mau_hien_co}.npy')
                np.save(ten_file, mang_mau)
                so_mau_hien_co += 1
                print(f"  [ĐÃ LƯU] {ky_hieu_hien_tai} — Mẫu {so_mau_hien_co}/{SO_MAU_MOI_KY_HIEU}")
                dang_ghi = False; buffer_ghi = []; so_frame_da_ghi = 0

                if so_mau_hien_co >= SO_MAU_MOI_KY_HIEU:
                    chi_so_ky_hieu += 1
                    if chi_so_ky_hieu < len(KY_HIEU_DONG):
                        ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]
                        thu_muc_ky_hieu = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai)
                        so_mau_hien_co = len([f for f in os.listdir(thu_muc_ky_hieu) if f.endswith('.npy')])
                        print(f"\n=> ĐỔI SANG: [{ky_hieu_hien_tai}]")
                    else:
                        print("\n=== HOÀN THÀNH ==="); break

        w_frame = frame.shape[1]
        cv2.rectangle(frame, (0, 0), (w_frame, 115), (10, 10, 20), cv2.FILLED)
        cv2.putText(frame, f"KY HIEU [{ky_hieu_hien_tai}]  |  {so_mau_hien_co}/{SO_MAU_MOI_KY_HIEU} mau", (16, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        if dang_ghi:
            ti_le = so_frame_da_ghi / SO_FRAME
            cv2.putText(frame, f"DANG GHI: {so_frame_da_ghi}/{SO_FRAME} frame", (16, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)
            cv2.rectangle(frame, (16, 92), (16 + int((w_frame - 32) * ti_le), 108), (0, 165, 255), cv2.FILLED)
        else:
            cv2.putText(frame, "Bấm SPACE de ghi | Bam N de bo qua", (16, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

        cv2.imshow('Thu Thap 2 Tay', frame)
        phim = cv2.waitKey(1) & 0xFF
        if phim == 27: break
        elif phim == ord('n'):
            chi_so_ky_hieu += 1
            if chi_so_ky_hieu < len(KY_HIEU_DONG): ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]; so_mau_hien_co = 0
        elif phim == 32:
            if not dang_ghi and co_tay: dang_ghi = True; buffer_ghi = []; so_frame_da_ghi = 0

    cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    chay_thu_thap_dong()