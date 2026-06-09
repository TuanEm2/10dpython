import os
import warnings
import cv2
import mediapipe as mp
import pickle
import time

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

# ============================================================
# PHẦN 1 — CÁC HẰNG SỐ CẤU HÌNH
# (Viết ở đây để dễ chỉnh, không cần tìm trong code)
# ============================================================

MODEL_FILE = 'model_tinh.pkl'   # Tên file chứa bộ não đã train

# --- Cấu hình DEBOUNCE (chống nhận trùng) ---
# Vấn đề: tay bạn giữ nguyên chữ A trong 1 giây → camera thấy 30 frame
# → nếu không có debounce, nó sẽ lưu "AAAAAAAAAA..." vào từ
# Giải pháp: chỉ lưu chữ khi tay giữ đủ THOI_GIAN_GIU giây LIÊN TỤC
# và chữ đó phải KHÁC chữ vừa lưu trước đó (hoặc đã nghỉ đủ lâu)

THOI_GIAN_GIU    = 1.0   # (giây) Giữ nguyên tư thế bao lâu thì mới lưu
THOI_GIAN_NGHI   = 0.5   # (giây) Sau khi lưu 1 chữ, cần nghỉ bao lâu trước khi lưu chữ tiếp
NGUONG_TIN_CAY   = 0.6   # (0.0 → 1.0) Chỉ lưu khi AI chắc hơn 60%
                          # VD: AI đoán A=45%, B=30% → bỏ qua (chưa đủ chắc)
                          #     AI đoán A=85%, B=10% → lưu A

# --- Cấu hình HIỂN THỊ ---
CHIEU_RONG_MAN_HINH = 900  # pixel chiều ngang cửa sổ
CHIEU_CAO_MAN_HINH  = 600  # pixel chiều dọc cửa sổ
SO_CHU_TOI_DA       = 30   # Từ/câu tối đa bao nhiêu ký tự (tránh tràn màn hình)

# ============================================================
# PHẦN 2 — MÀU SẮC LANDMARK (giữ nguyên từ code gốc của bạn)
# ============================================================

COLOR_PALM   = (255, 255, 255)  # Trắng  - Lòng bàn tay
COLOR_THUMB  = (0,   0,   255)  # Đỏ     - Ngón cái
COLOR_INDEX  = (0,   255, 255)  # Vàng   - Ngón trỏ
COLOR_MIDDLE = (0,   255,   0)  # Lục    - Ngón giữa
COLOR_RING   = (255,   0,   0)  # Lam    - Ngón áp út
COLOR_PINKY  = (255,   0, 255)  # Tím    - Ngón út


def tao_style_landmark(mp_draw):
    """
    Hàm này tạo ra 2 từ điển (dictionary) chứa cấu hình màu sắc
    cho từng điểm khớp và đường nối trên bàn tay.

    mp_draw  : module mediapipe.solutions.drawing_utils được truyền vào
               để dùng DrawingSpec (lớp cấu hình nét vẽ)

    Trả về   : (style_diem, style_duong)
               style_diem  → dict[số_thứ_tự_landmark] = DrawingSpec
               style_duong → dict[(điểm_a, điểm_b)]   = DrawingSpec
    """
    style_diem = {}
    style_diem[0] = mp_draw.DrawingSpec(color=COLOR_PALM,   circle_radius=4)
    for i in range(1,  5): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_THUMB,  circle_radius=4)
    for i in range(5,  9): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_INDEX,  circle_radius=4)
    for i in range(9,  13): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, circle_radius=4)
    for i in range(13, 17): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_RING,   circle_radius=4)
    for i in range(17, 21): style_diem[i] = mp_draw.DrawingSpec(color=COLOR_PINKY,  circle_radius=4)

    style_duong = {}
    for conn in [(0,1),(0,5),(5,9),(9,13),(13,17),(0,17)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_PALM,   thickness=2)
    for conn in [(1,2),(2,3),(3,4)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_THUMB,  thickness=2)
    for conn in [(5,6),(6,7),(7,8)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_INDEX,  thickness=2)
    for conn in [(9,10),(10,11),(11,12)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_MIDDLE, thickness=2)
    for conn in [(13,14),(14,15),(15,16)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_RING,   thickness=2)
    for conn in [(17,18),(18,19),(19,20)]:
        style_duong[conn] = mp_draw.DrawingSpec(color=COLOR_PINKY,  thickness=2)

    return style_diem, style_duong


