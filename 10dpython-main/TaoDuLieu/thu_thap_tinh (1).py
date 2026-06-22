import csv
import os
import warnings
import cv2
import mediapipe as mp

warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# --- CẤU HÌNH ĐƯỜNG DẪN TỐI ƯU ---
# Neo tuyệt đối ra ngoài Root (nơi chứa main.py) để file CSV không bị đi lạc
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT_DIR, "dataset_tinh.csv")

# TỔNG HỢP 27 NHẪN: BẢNG CHỮ CÁI + NÚT CÁCH
DANH_SACH_NHAN = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SPACE"]
SO_MAU_MUC_TIEU = 150  # 150 frame ~ giữ tay im 5 giây là xong 1 chữ


def trich_xuat_toa_do_2_tay(multi_hand_landmarks, multi_handedness):
    """Hàm bọc lót: Luôn xuất ra mảng cố định 126 tọa độ (63 Trái + 63 Phải)"""
    tay_trai = [0.0] * 63
    tay_phai = [0.0] * 63

    if not multi_hand_landmarks or not multi_handedness:
        return tay_trai + tay_phai

    for i, hand_lm in enumerate(multi_hand_landmarks):
        nhan_tay = multi_handedness[i].classification[0].label

        goc_x = hand_lm.landmark[0].x
        goc_y = hand_lm.landmark[0].y
        goc_z = hand_lm.landmark[0].z
        toa_do = []
        for diem in hand_lm.landmark:
            toa_do.extend([diem.x - goc_x, diem.y - goc_y, diem.z - goc_z])

        max_val = max(abs(v) for v in toa_do) if toa_do else 1.0
        if max_val == 0:
            max_val = 1.0
        toa_do_norm = [v / max_val for v in toa_do]

        # Camera flip nên 'Left' của AI chính là tay Phải thật của bạn
        if nhan_tay == "Left":
            tay_phai = toa_do_norm
        else:
            tay_trai = toa_do_norm

    return tay_trai + tay_phai


def kiem_tra_tien_do_csv():
    """Tự động kiểm đếm xem trong file CSV mỗi chữ đã có bao nhiêu dòng"""
    dem = {nhan: 0 for nhan in DANH_SACH_NHAN}

    # Nếu chưa có file CSV -> Tạo file mới kèm Header 127 cột
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = ["Nhan"] + [f"coord_{i}" for i in range(126)]
            writer.writerow(header)
        return dem

    # Nếu đã có -> Đọc lướt qua để đếm số lượng
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Bỏ qua dòng tiêu đề
        for row in reader:
            if row and row[0] in dem:
                dem[row[0]] += 1
    return dem


def chay_thu_thap_hoan_chinh():
    print(
        "\n=== KHỞI ĐỘNG CỖ MÁY THU THẬP TĨNH HOÀN CHỈNH (A-Z & SPACE) ==="
    )

    dem_tien_do = kiem_tra_tien_do_csv()

    hoan_thanh = [
        n for n in DANH_SACH_NHAN if dem_tien_do[n] >= SO_MAU_MUC_TIEU
    ]
    con_thieu = [
        n for n in DANH_SACH_NHAN if dem_tien_do[n] < SO_MAU_MUC_TIEU
    ]

    print(
        f"[*] Đã thu thập đủ ({len(hoan_thanh)}/{len(DANH_SACH_NHAN)}): {', '.join(hoan_thanh) if hoan_thanh else 'Chưa có'}"
    )
    print(f"[*] Các chữ cần thu thập: {', '.join(con_thieu)}\n")

    # THẦN CHÚ: Tự động trỏ ngay vào chữ cái "CHƯA XONG" đầu tiên
    chi_so = 0
    for i, n in enumerate(DANH_SACH_NHAN):
        if dem_tien_do[n] < SO_MAU_MUC_TIEU:
            chi_so = i
            break

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7
    )
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        nhan_hien_tai = DANH_SACH_NHAN[chi_so]
        so_mau_hien_co = dem_tien_do[nhan_hien_tai]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        toa_do_126 = []
        if result.multi_hand_landmarks:
            for hand_lm in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_lm, mp_hands.HAND_CONNECTIONS
                )
            toa_do_126 = trich_xuat_toa_do_2_tay(
                result.multi_hand_landmarks, result.multi_handedness
            )

        # --- VẼ GIAO DIỆN BẢNG ĐIỀU KHIỂN TRỰC QUAN ---
        cv2.rectangle(frame, (10, 10), (740, 140), (15, 15, 25), cv2.FILLED)

        cv2.putText(
            frame,
            f"MUC TIEU: [ {nhan_hien_tai} ]  ({chi_so + 1}/{len(DANH_SACH_NHAN)})",
            (25, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

        # Trực quan hóa bằng màu: Đủ 150 mẫu chuyển sang Xanh lá
        mau_thong_bao = (
            (0, 255, 0) if so_mau_hien_co >= SO_MAU_MUC_TIEU else (255, 255, 255)
        )
        cv2.putText(
            frame,
            f"Da ghi nhan: {so_mau_hien_co}/{SO_MAU_MUC_TIEU} mau",
            (25, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            mau_thong_bao,
            2,
        )

        cv2.putText(
            frame,
            "GIU 'SPACE': Luu  |  'N': Bo qua  |  'P': Quay lai  |  'ESC': Thoat",
            (25, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (180, 180, 180),
            1,
        )

        if so_mau_hien_co >= SO_MAU_MUC_TIEU:
            cv2.putText(
                frame,
                "[ ĐÃ ĐỦ SỐ LƯỢNG! BẤM 'N' ĐỂ SANG CHỮ KẾ ]",
                (25, 185),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        cv2.imshow("Thu Thap Tinh (A-Z & SPACE)", frame)

        # --- LẮNG NGHE PHÍM ĐIỀU KHIỂN ---
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC: Thoát
            break
        elif key == ord("n"):  # N: Nhảy cóc sang chữ kế tiếp
            chi_so = (chi_so + 1) % len(DANH_SACH_NHAN)
        elif key == ord("p"):  # P: Lùi lại chữ vừa đi qua
            chi_so = (chi_so - 1) % len(DANH_SACH_NHAN)
        elif key == 32:  # BẤM GIỮ PHÍM SPACE ĐỂ GHI DATA VÀO CSV
            if toa_do_126 and any(v != 0.0 for v in toa_do_126):
                with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([nhan_hien_tai] + toa_do_126)

                dem_tien_do[nhan_hien_tai] += 1

                # Nếu vừa chạm mốc 150, tự động lướt tìm chữ "chưa xong" tiếp theo
                if dem_tien_do[nhan_hien_tai] == SO_MAU_MUC_TIEU:
                    print(
                        f" -> [XONG] Đã thu đủ {SO_MAU_MUC_TIEU} mẫu cho chữ '{nhan_hien_tai}'!"
                    )
                    for _ in range(len(DANH_SACH_NHAN)):
                        chi_so = (chi_so + 1) % len(DANH_SACH_NHAN)
                        if dem_tien_do[DANH_SACH_NHAN[chi_so]] < SO_MAU_MUC_TIEU:
                            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    chay_thu_thap_hoan_chinh()