import os
import warnings
import cv2
import mediapipe as mp
import numpy as np

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

# Cấu hình dữ liệu chuỗi động
KY_HIEU_DONG = ['J', 'Z', 'None']
SO_FRAME = 45  # 30 khung hình liên tiếp cho 1 cử chỉ (~1 giây)
SO_MAU_MOI_KY_HIEU = 500  # Đảm bảo đủ dữ liệu mẫu cho Deep Learning
THU_MUC_DATASET = 'dataset_dong'

def tao_style_landmark(mp_draw):
    """Đổ màu xương tay chuyên nghiệp"""
    COLOR_PALM   = (255, 255, 255)
    COLOR_THUMB  = (0,   0,   255)
    COLOR_INDEX  = (0,   255, 255)
    COLOR_MIDDLE = (0,   255,   0)
    COLOR_RING   = (255,   0,   0)
    COLOR_PINKY  = (255,   0, 255)

    style_diem = {}
    style_diem[0] = mp_draw.DrawingSpec(color=COLOR_PALM, circle_radius=5)
    for i in range(1,  5): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_THUMB,  circle_radius=4)
    for i in range(5,  9): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_INDEX,  circle_radius=4)
    for i in range(9,  13):style_diem[i] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, circle_radius=4)
    for i in range(13, 17):style_diem[i] = mp_draw.DrawingSpec(color=COLOR_RING,   circle_radius=4)
    for i in range(17, 21):style_diem[i] = mp_draw.DrawingSpec(color=COLOR_PINKY,  circle_radius=4)

    style_duong = {}
    for conn in [(0,1),(0,5),(5,9),(9,13),(13,17),(0,17)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_PALM, thickness=2)
    for conn in [(1,2),(2,3),(3,4)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_THUMB, thickness=2)
    for conn in [(5,6),(6,7),(7,8)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_INDEX, thickness=2)
    for conn in [(9,10),(10,11),(11,12)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, thickness=2)
    for conn in [(13,14),(14,15),(15,16)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_RING, thickness=2)
    for conn in [(17,18),(18,19),(19,20)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_PINKY, thickness=2)

    return style_diem, style_duong

def trich_xuat_toa_do(hand_landmarks):
    """Hàm lõi chuẩn hóa không gian gốc tương đối và tỉ lệ hình học"""
    goc_x = hand_landmarks.landmark[0].x
    goc_y = hand_landmarks.landmark[0].y
    goc_z = hand_landmarks.landmark[0].z

    toa_do = []
    for diem in hand_landmarks.landmark:
        toa_do.extend([diem.x - goc_x, diem.y - goc_y, diem.z - goc_z])

    max_val = max(abs(v) for v in toa_do)
    if max_val == 0: max_val = 1.0

    return [v / max_val for v in toa_do]