def trich_xuat_toa_do(hand_landmarks):
    """
    Từ object hand_landmarks của MediaPipe, hàm này trích xuất
    63 tọa độ đã chuẩn hóa (đã trừ đi gốc cổ tay).

    hand_landmarks : object chứa 21 điểm landmark, mỗi điểm có .x .y .z

    Chuẩn hóa 3D là gì?
        - Điểm 0 là cổ tay → dùng làm gốc tọa độ (0,0,0)
        - Mọi điểm khác đều trừ đi tọa độ cổ tay
        - Kết quả: tọa độ TƯƠNG ĐỐI so với cổ tay
        - Lợi ích: tay ở góc nào, xa gần bao nhiêu cũng cho ra số giống nhau
          VD: chữ A ở góc trái hay góc phải màn hình → model vẫn nhận đúng

    Trả về : list 63 số [x0,y0,z0, x1,y1,z1, ..., x20,y20,z20]
             hoặc [] nếu không đủ dữ liệu
    """
    goc_x = hand_landmarks.landmark[0].x   # Tọa độ x của cổ tay
    goc_y = hand_landmarks.landmark[0].y   # Tọa độ y của cổ tay
    goc_z = hand_landmarks.landmark[0].z   # Tọa độ z của cổ tay

    toa_do = []
    for diem in hand_landmarks.landmark:
        toa_do.extend([
            diem.x - goc_x,   # x tương đối
            diem.y - goc_y,   # y tương đối
            diem.z - goc_z    # z tương đối (độ sâu)
        ])
    return toa_do  # 21 điểm × 3 tọa độ = 63 số


