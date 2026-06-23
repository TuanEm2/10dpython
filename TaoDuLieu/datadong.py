import os
import warnings
import cv2
import mediapipe as mp
import numpy as np

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

# --- CẤU HÌNH ĐƯỜNG DẪN TỐI ƯU ---
# Neo trỏ ra ngoài Root (nơi để main.py) để tự động tìm/tạo đúng thư mục
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_NGUON = os.path.join(ROOT_DIR, 'video_goc')
THU_MUC_DICH  = os.path.join(ROOT_DIR, 'dataset_dong')

SO_FRAME_CHUAN = 45
SO_TOA_DO_TINH = 126  # 63 Trái + 63 Phải
SO_TOA_DO_DONG = 252  # 126 tĩnh + 126 vận tốc


def loc_ban_tay_ghost(multi_hand_landmarks, multi_handedness):
    """Bộ lọc NMS: Khử 'bàn tay ma' do MediaPipe nhìn 1 tay thành 2"""
    if not multi_hand_landmarks or not multi_handedness:
        return []

    tay_tho = []
    for i, lm in enumerate(multi_hand_landmarks):
        score = multi_handedness[i].classification[0].score
        label = multi_handedness[i].classification[0].label
        cx = sum(p.x for p in lm.landmark) / 21.0
        cy = sum(p.y for p in lm.landmark) / 21.0
        tay_tho.append({"lm": lm, "score": score, "label": label, "cx": cx, "cy": cy})

    tay_tho.sort(key=lambda item: item["score"], reverse=True)

    tay_sach = []
    for item in tay_tho:
        if item["score"] < 0.65: continue
        trung_lap = False
        for da_chon in tay_sach:
            khoang_cach = ((item["cx"] - da_chon["cx"])**2 + (item["cy"] - da_chon["cy"])**2)**0.5
            if khoang_cach < 0.15:
                trung_lap = True; break
        if not trung_lap:
            tay_sach.append(item)

    return tay_sach


def trich_xuat_toa_do_2_tay(danh_sach_tay_sach):
    """Xuất ra mảng 126 tọa độ tĩnh chuẩn mực từ danh sách tay đã lọc sạch"""
    tay_trai = [0.0] * 63
    tay_phai = [0.0] * 63

    if not danh_sach_tay_sach:
        return tay_trai + tay_phai

    for item in danh_sach_tay_sach:
        hand_lm = item["lm"]
        nhan_tay = item["label"]

        gx, gy, gz = hand_lm.landmark[0].x, hand_lm.landmark[0].y, hand_lm.landmark[0].z
        toa_do = []
        for diem in hand_lm.landmark:
            toa_do.extend([diem.x - gx, diem.y - gy, diem.z - gz])

        max_val = max(abs(v) for v in toa_do) if toa_do else 1.0
        if max_val == 0: max_val = 1.0
        toa_do_norm = [v / max_val for v in toa_do]

        # Cam selfie lật ngược ngang nên Left của AI là tay Phải ngoài đời
        if nhan_tay == 'Left':
            tay_phai = toa_do_norm
        else:
            tay_trai = toa_do_norm

    return tay_trai + tay_phai