def chay_thu_thap_dong():
    print("\n--- THU THẬP DỮ LIỆU ĐỘNG TỐI ƯU ---")
    for ky_hieu in KY_HIEU_DONG:
        os.makedirs(os.path.join(THU_MUC_DATASET, ky_hieu), exist_ok=True)

    mp_hands  = mp.solutions.hands
    hands     = mp_hands.Hands(
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )
    mp_draw   = mp.solutions.drawing_utils
    style_diem, style_duong = tao_style_landmark(mp_draw)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

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

        toa_do_hien_tai = []

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=style_diem,
                    connection_drawing_spec=style_duong
                )
                toa_do_hien_tai = trich_xuat_toa_do(hand_landmarks)

        if dang_ghi:
            if len(toa_do_hien_tai) == 63:
                if toa_do_frame_truoc is None:
                    van_toc = [0.0] * 63
                else:
                    van_toc = [
                        toa_do_hien_tai[i] - toa_do_frame_truoc[i]
                        for i in range(63)
                    ]
                dac_trung = toa_do_hien_tai + van_toc
                buffer_ghi.append(dac_trung)
                toa_do_frame_truoc = toa_do_hien_tai.copy()
                so_frame_da_ghi += 1
            else:
                print("[Huy Lan Ghi] Mat dau tay giua chung")
                dang_ghi = False
                buffer_ghi = []
                so_frame_da_ghi = 0

                toa_do_frame_truoc = None

            if so_frame_da_ghi >= SO_FRAME:
                mang_mau = np.array(buffer_ghi)
                ten_file = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai, f'{so_mau_hien_co}.npy')
                np.save(ten_file, mang_mau)
                so_mau_hien_co += 1
                print(f"  [ĐÃ LƯU] {ky_hieu_hien_tai} — Mẫu {so_mau_hien_co}/{SO_MAU_MOI_KY_HIEU}")

                dang_ghi = False
                buffer_ghi = []
                so_frame_da_ghi = 0

                if so_mau_hien_co >= SO_MAU_MOI_KY_HIEU:
                    chi_so_ky_hieu += 1
                    if chi_so_ky_hieu < len(KY_HIEU_DONG):
                        ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]
                        thu_muc_ky_hieu = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai)
                        so_mau_hien_co = len([f for f in os.listdir(thu_muc_ky_hieu) if f.endswith('.npy')])
                        print(f"\n=> ĐỔI SANG KÝ HIỆU: [{ky_hieu_hien_tai}]")
                    else:
                        print("\n=== HOÀN THÀNH TOÀN BỘ QUÁ TRÌNH THU THẬP DỮ LIỆU ĐỘNG ===")
                        break

        # Giao diện trực quan
        w_frame = frame.shape[1]
        cv2.rectangle(frame, (0, 0), (w_frame, 115), (10, 10, 20), cv2.FILLED)
        cv2.putText(frame, f"KY HIEU [{ky_hieu_hien_tai}]  |  {so_mau_hien_co}/{SO_MAU_MOI_KY_HIEU} mau", (16, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        if dang_ghi:
            ti_le = so_frame_da_ghi / SO_FRAME
            cv2.putText(frame, f"DANG GHI: {so_frame_da_ghi}/{SO_FRAME} frame", (16, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)
            cv2.rectangle(frame, (16, 92), (16 + w_frame - 32, 108), (40, 40, 50), cv2.FILLED)
            cv2.rectangle(frame, (16, 92), (16 + int((w_frame - 32) * ti_le), 108), (0, 165, 255), cv2.FILLED)
        else:
            cv2.putText(frame, "SPACE: Bat dau ghi | N: Bo qua ki hieu | ESC: Thoat", (16, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)
            mau_tay = (0, 255, 100) if len(toa_do_hien_tai) == 63 else (0, 100, 255)
            trang_thai_tay = "TAY OK - San sang" if len(toa_do_hien_tai) == 63 else "Khong thay ban tay!"
            cv2.putText(frame, trang_thai_tay, (16, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.45, mau_tay, 1)

        cv2.imshow('Thu Thap Dong (J, Z)', frame)
        phim = cv2.waitKey(1) & 0xFF

        if phim == 27: break
        elif phim == ord('n'):
            chi_so_ky_hieu += 1
            if chi_so_ky_hieu < len(KY_HIEU_DONG):
                ky_hieu_hien_tai = KY_HIEU_DONG[chi_so_ky_hieu]
                thu_muc_ky_hieu = os.path.join(THU_MUC_DATASET, ky_hieu_hien_tai)
                so_mau_hien_co = len([f for f in os.listdir(thu_muc_ky_hieu) if f.endswith('.npy')])
                dang_ghi = False
                buffer_ghi = []
                so_frame_da_ghi = 0
        elif phim == 32:
            if not dang_ghi and len(toa_do_hien_tai) == 63:
                dang_ghi = True
                buffer_ghi = []
                so_frame_da_ghi = 0


    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    chay_thu_thap_dong()