def ve_giao_dien(frame, chu_hien_tai, do_tin_cay, tu_dang_ghep,
                 lich_su, trang_thai_debounce, thoi_gian_con_lai):
    """
    Vẽ toàn bộ giao diện HUD (heads-up display) lên frame camera.

    frame               : ảnh BGR từ OpenCV (sẽ bị vẽ đè lên)
    chu_hien_tai        : chữ AI vừa dự đoán, VD "A"
    do_tin_cay          : float 0.0→1.0, VD 0.87 = 87% chắc chắn
    tu_dang_ghep        : string câu đang gõ, VD "CHÀO"
    lich_su             : list các câu đã hoàn thành trước đó
    trang_thai_debounce : "cho"/"dang_giu"/"vua_luu" để vẽ màu khác nhau
    thoi_gian_con_lai   : float, còn bao nhiêu giây nữa thì lưu (cho thanh tiến trình)
    """
    chieu_cao, chieu_rong = frame.shape[:2]
    # frame.shape trả về (cao, rộng, kênh_màu)
    # [:2] lấy 2 giá trị đầu, bỏ kênh màu

    # --- VÙNG 1: Panel trên cùng (chữ đang nhận diện + độ tin cậy) ---
    cv2.rectangle(frame, (0, 0), (chieu_rong, 90), (15, 15, 25), cv2.FILLED)

    # Chọn màu chữ dựa trên trạng thái debounce
    if trang_thai_debounce == "vua_luu":
        mau_chu = (0, 255, 150)    # Xanh lá sáng → vừa lưu xong
    elif trang_thai_debounce == "dang_giu":
        mau_chu = (0, 200, 255)    # Vàng cam → đang giữ, sắp lưu
    else:
        mau_chu = (180, 180, 180)  # Xám → chờ

    cv2.putText(frame,
                f"KY HIEU: {chu_hien_tai}",
                (20, 55),                      # vị trí (x, y) pixel
                cv2.FONT_HERSHEY_DUPLEX,        # font chữ
                1.6,                            # cỡ chữ
                mau_chu,
                2)                             # độ dày nét

    # Hiển thị phần trăm độ tin cậy
    phan_tram = int(do_tin_cay * 100)
    cv2.putText(frame,
                f"{phan_tram}%",
                (chieu_rong - 100, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                mau_chu,
                2)

    # --- THANH TIẾN TRÌNH DEBOUNCE ---
    # Vẽ thanh ngang hiện thị còn bao lâu nữa thì lưu chữ
    # Khi tay giữ nguyên, thanh này dần đầy → khi đầy = lưu chữ
    y_thanh = 82
    chieu_dai_toi_da = chieu_rong - 40   # chiều dài tối đa của thanh

    # Tỉ lệ = thời gian đã giữ / thời gian cần giữ
    # thoi_gian_con_lai chạy từ THOI_GIAN_GIU xuống 0
    # → ti_le chạy từ 0 lên 1
    ti_le = 1.0 - (thoi_gian_con_lai / THOI_GIAN_GIU) if thoi_gian_con_lai < THOI_GIAN_GIU else 0.0
    ti_le = max(0.0, min(1.0, ti_le))   # giới hạn trong [0, 1]

    # Nền thanh (xám tối)
    cv2.rectangle(frame, (20, y_thanh), (20 + chieu_dai_toi_da, y_thanh + 6),
                  (50, 50, 60), cv2.FILLED)
    # Phần đã đầy (màu tùy trạng thái)
    if ti_le > 0:
        cv2.rectangle(frame,
                      (20, y_thanh),
                      (20 + int(chieu_dai_toi_da * ti_le), y_thanh + 6),
                      (0, 200, 255) if trang_thai_debounce == "dang_giu" else (0, 255, 150),
                      cv2.FILLED)

    # --- VÙNG 2: Panel giữa (từ đang ghép) ---
    cv2.rectangle(frame, (0, 95), (chieu_rong, 160), (20, 20, 35), cv2.FILLED)
    cv2.putText(frame,
                f"DANG GHEP: {tu_dang_ghep}_",   # dấu _ làm con trỏ nhấp nháy
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 100),   # vàng nhạt
                2)

    # --- VÙNG 3: Lịch sử các câu đã hoàn thành ---
    # Hiện tối đa 3 câu gần nhất (lấy từ cuối list)
    y_bat_dau_lich_su = chieu_cao - 130
    cv2.rectangle(frame, (0, y_bat_dau_lich_su - 10), (chieu_rong, chieu_cao), (10, 10, 20), cv2.FILLED)
    cv2.putText(frame, "LICH SU:", (20, y_bat_dau_lich_su + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 120), 1)

    # Lấy tối đa 3 câu cuối cùng trong lịch sử
    cac_cau_gan_nhat = lich_su[-3:] if len(lich_su) >= 3 else lich_su
    for i, cau in enumerate(reversed(cac_cau_gan_nhat)):
        # reversed() → hiện câu mới nhất ở trên
        do_mo_dan = 200 - i * 50   # câu mới = 200, câu cũ hơn = 150, 100
        cv2.putText(frame,
                    f"> {cau}",
                    (20, y_bat_dau_lich_su + 40 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (do_mo_dan, do_mo_dan, do_mo_dan),
                    1)

    # --- HƯỚNG DẪN PHÍM TẮT (góc dưới phải) ---
    huong_dan = "[SPACE] Them chu | [BACKSPACE] Xoa | [ENTER] Luu cau | [Q] Thoat"
    cv2.putText(frame, huong_dan,
                (10, chieu_cao - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (80, 80, 100),
                1)


# ============================================================
# PHẦN 3 — CLASS DEBOUNCE
# (Bộ lọc thông minh, tránh lưu chữ bị trùng lặp)
# ============================================================

class BoLocDebounce:
    """
    Class này giải quyết vấn đề: camera chạy 30 frame/giây,
    tay giữ nguyên 1 tư thế → sẽ dự đoán đúng tên chữ 30 lần/giây.
    Nếu lưu hết → "AAAAAAAAA..."

    Logic hoạt động:
    1. Mỗi frame gọi cap_nhat(chu_moi, do_tin_cay)
    2. Bộ lọc đếm thời gian giữ nguyên chữ đó
    3. Khi đủ THOI_GIAN_GIU → trả về True (cho phép lưu)
    4. Sau khi lưu → reset, phải nghỉ THOI_GIAN_NGHI trước khi lưu tiếp

    Biến nội bộ:
    chu_dang_giu     : chữ đang được giữ hiện tại
    thoi_diem_bat_dau: timestamp (giây) lúc bắt đầu giữ chữ này
    thoi_diem_vua_luu: timestamp lần cuối vừa lưu (để tính thời gian nghỉ)
    """

    def __init__(self):
        self.chu_dang_giu      = None   # Chữ đang được theo dõi
        self.thoi_diem_bat_dau = None   # Lúc nào bắt đầu giữ chữ này
        self.thoi_diem_vua_luu = 0.0    # Lúc nào lưu lần gần nhất (0 = chưa lưu lần nào)
        self.trang_thai        = "cho"  # "cho" / "dang_giu" / "vua_luu"

    def cap_nhat(self, chu_moi, do_tin_cay):
        """
        Gọi mỗi frame. Nhận chữ AI vừa đoán và độ tin cậy.

        chu_moi    : string, VD "A"
        do_tin_cay : float 0→1

        Trả về (cho_luu, thoi_gian_con_lai):
            cho_luu           : True nếu frame này được phép lưu chữ
            thoi_gian_con_lai : còn bao nhiêu giây nữa thì lưu (dùng vẽ thanh tiến trình)
        """
        hien_tai = time.time()   # Thời điểm hiện tại (giây, kiểu float)

        # Điều kiện 1: Độ tin cậy quá thấp → bỏ qua hoàn toàn
        if do_tin_cay < NGUONG_TIN_CAY:
            self.chu_dang_giu      = None
            self.thoi_diem_bat_dau = None
            self.trang_thai        = "cho"
            return False, THOI_GIAN_GIU

        # Điều kiện 2: Chữ mới KHÁC chữ đang theo dõi → reset bộ đếm
        if chu_moi != self.chu_dang_giu:
            self.chu_dang_giu      = chu_moi
            self.thoi_diem_bat_dau = hien_tai
            self.trang_thai        = "dang_giu"
            return False, THOI_GIAN_GIU

        # Tính thời gian đã giữ nguyên chữ này
        thoi_gian_da_giu = hien_tai - self.thoi_diem_bat_dau
        # Còn bao lâu nữa thì đủ
        thoi_gian_con_lai = max(0.0, THOI_GIAN_GIU - thoi_gian_da_giu)

        # Điều kiện 3: Chưa giữ đủ lâu → chờ thêm
        if thoi_gian_da_giu < THOI_GIAN_GIU:
            self.trang_thai = "dang_giu"
            return False, thoi_gian_con_lai

        # Điều kiện 4: Chưa nghỉ đủ sau lần lưu trước → chờ
        thoi_gian_da_nghi = hien_tai - self.thoi_diem_vua_luu
        if thoi_gian_da_nghi < THOI_GIAN_NGHI:
            self.trang_thai = "cho"
            return False, 0.0

        # ✅ Tất cả điều kiện OK → CHO PHÉP LƯU
        self.thoi_diem_vua_luu = hien_tai   # Ghi nhớ thời điểm lưu
        self.thoi_diem_bat_dau = hien_tai   # Reset để chữ tiếp theo cũng cần giữ đủ
        self.trang_thai = "vua_luu"
        return True, 0.0


# ============================================================
# PHẦN 4 — HÀM CHÍNH
# ============================================================

def chay_nhan_dien():
    """
    Hàm chính điều phối toàn bộ luồng xử lý:
    Camera → MediaPipe → Trích tọa độ → Model đoán → Debounce → Ghép chữ → Hiển thị
    """

    print("\n--- BƯỚC 3: NHẬN DIỆN + GHÉP CHỮ THÀNH TỪ ---")

    # --- Kiểm tra model ---
    if not os.path.exists(MODEL_FILE):
        print(f"[LỖI] Không tìm thấy '{MODEL_FILE}'. Hãy chạy BƯỚC 2 trước!")
        return

    with open(MODEL_FILE, 'rb') as f:
        model = pickle.load(f)
    print("-> Nạp model thành công! Đang bật camera...")

    # --- Khởi tạo MediaPipe ---
    mp_hands = mp.solutions.hands
    hands    = mp_hands.Hands(
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.8,
        min_tracking_confidence=0.8
    )
    mp_draw = mp.solutions.drawing_utils
    style_diem, style_duong = tao_style_landmark(mp_draw)

    # --- Khởi tạo camera ---
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CHIEU_RONG_MAN_HINH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CHIEU_CAO_MAN_HINH)

    # --- Khởi tạo các biến trạng thái ---

    tu_dang_ghep = ""
    # String đang được xây dựng từng chữ một
    # VD: sau khi ghép A, N, H → tu_dang_ghep = "ANH"

    lich_su_cau = []
    # List chứa các câu/từ đã hoàn chỉnh (nhấn ENTER để lưu vào đây)
    # VD: ["XIN CHAO", "CAM ON", "ANH YEU EM"]

    bo_loc = BoLocDebounce()
    # Khởi tạo bộ lọc debounce (xem giải thích ở class trên)

    chu_hien_tai  = "..."   # Chữ AI đang đoán (hiển thị trên màn hình)
    do_tin_cay    = 0.0     # Độ chắc chắn của dự đoán hiện tại
    thoi_gian_con = THOI_GIAN_GIU  # Dùng để vẽ thanh tiến trình

    print("-> Sẵn sàng! Hướng dẫn:")
    print("   SPACE     : Thêm chữ vào từ thủ công (nếu không muốn dùng auto)")
    print("   BACKSPACE : Xóa ký tự cuối")
    print("   ENTER     : Lưu từ vào lịch sử, bắt đầu từ mới")
    print("   C         : Xóa toàn bộ từ đang ghép")
    print("   Q         : Thoát")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame     = cv2.flip(frame, 1)
        # cv2.flip(..., 1) → lật ngang (như gương)
        # Không có dòng này: giơ tay phải thì trên màn hình thấy tay trái

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # MediaPipe cần ảnh RGB, OpenCV mặc định là BGR
        # BGR = Blue Green Red (thứ tự kênh màu ngược với RGB)

        result    = hands.process(rgb_frame)
        # result.multi_hand_landmarks : list các bàn tay phát hiện được
        # None nếu không thấy tay nào

        # Reset dự đoán mỗi frame (nếu không thấy tay → hiện "...")
        chu_hien_tai = "..."
        do_tin_cay   = 0.0

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:

                # Vẽ skeleton bàn tay
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=style_diem,
                    connection_drawing_spec=style_duong
                )

                # Trích xuất 63 tọa độ đã chuẩn hóa
                toa_do = trich_xuat_toa_do(hand_landmarks)

                if len(toa_do) == 63:
                    # predict_proba → trả về xác suất cho TẤT CẢ nhãn
                    # VD: [0.01, 0.87, 0.05, ...] → A=1%, B=87%, C=5%,...
                    xac_suat_tat_ca = model.predict_proba([toa_do])[0]
                    # [0] vì chỉ có 1 mẫu, lấy hàng đầu tiên

                    # argmax() → tìm vị trí có xác suất cao nhất
                    vi_tri_cao_nhat = xac_suat_tat_ca.argmax()

                    # Lấy tên nhãn tương ứng vị trí đó
                    chu_hien_tai = model.classes_[vi_tri_cao_nhat]
                    # model.classes_ = ['A','B','C',...,'Z'] (đã train)

                    do_tin_cay   = xac_suat_tat_ca[vi_tri_cao_nhat]
                    # Độ tin cậy = xác suất cao nhất

                    # --- GỌI BỘ LỌC DEBOUNCE ---
                    cho_luu, thoi_gian_con = bo_loc.cap_nhat(chu_hien_tai, do_tin_cay)

                    if cho_luu:
                        # Bộ lọc cho phép → ghép chữ vào từ
                        if len(tu_dang_ghep) < SO_CHU_TOI_DA:
                            tu_dang_ghep += chu_hien_tai
                            print(f"  + Ghep: '{chu_hien_tai}'  →  Tu: '{tu_dang_ghep}'")

        # --- Vẽ giao diện HUD ---
        ve_giao_dien(
            frame,
            chu_hien_tai,
            do_tin_cay,
            tu_dang_ghep,
            lich_su_cau,
            bo_loc.trang_thai,
            thoi_gian_con
        )

        cv2.imshow('Nhan Dien Ky Hieu', frame)

        # --- XỬ LÝ PHÍM BẤM ---
        phim = cv2.waitKey(1) & 0xFF
        # waitKey(1) : chờ 1ms → đủ để video chạy mượt 30fps
        # & 0xFF     : lấy 8 bit cuối (tránh lỗi trên một số hệ điều hành)

        if phim == ord('q') or phim == 27:
            # Q hoặc ESC → thoát
            break

        elif phim == 32:
            # SPACE → thêm thủ công chữ đang thấy (bỏ qua debounce)
            if chu_hien_tai != "..." and len(tu_dang_ghep) < SO_CHU_TOI_DA:
                tu_dang_ghep += chu_hien_tai
                print(f"  [THU CONG] Ghep: '{chu_hien_tai}'  →  Tu: '{tu_dang_ghep}'")

        elif phim == 8:
            # BACKSPACE (mã ASCII 8) → xóa ký tự cuối
            if len(tu_dang_ghep) > 0:
                chu_xoa     = tu_dang_ghep[-1]   # ký tự cuối
                tu_dang_ghep = tu_dang_ghep[:-1]  # chuỗi trừ ký tự cuối
                print(f"  [XOA] Bo '{chu_xoa}'  →  Tu: '{tu_dang_ghep}'")

        elif phim == 13:
            # ENTER (mã ASCII 13) → lưu câu vào lịch sử
            if tu_dang_ghep.strip():
                lich_su_cau.append(tu_dang_ghep)
                print(f"  [ENTER] Luu cau: '{tu_dang_ghep}'")
                tu_dang_ghep = ""   # Xóa từ, bắt đầu từ mới

        elif phim == ord('c'):
            # C → xóa sạch từ đang ghép
            print(f"  [XOA HET] Xoa tu: '{tu_dang_ghep}'")
            tu_dang_ghep = ""

    # --- Dọn dẹp ---
    cap.release()
    cv2.destroyAllWindows()

    # In tóm tắt lịch sử khi thoát
    if lich_su_cau:
        print("\n=== LỊCH SỬ CÁC CÂU ĐÃ GHI ===")
        for i, cau in enumerate(lich_su_cau, 1):
            print(f"  {i}. {cau}")


if __name__ == "__main__":
    chay_nhan_dien()