def xu_ly_mot_video(duong_dan_video, hands_ai):
    cap = cv2.VideoCapture(duong_dan_video)
    buffer_dac_trung = []
    toa_do_frame_truoc = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # NẾU VIDEO QUAY TIKTOK CAM TRƯỚC BỊ NGƯỢC, BỎ DẤU # Ở DÒNG DƯỚI:
        # frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands_ai.process(rgb)

        # 1. Lọc tay sạch bằng NMS
        tay_sach = loc_ban_tay_ghost(result.multi_hand_landmarks, result.multi_handedness)

        # 2. Chiết xuất ra 126 con số tĩnh
        toa_do_126 = trich_xuat_toa_do_2_tay(tay_sach)

        # Chỉ nạp frame khi AI nhìn thấy ít nhất 1 bàn tay
        if any(v != 0.0 for v in toa_do_126):
            if toa_do_frame_truoc is None:
                van_toc_126 = [0.0] * 126
            else:
                van_toc_126 = [toa_do_126[i] - toa_do_frame_truoc[i] for i in range(126)]

            # BƯỚC TIẾN HÓA: 126 tĩnh + 126 vận tốc = 252 CHIỀU!
            dac_trung_252 = toa_do_126 + van_toc_126
            buffer_dac_trung.append(dac_trung_252)
            toa_do_frame_truoc = toa_do_126.copy()

    cap.release()

    tong_frame_thuc_te = len(buffer_dac_trung)
    if tong_frame_thuc_te < 10:
        return None, f"Thất bại (Clip quá ngắn hoặc AI không nhìn thấy bàn tay)"

    # --- ÉP THỜI GIAN VỀ CHUẨN 45 FRAMES ---
    du_lieu_tho = np.array(buffer_dac_trung)
    chi_so_co_gian = np.linspace(0, tong_frame_thuc_te - 1, SO_FRAME_CHUAN).astype(int)
    tensor_hoan_chinh = du_lieu_tho[chi_so_co_gian]  # Output xịn: (45, 252)

    return tensor_hoan_chinh, "Thành công"


def chay_quet_hang_loat():
    print("\n=== BỘ CHUYỂN ĐỔI VIDEO MP4 SANG TENSOR AI (2 TAY - 252 CHIỀU) ===")

    if not os.path.exists(THU_MUC_NGUON):
        os.makedirs(THU_MUC_NGUON)
        print(f"[CẢNH BÁO] Đã tạo thư mục chứa video gốc: '{THU_MUC_NGUON}'")
        print(f"Hãy tạo các thư mục con viết hoa (VD: video_goc/XIN CHAO/) rồi bỏ clip MP4 vào và chạy lại!")
        return

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    danh_sach_tu_khoa = [d for d in os.listdir(THU_MUC_NGUON) if os.path.isdir(os.path.join(THU_MUC_NGUON, d))]

    if not danh_sach_tu_khoa:
        print(f"❌ Không tìm thấy thư mục nhãn ký hiệu nào trong '{THU_MUC_NGUON}'.")
        return

    tong_thanh_cong = 0
    for tu_khoa in danh_sach_tu_khoa:
        thu_muc_con_goc = os.path.join(THU_MUC_NGUON, tu_khoa)
        thu_muc_con_dich = os.path.join(THU_MUC_DICH, tu_khoa)

        os.makedirs(thu_muc_con_dich, exist_ok=True)

        so_mau_hien_co = len([f for f in os.listdir(thu_muc_con_dich) if f.endswith('.npy')])
        file_videos = [f for f in os.listdir(thu_muc_con_goc) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

        print(f"\n📁 Quét nhãn: [{tu_khoa}] ({len(file_videos)} video phát hiện)")

        for file_mp4 in file_videos:
            duong_dan_mp4 = os.path.join(thu_muc_con_goc, file_mp4)
            tensor_out, trang_thai = xu_ly_mot_video(duong_dan_mp4, hands)

            if tensor_out is not None:
                ten_file_npy = os.path.join(thu_muc_con_dich, f"{so_mau_hien_co}.npy")
                np.save(ten_file_npy, tensor_out)
                so_mau_hien_co += 1
                tong_thanh_cong += 1
                print(f"  ├── [OK] Xuất Tensor (45, 252) -> {ten_file_npy}")
            else:
                print(f"  ├── [X] Bỏ qua '{file_mp4}': {trang_thai}")

    print(f"\n🎉 HOÀN TẤT! Đã đóng gói tổng cộng {tong_thanh_cong} ma trận chuẩn 252 chiều vào kho.")


if __name__ == "__main__":
    chay_quet_hang_loat()