import os
import warnings
import cv2
import mediapipe as mp
import csv

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'


def chay_thu_thap():
    print("\n--- BƯỚC 1: THU THẬP DỮ LIỆU TỰ ĐỘNG ---")
    csv_file = 'dataset_tinh.csv'

    # Tạo file CSV với 64 cột (1 Nhãn + 63 Tọa độ)
    if not os.path.exists(csv_file):
        with open(csv_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            header = ['Nhan'] + [f'{axis}{i}' for i in range(21) for axis in ('x', 'y', 'z')]
            writer.writerow(header)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, model_complexity=1, min_detection_confidence=0.8,
                           min_tracking_confidence=0.8)
    mp_draw = mp.solutions.drawing_utils
    # ========================================================
    # CẤU HÌNH MÀU SẮC RIÊNG BIỆT CHO TỪNG NGÓN TAY (Mã BGR)
    # ========================================================
    COLOR_PALM = (255, 255, 255)  # Trắng (Lòng bàn tay)
    COLOR_THUMB = (0, 0, 255)  # Đỏ (Ngón cái)
    COLOR_INDEX = (0, 255, 255)  # Vàng (Ngón trỏ)
    COLOR_MIDDLE = (0, 255, 0)  # Lục (Ngón giữa)
    COLOR_RING = (255, 0, 0)  # Lam (Ngón áp út)
    COLOR_PINKY = (255, 0, 255)  # Tím (Ngón út)

    # 1. Tô màu cho các Khớp (Điểm Landmark)
    custom_landmarks_style = {}
    custom_landmarks_style[0] = mp_draw.DrawingSpec(color=COLOR_PALM, circle_radius=4)
    for i in range(1, 5): custom_landmarks_style[i] = mp_draw.DrawingSpec(color=COLOR_THUMB, circle_radius=4)
    for i in range(5, 9): custom_landmarks_style[i] = mp_draw.DrawingSpec(color=COLOR_INDEX, circle_radius=4)
    for i in range(9, 13): custom_landmarks_style[i] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, circle_radius=4)
    for i in range(13, 17): custom_landmarks_style[i] = mp_draw.DrawingSpec(color=COLOR_RING, circle_radius=4)
    for i in range(17, 21): custom_landmarks_style[i] = mp_draw.DrawingSpec(color=COLOR_PINKY, circle_radius=4)

    # 2. Tô màu cho các Đường nối (Connections)
    custom_connections_style = {}
    # Lòng bàn tay
    for conn in [(0, 1), (0, 5), (5, 9), (9, 13), (13, 17), (0, 17)]:
        custom_connections_style[conn] = mp_draw.DrawingSpec(color=COLOR_PALM, thickness=2)
    # Các ngón
    for conn in [(1, 2), (2, 3), (3, 4)]:
        custom_connections_style[conn] = mp_draw.DrawingSpec(color=COLOR_THUMB, thickness=2)
    for conn in [(5, 6), (6, 7), (7, 8)]:
        custom_connections_style[conn] = mp_draw.DrawingSpec(color=COLOR_INDEX, thickness=2)
    for conn in [(9, 10), (10, 11), (11, 12)]:
        custom_connections_style[conn] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, thickness=2)
    for conn in [(13, 14), (14, 15), (15, 16)]:
        custom_connections_style[conn] = mp_draw.DrawingSpec(color=COLOR_RING, thickness=2)
    for conn in [(17, 18), (18, 19), (19, 20)]:
        custom_connections_style[conn] = mp_draw.DrawingSpec(color=COLOR_PINKY, thickness=2)
    # ========================================================
    cap = cv2.VideoCapture(0)

    bang_chu_cai = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    chi_so_chu = 0
    nhan_dang_day = bang_chu_cai[chi_so_chu]
    so_lan_luu = 0
    MUC_TIEU = 200  # Chỉ tiêu 200 mẫu ảnh cho mỗi chữ cái

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
        toa_do_phang = []

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=custom_landmarks_style,
                    connection_drawing_spec=custom_connections_style
                )

                # CHUẨN HÓA 3D: Lấy cổ tay (điểm 0) làm gốc
                base_x = hand_landmarks.landmark[0].x
                base_y = hand_landmarks.landmark[0].y
                base_z = hand_landmarks.landmark[0].z

                toa_do_tam_thoi = []
                for lm in hand_landmarks.landmark:
                    toa_do_tam_thoi.extend([lm.x - base_x, lm.y - base_y, lm.z - base_z])

                # CHUẨN HÓA TỈ LỆ (Mới thêm)
                max_value = max(list(map(abs, toa_do_tam_thoi)))
                if max_value == 0: max_value = 1.0  # Tránh lỗi chia cho 0

                toa_do_phang = [x / max_value for x in toa_do_tam_thoi]

        # Vẽ giao diện
        cv2.rectangle(frame, (10, 10), (620, 110), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, f"DANG THU: CHU [{nhan_dang_day}] ({chi_so_chu + 1}/26)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (0, 255, 255), 2)
        cv2.putText(frame, f"TIEN DO: {so_lan_luu}/{MUC_TIEU} (Giu SPACE de luu)", (20, 75), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (0, 255, 0), 2)
        cv2.putText(frame, f"BAM 'N' DE BO QUA | 'ESC' THOAT", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (200, 200, 200), 1)
        cv2.imshow('Thu Thap Auto', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break  # ESC
        elif key == ord('n'):  # N: Skip chữ
            chi_so_chu += 1
            if chi_so_chu < len(bang_chu_cai):
                nhan_dang_day = bang_chu_cai[chi_so_chu]
                so_lan_luu = 0
        elif key == 32:  # SPACE: Lưu data
            if len(toa_do_phang) == 63:
                with open(csv_file, mode='a', newline='') as f:
                    csv.writer(f).writerow([nhan_dang_day] + toa_do_phang)
                so_lan_luu += 1

                # Logic tự động chuyển chữ cái
                if so_lan_luu >= MUC_TIEU:
                    chi_so_chu += 1
                    if chi_so_chu < len(bang_chu_cai):
                        nhan_dang_day = bang_chu_cai[chi_so_chu]
                        so_lan_luu = 0
                        print(f"=> Chuyển sang chữ: [{nhan_dang_day}]")
                    else:
                        print("\n=== HOÀN THÀNH TẤT CẢ ===")
                        break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    chay_thu_thap()