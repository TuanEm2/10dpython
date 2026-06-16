import os
import time
import pickle
import cv2
import mediapipe as mp
import customtkinter as ctk
from PIL import Image, ImageTk


class UngDungNhanDien(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. CÀI ĐẶT CỬA SỔ & GIAO DIỆN ---
        self.title("SIGNLENS - Hệ Thống Ký Hiệu & Phiên Dịch")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.cap = None

        # Biến lưu bài học hiện tại để so sánh kết quả
        self.bai_dang_hoc = None

        self.dinh_dang_giao_dien()
        self.tao_du_lieu_bai_hoc()

        # --- 2. TẢI MÔ HÌNH AI ---
        self.model = None
        if os.path.exists('model_tinh.pkl'):
            with open('model_tinh.pkl', 'rb') as f:
                self.model = pickle.load(f)

        # --- 3. CÀI ĐẶT MEDIAPIPE ---
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils
        self.tao_mau_khung_xuong()

        # --- 4. BỘ LỌC CHỐNG NHIỄU ---
        self.chu_dang_giu = None
        self.thoi_diem_bat_dau = None
        self.thoi_diem_vua_luu = 0.0
        self.thoi_gian_giu = 1.0
        self.thoi_gian_nghi = 0.5
        self.nguong_tin_cay = 0.6

        # --- 5. BỐ CỤC CHÍNH CỦA APP ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sử dụng Tabview nhưng bo góc và màu sắc hiện đại hơn
        self.tab_chinh = ctk.CTkTabview(self,
                                        fg_color=self.mau_nen_tab,
                                        segmented_button_selected_color=self.mau_chu_dao,
                                        segmented_button_selected_hover_color=self.mau_hover,
                                        segmented_button_unselected_hover_color="#3A3B3C",
                                        corner_radius=15)
        self.tab_chinh.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.tab_chinh.add("📚 HỌC TẬP")
        self.tab_chinh.add("🔄 PHIÊN DỊCH")

        self.ve_tab_hoc_tap()
        self.ve_tab_phien_dich()

    def dinh_dang_giao_dien(self):
        """Hệ thống màu sắc Modern Dark Theme"""
        ctk.set_appearance_mode("dark")
        self.mau_nen_chinh = "#18191A"  # Nền ngoài cùng
        self.mau_nen_tab = "#242526"  # Nền trong tab
        self.mau_card = "#3A3B3C"  # Nền các khung bo góc (Card)
        self.mau_chu_dao = "#E50914"  # Đỏ Netflix (Tạo điểm nhấn mạnh mẽ)
        self.mau_hover = "#B80710"  # Đỏ đậm khi hover
        self.mau_thanh_cong = "#00C851"  # Xanh lá cho thông báo đúng

        self.configure(fg_color=self.mau_nen_chinh)

        self.font_tieu_de_lon = ("Segoe UI", 28, "bold")
        self.font_tieu_de = ("Segoe UI", 20, "bold")
        self.font_chu = ("Segoe UI", 15)
        self.font_chu_dam = ("Segoe UI", 15, "bold")

    def tao_mau_khung_xuong(self):
        self.style_diem = {i: self.mp_draw.DrawingSpec(color=(0, 215, 255), circle_radius=4) for i in range(21)}
        self.style_diem[0] = self.mp_draw.DrawingSpec(color=(255, 255, 255), circle_radius=5)
        self.style_duong = self.mp_draw.DrawingSpec(color=(200, 200, 200), thickness=2)

    def tao_du_lieu_bai_hoc(self):
        self.du_lieu_hoc = {
            "SỐ ĐẾM": [
                {"ten": "Số 0", "nhan_ai": "0", "hd": "Các ngón tay chạm vào ngón cái tạo thành hình chữ O."},
                {"ten": "Số 1", "nhan_ai": "1", "hd": "Nắm các ngón tay lại, chỉ duỗi thẳng ngón trỏ hướng lên trên."},
                {"ten": "Số 2", "nhan_ai": "2", "hd": "Duỗi thẳng ngón trỏ và ngón giữa tạo thành chữ V."}
            ],
            "CHỮ CÁI": [
                {"ten": "Chữ A", "nhan_ai": "A", "hd": "Khép chặt 4 ngón tay, ngón cái ép sát vào má ngoài ngón trỏ."},
                {"ten": "Chữ B", "nhan_ai": "B", "hd": "Duỗi thẳng 4 ngón tay, ngón cái gập vào lòng bàn tay."},
                {"ten": "Chữ C", "nhan_ai": "C", "hd": "Uốn cong các ngón tay và ngón cái tạo thành hình chữ C."}
            ]
        }

    # =======================================================
    # TAB 1: HỌC TẬP (THIẾT KẾ CARD HIỆN ĐẠI)
    # =======================================================
    def ve_tab_hoc_tap(self):
        tab = self.tab_chinh.tab("📚 HỌC TẬP")
        tab.grid_columnconfigure(0, weight=6)  # Khung Camera (60%)
        tab.grid_columnconfigure(1, weight=4)  # Khung Bài học (40%)
        tab.grid_rowconfigure(0, weight=1)

        # --- TRÁI: CAMERA (Card bo góc) ---
        khung_trai = ctk.CTkFrame(tab, fg_color=self.mau_card, corner_radius=15)
        khung_trai.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        khung_trai.grid_rowconfigure(1, weight=1)
        khung_trai.grid_columnconfigure(0, weight=1)

        # Header điều khiển Camera
        khung_dieu_khien = ctk.CTkFrame(khung_trai, fg_color="transparent")
        khung_dieu_khien.grid(row=0, column=0, sticky="ew", pady=(15, 5), padx=20)

        ctk.CTkButton(khung_dieu_khien, text="▶ BẬT CAM", font=self.font_chu_dam,
                      fg_color=self.mau_chu_dao, hover_color=self.mau_hover,
                      command=self.bat_camera, width=100, corner_radius=8).pack(side="left", padx=5)
        ctk.CTkButton(khung_dieu_khien, text="⏹ TẮT", font=self.font_chu_dam,
                      fg_color="#555555", hover_color="#333333",
                      command=self.tat_camera, width=80, corner_radius=8).pack(side="left", padx=5)

        self.lbl_ket_qua_hoc = ctk.CTkLabel(khung_dieu_khien, text="Bật camera để bắt đầu",
                                            font=("Segoe UI", 16, "bold"), text_color="#FFBB33")
        self.lbl_ket_qua_hoc.pack(side="right", padx=10)

        # Vùng hiển thị Camera (Màu đen giả lập màn hình)
        khung_man_hinh = ctk.CTkFrame(khung_trai, fg_color="#000000", corner_radius=10)
        khung_man_hinh.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        khung_man_hinh.grid_rowconfigure(0, weight=1)
        khung_man_hinh.grid_columnconfigure(0, weight=1)

        self.lbl_camera_hoc = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH CAMERA ]", text_color="#555555")
        self.lbl_camera_hoc.grid(row=0, column=0)

        # --- PHẢI: BÀI HỌC (Card bo góc) ---
        khung_phai = ctk.CTkFrame(tab, fg_color=self.mau_card, corner_radius=15)
        khung_phai.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Danh mục bài học
        ctk.CTkLabel(khung_phai, text="CHỌN GIÁO TRÌNH", font=self.font_tieu_de).pack(pady=(20, 10))

        khung_danh_muc = ctk.CTkFrame(khung_phai, fg_color="transparent")
        khung_danh_muc.pack(fill="x", padx=20)

        for danh_muc in self.du_lieu_hoc.keys():
            ctk.CTkButton(khung_danh_muc, text=danh_muc, font=self.font_chu_dam,
                          fg_color="#4A4B4C", hover_color=self.mau_chu_dao, corner_radius=8,
                          command=lambda dm=danh_muc: self.tai_danh_sach_bai_hoc(dm)).pack(side="left", fill="x",
                                                                                           expand=True, padx=5)

        # Vùng hiển thị chi tiết bài
        self.khung_chi_tiet = ctk.CTkFrame(khung_phai, fg_color=self.mau_nen_tab, corner_radius=10)
        self.khung_chi_tiet.pack(fill="both", expand=True, padx=20, pady=20)

        self.lbl_tieu_de_bai = ctk.CTkLabel(self.khung_chi_tiet, text="Chưa chọn bài học", font=self.font_tieu_de_lon)
        self.lbl_tieu_de_bai.pack(pady=(20, 10))

        self.khung_ds_con = ctk.CTkScrollableFrame(self.khung_chi_tiet, height=60, orientation="horizontal",
                                                   fg_color="transparent")
        self.khung_ds_con.pack(fill="x", padx=10)

        # Card mô tả
        khung_mo_ta = ctk.CTkFrame(self.khung_chi_tiet, fg_color=self.mau_card, corner_radius=8)
        khung_mo_ta.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self.lbl_hd_chi_tiet = ctk.CTkLabel(khung_mo_ta, text="Chọn một bài học ở trên để xem hướng dẫn chi tiết.",
                                            font=self.font_chu, wraplength=280, justify="center")
        self.lbl_hd_chi_tiet.pack(expand=True, pady=20, padx=20)

    def tai_danh_sach_bai_hoc(self, danh_muc):
        for widget in self.khung_ds_con.winfo_children(): widget.destroy()

        for bai in self.du_lieu_hoc[danh_muc]:
            btn = ctk.CTkButton(self.khung_ds_con, text=bai["ten"], font=self.font_chu,
                                fg_color="#555555", hover_color=self.mau_chu_dao, corner_radius=20,
                                command=lambda b=bai: self.hien_thi_chi_tiet_bai(b))
            btn.pack(side="left", padx=5)

        if self.du_lieu_hoc[danh_muc]:
            self.hien_thi_chi_tiet_bai(self.du_lieu_hoc[danh_muc][0])

    def hien_thi_chi_tiet_bai(self, bai_hoc):
        self.bai_dang_hoc = bai_hoc
        self.lbl_tieu_de_bai.configure(text=f"👉 {bai_hoc['ten']}")
        self.lbl_hd_chi_tiet.configure(text=f"{bai_hoc['hd']}")
        self.lbl_ket_qua_hoc.configure(text=f"Hãy làm thử chữ: {bai_hoc['nhan_ai']}", text_color="#00C851")

    # =======================================================
    # TAB 2: PHIÊN DỊCH
    # =======================================================
    def ve_tab_phien_dich(self):
        tab = self.tab_chinh.tab("🔄 PHIÊN DỊCH")
        tab.grid_columnconfigure(0, weight=6)
        tab.grid_columnconfigure(1, weight=4)
        tab.grid_rowconfigure(0, weight=1)

        # --- TRÁI: CAMERA & KẾT QUẢ ---
        khung_trai = ctk.CTkFrame(tab, fg_color=self.mau_card, corner_radius=15)
        khung_trai.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        khung_trai.grid_rowconfigure(0, weight=1)
        khung_trai.grid_columnconfigure(0, weight=1)

        # Màn hình Cam
        khung_man_hinh = ctk.CTkFrame(khung_trai, fg_color="#000000", corner_radius=10)
        khung_man_hinh.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        khung_man_hinh.grid_rowconfigure(0, weight=1)
        khung_man_hinh.grid_columnconfigure(0, weight=1)

        self.lbl_camera_dich = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH CAMERA ]", text_color="#555555")
        self.lbl_camera_dich.grid(row=0, column=0)

        # Thanh Kết quả Realtime
        khung_ket_qua = ctk.CTkFrame(khung_trai, fg_color=self.mau_nen_tab, corner_radius=10)
        khung_ket_qua.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.lbl_chu_hien_tai = ctk.CTkLabel(khung_ket_qua, text="AI: ...", font=("Segoe UI", 35, "bold"))
        self.lbl_chu_hien_tai.pack(side="left", padx=30, pady=15)

        khung_tien_trinh = ctk.CTkFrame(khung_ket_qua, fg_color="transparent")
        khung_tien_trinh.pack(side="right", padx=30)
        ctk.CTkLabel(khung_tien_trinh, text="Độ tin cậy", font=("Segoe UI", 12)).pack(anchor="w")
        self.thanh_tin_cay = ctk.CTkProgressBar(khung_tien_trinh, progress_color=self.mau_thanh_cong, width=150)
        self.thanh_tin_cay.pack()
        self.thanh_tin_cay.set(0.0)

        # --- PHẢI: BẢNG DỊCH VĂN BẢN ---
        khung_phai = ctk.CTkFrame(tab, fg_color=self.mau_card, corner_radius=15)
        khung_phai.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        khung_nut = ctk.CTkFrame(khung_phai, fg_color="transparent")
        khung_nut.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkButton(khung_nut, text="▶ BẬT CAMERA DỊCH", font=self.font_chu_dam, fg_color=self.mau_chu_dao,
                      hover_color=self.mau_hover, command=self.bat_camera).pack(side="left", fill="x", expand=True,
                                                                                padx=(0, 5))
        ctk.CTkButton(khung_nut, text="⏹ TẮT", font=self.font_chu_dam, fg_color="#555555", hover_color="#333333",
                      command=self.tat_camera).pack(side="right", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(khung_phai, text="ĐOẠN VĂN BẢN ĐÃ DỊCH", font=self.font_tieu_de).pack(pady=(10, 5), anchor="w",
                                                                                           padx=25)
        self.hop_cau_chu = ctk.CTkTextbox(khung_phai, height=100, font=self.font_chu_dam, corner_radius=10,
                                          fg_color=self.mau_nen_tab)
        self.hop_cau_chu.pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(khung_phai, text="Lưu đoạn văn (Xuống dòng)", font=self.font_chu_dam, fg_color="#4A4B4C",
                      hover_color="#555555", corner_radius=8, command=self.luu_cau_vao_lich_su).pack(pady=10, padx=20,
                                                                                                     fill="x")

        ctk.CTkLabel(khung_phai, text="LỊCH SỬ DỊCH", font=self.font_chu_dam, text_color="#888888").pack(anchor="w",
                                                                                                         padx=25)
        self.hop_lich_su = ctk.CTkTextbox(khung_phai, font=self.font_chu, corner_radius=10, fg_color=self.mau_nen_tab)
        self.hop_lich_su.pack(pady=5, padx=20, fill="both", expand=True)

    # =======================================================
    # XỬ LÝ LOGIC CAMERA VÀ NHẬN DIỆN (GIỮ NGUYÊN)
    # =======================================================
    def lay_toa_do_chuan_hoa(self, hand_landmarks):
        goc_x, goc_y, goc_z = hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y, hand_landmarks.landmark[0].z
        toa_do = []
        for diem in hand_landmarks.landmark:
            toa_do.extend([diem.x - goc_x, diem.y - goc_y, diem.z - goc_z])
        return toa_do

    def kiem_tra_cho_luu(self, chu_moi, do_tin_cay):
        hien_tai = time.time()
        if do_tin_cay < self.nguong_tin_cay: return False
        if chu_moi != self.chu_dang_giu:
            self.chu_dang_giu = chu_moi
            self.thoi_diem_bat_dau = hien_tai
            return False
        if (hien_tai - self.thoi_diem_bat_dau >= self.thoi_gian_giu) and (
                hien_tai - self.thoi_diem_vua_luu >= self.thoi_gian_nghi):
            self.thoi_diem_vua_luu = self.thoi_diem_bat_dau = hien_tai
            return True
        return False

    def luu_cau_vao_lich_su(self):
        cau_hien_tai = self.hop_cau_chu.get("1.0", "end").strip()
        if cau_hien_tai:
            self.hop_lich_su.insert("end", f"- {cau_hien_tai}\n")
            self.hop_cau_chu.delete("1.0", "end")

    def bat_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Có thể đổi thành 1, 2 nếu dùng ivCam
        self.cap_nhat_khung_hinh()

    def tat_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.lbl_camera_hoc.configure(image=None, text="[ MÀN HÌNH CAMERA ĐÃ TẮT ]")
            self.lbl_camera_dich.configure(image=None, text="[ MÀN HÌNH CAMERA ĐÃ TẮT ]")
            self.lbl_chu_hien_tai.configure(text="AI: ...", text_color="white")
            self.thanh_tin_cay.set(0)

    def cap_nhat_khung_hinh(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                ket_qua = self.hands.process(rgb_frame)
                chu_du_doan = "..."
                do_tin_cay_max = 0.0

                if ket_qua.multi_hand_landmarks and self.model is not None:
                    for hand_landmarks in ket_qua.multi_hand_landmarks:
                        self.mp_draw.draw_landmarks(rgb_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                                                    self.style_diem[0], self.style_duong)
                        toa_do = self.lay_toa_do_chuan_hoa(hand_landmarks)

                        if len(toa_do) == 63:
                            xac_suat = self.model.predict_proba([toa_do])[0]
                            vi_tri = xac_suat.argmax()
                            chu_du_doan, do_tin_cay_max = self.model.classes_[vi_tri], xac_suat[vi_tri]

                            if self.tab_chinh.get() == "🔄 PHIÊN DỊCH" and self.kiem_tra_cho_luu(chu_du_doan,
                                                                                                do_tin_cay_max):
                                self.hop_cau_chu.insert("end", chu_du_doan + " ")

                tab_hien_tai = self.tab_chinh.get()
                img = Image.fromarray(rgb_frame)

                if tab_hien_tai == "📚 HỌC TẬP":
                    chieu_rong, chieu_cao = self.lbl_camera_hoc.winfo_width(), self.lbl_camera_hoc.winfo_height()
                    if chieu_rong > 10 and chieu_cao > 10:
                        self.lbl_camera_hoc.configure(
                            image=ctk.CTkImage(light_image=img, dark_image=img, size=(chieu_rong, chieu_cao)), text="")

                    if self.bai_dang_hoc and do_tin_cay_max >= self.nguong_tin_cay:
                        if chu_du_doan == self.bai_dang_hoc["nhan_ai"]:
                            self.lbl_ket_qua_hoc.configure(text="✅ CHÍNH XÁC! Tốt lắm!", text_color=self.mau_thanh_cong)
                        else:
                            self.lbl_ket_qua_hoc.configure(text=f"❌ Sai rồi. Đang nhận diện là: {chu_du_doan}",
                                                           text_color=self.mau_chu_dao)
                    else:
                        self.lbl_ket_qua_hoc.configure(text="Đang chờ bạn thực hành...", text_color="#FFBB33")

                elif tab_hien_tai == "🔄 PHIÊN DỊCH":
                    chieu_rong, chieu_cao = self.lbl_camera_dich.winfo_width(), self.lbl_camera_dich.winfo_height()
                    if chieu_rong > 10 and chieu_cao > 10:
                        self.lbl_camera_dich.configure(
                            image=ctk.CTkImage(light_image=img, dark_image=img, size=(chieu_rong, chieu_cao)), text="")

                    mau_hien_tai = self.mau_thanh_cong if do_tin_cay_max >= self.nguong_tin_cay else "white"
                    self.lbl_chu_hien_tai.configure(text=f"AI: {chu_du_doan}", text_color=mau_hien_tai)
                    self.thanh_tin_cay.set(float(do_tin_cay_max))

            self.after(15, self.cap_nhat_khung_hinh)