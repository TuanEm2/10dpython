import os
import time
import cv2
import pickle
import threading
import random
import mediapipe as mp
import customtkinter as ctk
from PIL import Image

# --- IMPORT TẦNG LOGIC (BUS) ---
try:
    from XuLyLogic.logic_bai_hoc import QuanLyBaiHoc
    from XuLyLogic.logic_thuc_hanh_tu_do import QuanLyThucHanhTuDo
    from XuLyLogic.logic_ho_so import QuanLyHoSo
    from XuLyLogic.logic_tro_choi import QuanLyTroChoi
    from XuLyLogic.engine_nhan_dien_v2 import BoXuLyNhanDienKetHop

except ImportError as e:
    print(f"Lưu ý: Chưa tải được module logic. Chi tiết: {e}")

class UngDungNhanDien(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. CÀI ĐẶT CỬA SỔ & THEME ---
        self.title("SIGNLENS - Hệ Thống Ký Hiệu & Phiên Dịch")
        self.geometry("1300x800")
        self.minsize(1100, 700)
        self.dinh_dang_giao_dien()

        # Quản lý Camera, Đa luồng & Trạng thái
        self.camera_running = False
        self.camera_thread = None
        self.latest_frame = None
        self.latest_prediction = ("...", 0.0, "...")
        self.dang_kiem_tra = False

        # --- Biến cho tính năng TỰ ĐỘNG THÊM CHỮ & SPACE ---
        self.chu_cho_them = ""
        self.thoi_diem_mat_tay = 0
        self.delay_tu_dong_them = 1.0  # Thời gian chờ (giây) sau khi rút tay để tự động ghép chữ

        # Khởi tạo AI Engine V2
        try:
            self.engine = BoXuLyNhanDienKetHop()
        except NameError:
            self.engine = None
            print("Chưa tải được Engine Nhận Diện")

        # Khởi tạo Logic
        try:
            self.logic_hoc = QuanLyBaiHoc()
            self.logic_thuc_hanh = QuanLyThucHanhTuDo()
            self.logic_ho_so = QuanLyHoSo()
            self.logic_game = QuanLyTroChoi()
        except NameError:
            self.logic_hoc = None
            self.logic_thuc_hanh = None
            self.logic_ho_so = None
            self.logic_game = None

        # --- 2. BỐ CỤC KHUNG CHÍNH ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.ve_menu_sidebar()

        self.khung_chinh = ctk.CTkFrame(self, fg_color="transparent")
        self.khung_chinh.grid(row=0, column=1, sticky="nsew", padx=(20, 20), pady=20)
        self.khung_chinh.grid_rowconfigure(0, weight=1)
        self.khung_chinh.grid_columnconfigure(0, weight=1)

        # Khởi tạo các trang
        self.trang_hoc_tap = self.tao_trang_hoc_tap()
        self.trang_thuc_hanh = self.tao_trang_thuc_hanh()
        self.trang_tro_choi = self.tao_trang_tro_choi()
        self.trang_ho_so = self.tao_trang_ho_so()

        self.trang_hien_tai = "Học Tập"
        self.hien_thi_trang("Học Tập")

    def dinh_dang_giao_dien(self):
        ctk.set_appearance_mode("dark")
        self.mau_nen = "#121212"
        self.mau_sidebar = "#1E1E1E"
        self.mau_card = "#2C2C2C"
        self.mau_chu_dao = "#E50914"
        self.mau_hover = "#B80710"
        self.mau_thanh_cong = "#00E676"
        self.configure(fg_color=self.mau_nen)

        self.font_logo = ("Segoe UI Black", 28, "bold")
        self.font_menu = ("Segoe UI", 16, "bold")
        self.font_tieu_de_lon = ("Segoe UI", 28, "bold")
        self.font_tieu_de = ("Segoe UI", 22, "bold")
        self.font_chu = ("Segoe UI", 15)
        self.font_chu_dam = ("Segoe UI", 15, "bold")

    def ve_menu_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=self.mau_sidebar)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self.sidebar, text="SIGNLENS", font=self.font_logo, text_color=self.mau_chu_dao).grid(row=0, column=0, padx=20, pady=(30, 30))

        self.nut_menu = {}
        danh_sach_menu = ["Học Tập", "Thực Hành Tự Do", "Minigame", "Hồ Sơ & Xếp Hạng"]

        for i, ten_menu in enumerate(danh_sach_menu):
            btn = ctk.CTkButton(self.sidebar, text=ten_menu, font=self.font_menu, fg_color="transparent",
                                text_color="#A0A0A0", hover_color=self.mau_card, anchor="w",
                                command=lambda m=ten_menu: self.hien_thi_trang(m))
            btn.grid(row=i + 1, column=0, padx=20, pady=10, sticky="ew")
            self.nut_menu[ten_menu] = btn

    def hien_thi_trang(self, ten_trang):
        # Tắt camera nếu đang chạy khi chuyển trang
        if self.camera_running:
            self.tat_camera()

        self.trang_hien_tai = ten_trang
        for ten, nut in self.nut_menu.items():
            if ten == ten_trang:
                nut.configure(fg_color=self.mau_card, text_color="white")
            else:
                nut.configure(fg_color="transparent", text_color="#A0A0A0")

        for widget in self.khung_chinh.winfo_children():
            widget.grid_forget()

        if ten_trang == "Học Tập":
            self.trang_hoc_tap.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Thực Hành Tự Do":
            self.trang_thuc_hanh.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Minigame":
            self.trang_tro_choi.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Hồ Sơ & Xếp Hạng":
            self.ve_lai_giao_dien_ho_so()  # Refresh data trước khi show
            self.trang_ho_so.grid(row=0, column=0, sticky="nsew")

    # =======================================================
    # TRANG HỌC TẬP
    # =======================================================
    def tao_trang_hoc_tap(self):
        self.bai_da_hoc = set()
        self.bai_hien_tai = None
        self.nut_bai_hoc_dict = {}

        trang = ctk.CTkFrame(self.khung_chinh, fg_color="transparent")
        trang.grid_columnconfigure(0, weight=7)
        trang.grid_columnconfigure(1, weight=3)
        trang.grid_rowconfigure(0, weight=1)

        khung_trai = ctk.CTkFrame(trang, fg_color="transparent")
        khung_trai.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        khung_trai.grid_columnconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(1, weight=0)

        khung_cam = ctk.CTkFrame(khung_trai, fg_color=self.mau_card, corner_radius=15)
        khung_cam.grid(row=0, column=0, sticky="nsew", pady=(0, 15))

        khung_dieu_khien = ctk.CTkFrame(khung_cam, fg_color="transparent")
        khung_dieu_khien.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(khung_dieu_khien, text="▶ BẬT CAM", font=self.font_chu_dam, fg_color=self.mau_chu_dao, hover_color=self.mau_hover, command=self.bat_camera, width=100).pack(side="left", padx=5)
        ctk.CTkButton(khung_dieu_khien, text="⏹ TẮT", font=self.font_chu_dam, fg_color="#555555", hover_color="#333333", command=self.tat_camera, width=80).pack(side="left", padx=5)

        self.lbl_ket_qua_hoc = ctk.CTkLabel(khung_dieu_khien, text="Chưa bật camera", font=("Segoe UI", 16, "bold"), text_color="#FFCC00")
        self.lbl_ket_qua_hoc.pack(side="right", padx=10)

        khung_man_hinh = ctk.CTkFrame(khung_cam, fg_color="#000000", width=640, height=480)
        khung_man_hinh.pack(pady=10, expand=True)
        khung_man_hinh.grid_propagate(False)
        self.lbl_camera_main = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH ]", text_color="#555555")
        self.lbl_camera_main.place(relx=0.5, rely=0.5, anchor="center")

        self.khung_duoi = ctk.CTkFrame(khung_trai, fg_color=self.mau_card, corner_radius=15)
        self.khung_duoi.grid(row=1, column=0, sticky="nsew")

        self.lbl_tieu_de_huong_dan = ctk.CTkLabel(self.khung_duoi, text="📝 Hướng dẫn thực hiện:",
                                                  font=self.font_tieu_de)
        self.lbl_tieu_de_huong_dan.pack(anchor="w", padx=20, pady=(15, 5))
        self.lbl_mo_ta = ctk.CTkLabel(self.khung_duoi, text="(Vui lòng chọn bài học ở danh sách bên phải)",
                                      font=self.font_chu, text_color="#A0A0A0", wraplength=500, justify="left")
        self.lbl_mo_ta.pack(anchor="w", padx=20, pady=5)

        self.khung_nut_duoi = ctk.CTkFrame(self.khung_duoi, fg_color="transparent")
        self.khung_nut_duoi.pack(fill="x", side="bottom", pady=15, padx=20)

        self.btn_quiz = ctk.CTkButton(self.khung_nut_duoi, text="🎯 Kiểm tra tiến độ", fg_color="#8e44ad",
                                      hover_color="#9b59b6", font=self.font_chu_dam, command=self.mo_kiem_tra)
        self.btn_quiz.pack(side="right", padx=10)

        khung_phai = ctk.CTkFrame(trang, fg_color=self.mau_card, corner_radius=15)
        khung_phai.grid(row=0, column=1, sticky="nsew")

        khung_anh_mau = ctk.CTkFrame(khung_phai, fg_color=self.mau_sidebar, corner_radius=10)
        khung_anh_mau.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(khung_anh_mau, text="🖼 ẢNH MẪU", font=self.font_tieu_de).pack(pady=(15, 5))
        self.lbl_anh_mau = ctk.CTkLabel(khung_anh_mau, text="[Chưa có ảnh]", width=150, height=150, fg_color="#1E1E1E", corner_radius=10)
        self.lbl_anh_mau.pack(pady=10)

        self.lbl_tieu_de_bai_phai = ctk.CTkLabel(khung_anh_mau, text="Chưa chọn bài", font=self.font_chu_dam)
        self.lbl_tieu_de_bai_phai.pack(pady=(5, 15))

        self.khung_ds_con = ctk.CTkScrollableFrame(khung_phai, fg_color="transparent")
        self.khung_ds_con.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        if hasattr(self, 'logic_ho_so') and self.logic_ho_so:
            self.bai_da_hoc = set(self.logic_ho_so.lay_danh_sach_da_hoc())
        else:
            self.bai_da_hoc = set()

        if self.logic_hoc and self.logic_hoc.danh_sach_bai_hoc:
            for bai in self.logic_hoc.danh_sach_bai_hoc:
                # Kiểm tra xem bài này có trong danh sách DB đã lấy lên không
                is_done = bai in self.bai_da_hoc
                btn_color = "#00E676" if is_done else "#3A3B3C"
                text_color = "#000000" if is_done else "white"
                text_hien_thi = f"✅ {bai}" if is_done else bai

                btn = ctk.CTkButton(self.khung_ds_con, text=text_hien_thi, font=self.font_chu, fg_color=btn_color,
                                    text_color=text_color, hover_color=self.mau_chu_dao,
                                    command=lambda b=bai: self.chon_bai_hoc_logic(b))
                btn.pack(pady=5, fill="x")
                self.nut_bai_hoc_dict[bai] = btn
        else:
            ctk.CTkLabel(self.khung_ds_con, text="(Trống)", text_color="#888").pack(pady=20)

        return trang

    def cap_nhat_ui_danh_sach_bai_hoc(self):
        """Cập nhật lại màu sắc của danh sách bài học dựa trên DB hiện tại"""
        if not hasattr(self, 'logic_ho_so') or not self.logic_ho_so:
            return

        # 1. Lấy danh sách bài đã học của user hiện tại từ Database
        self.bai_da_hoc = set(self.logic_ho_so.lay_danh_sach_da_hoc())

        # 2. Quét qua toàn bộ nút bài học trên màn hình để tô lại màu
        if hasattr(self, 'nut_bai_hoc_dict'):
            for bai, btn in self.nut_bai_hoc_dict.items():
                is_done = bai in self.bai_da_hoc
                btn_color = "#00E676" if is_done else "#3A3B3C"
                text_color = "#000000" if is_done else "white"
                text_hien_thi = f"✅ {bai}" if is_done else bai

                # Cập nhật trực tiếp lên giao diện
                btn.configure(fg_color=btn_color, text_color=text_color, text=text_hien_thi)

    def chon_bai_hoc_logic(self, ten_bai):
        if self.logic_hoc:
            self.bai_hien_tai = ten_bai
            muc_tieu, duong_dan_anh = self.logic_hoc.thiet_lap_bai_hoc(ten_bai)

            self.lbl_tieu_de_bai_phai.configure(text=f"Đang học: Chữ {muc_tieu}")
            self.lbl_ket_qua_hoc.configure(text=f"Đang chờ chữ: {muc_tieu}", text_color="#FFCC00")

            if os.path.exists(duong_dan_anh):
                img = Image.open(duong_dan_anh)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(180, 180))
                self.lbl_anh_mau.configure(image=ctk_img, text="")
            else:
                self.lbl_anh_mau.configure(image=None, text="[Thiếu ảnh]")

            if hasattr(self.logic_hoc, 'lay_mo_ta_huong_dan'):
                mo_ta = self.logic_hoc.lay_mo_ta_huong_dan(muc_tieu)
                self.lbl_mo_ta.configure(text=mo_ta)
    # =======================================================
    # LOGIC FLASHCARD (INLINE UI)
    # =======================================================
    def mo_kiem_tra(self):
        # 1. Điều kiện mở khóa: >= 5 chữ
        if not hasattr(self, 'bai_da_hoc') or len(self.bai_da_hoc) < 5:
            self.lbl_mo_ta.configure(text="⚠️ Bạn cần học xanh ít nhất 5 bài để mở khóa Flashcard!", text_color="#e74c3c")
            return

        self.dang_kiem_tra = True
        self.cau_hoi_da_hoi = []  # Bộ nhớ lưu các chữ đã ra để không bị lặp
        self.loai_cau_hoi = 1     # 1: Múa tay (Camera), 2: Bấm trắc nghiệm

        # 2. Vô hiệu hóa danh sách bài học bên phải
        for btn in self.nut_bai_hoc_dict.values():
            btn.configure(state="disabled")

        # 3. Giấu UI miêu tả cũ, đưa UI Flashcard vào
        self.lbl_tieu_de_huong_dan.pack_forget()
        self.lbl_mo_ta.pack_forget()
        self.khung_nut_duoi.pack_forget()

        self.khung_flashcard = ctk.CTkFrame(self.khung_duoi, fg_color="transparent")
        self.khung_flashcard.pack(fill="both", expand=True, padx=20, pady=10)

        # Header Flashcard (Có dấu X tắt)
        header_fc = ctk.CTkFrame(self.khung_flashcard, fg_color="transparent")
        header_fc.pack(fill="x")
        ctk.CTkLabel(header_fc, text="🧠 CHẾ ĐỘ KIỂM TRA", font=self.font_tieu_de, text_color="#f39c12").pack(side="left")
        ctk.CTkButton(header_fc, text="✖ Thoát", width=60, fg_color="#c0392b", hover_color="#a93226", command=self.dong_kiem_tra).pack(side="right")

        # Khung Nội dung
        self.lbl_fc_cau_hoi = ctk.CTkLabel(self.khung_flashcard, text="Đang tải thẻ...", font=("Segoe UI", 24, "bold"))
        self.lbl_fc_cau_hoi.pack(pady=(15, 5))
        self.lbl_fc_trang_thai = ctk.CTkLabel(self.khung_flashcard, text="...", font=self.font_chu)
        self.lbl_fc_trang_thai.pack(pady=5)

        # Khung Trắc nghiệm (Chỉ hiện khi ra mode 2)
        self.khung_trac_nghiem = ctk.CTkFrame(self.khung_flashcard, fg_color="transparent")

        self.load_cau_hoi_flashcard()

    def load_cau_hoi_flashcard(self):
        if not self.dang_kiem_tra: return

        # Lọc các câu chưa hỏi. Nếu hỏi hết rồi thì reset để quay vòng lại.
        ds_co_the_hoi = [b for b in self.bai_da_hoc if b not in self.cau_hoi_da_hoi]
        if not ds_co_the_hoi:
            self.cau_hoi_da_hoi = []
            ds_co_the_hoi = list(self.bai_da_hoc)

        bai_chon = random.choice(ds_co_the_hoi)
        self.cau_hoi_da_hoi.append(bai_chon)
        self.muc_tieu_quiz_hien_tai = self.logic_hoc._trich_xuat_chu(bai_chon)

        # Đẩy ảnh lên ô vuông nhỏ bên phải màn hình
        duong_dan_anh = os.path.join(self.logic_hoc.thu_muc_anh, f"{self.muc_tieu_quiz_hien_tai}.png")
        if os.path.exists(duong_dan_anh):
            img = Image.open(duong_dan_anh)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(180, 180))
            self.lbl_anh_mau.configure(image=ctk_img, text="")
        else:
            self.lbl_anh_mau.configure(image=None, text="[Thiếu ảnh Flashcard]")

        # Tỉ lệ 70% bắt làm dấu bằng Cam, 30% cho đoán trắc nghiệm dựa trên ảnh
        self.loai_cau_hoi = random.choices([1, 2], weights=[70, 30])[0]

        if self.loai_cau_hoi == 1:
            # Mode 1: Yêu cầu Camera
            self.khung_trac_nghiem.pack_forget()
            self.lbl_fc_cau_hoi.configure(text=f"Hãy làm ký hiệu chữ: {self.muc_tieu_quiz_hien_tai}")
            self.lbl_fc_trang_thai.configure(text="Đưa tay lên camera...", text_color="white")
            self.lbl_tieu_de_bai_phai.configure(text="Ảnh gợi ý (Ghi nhớ)")
        else:
            # Mode 2: Trắc nghiệm ABCD
            self.lbl_fc_cau_hoi.configure(text="Ảnh bên phải là chữ gì?")
            self.lbl_fc_trang_thai.configure(text="Hãy chọn đáp án đúng bên dưới", text_color="white")
            self.lbl_tieu_de_bai_phai.configure(text="Câu hỏi Trắc nghiệm")

            self.khung_trac_nghiem.pack(pady=10)
            for widget in self.khung_trac_nghiem.winfo_children():
                widget.destroy()

            # Tạo bộ đáp án (1 đúng + 3 sai ngẫu nhiên lấy từ bài đã học)
            dap_an = [self.muc_tieu_quiz_hien_tai]
            ds_sai = [self.logic_hoc._trich_xuat_chu(b) for b in self.bai_da_hoc if self.logic_hoc._trich_xuat_chu(b) != self.muc_tieu_quiz_hien_tai]
            dap_an.extend(random.sample(ds_sai, min(3, len(ds_sai))))
            random.shuffle(dap_an)

            for da in dap_an:
                ctk.CTkButton(self.khung_trac_nghiem, text=da, font=self.font_chu_dam, width=60, height=40,
                              command=lambda ans=da: self.kiem_tra_trac_nghiem(ans)).pack(side="left", padx=10)

    def kiem_tra_trac_nghiem(self, dap_an_chon):
        """Hàm chấm điểm khi user bấm nút ABCD ở Mode 2"""
        if dap_an_chon == self.muc_tieu_quiz_hien_tai:
            self.lbl_fc_trang_thai.configure(text="✅ CHÍNH XÁC! Đổi thẻ mới...", text_color=self.mau_thanh_cong)
            # Khóa nút lại tránh bấm nhiều lần
            for widget in self.khung_trac_nghiem.winfo_children():
                widget.configure(state="disabled")
            self.after(1500, self.load_cau_hoi_flashcard)
        else:
            self.lbl_fc_trang_thai.configure(text="❌ Sai rồi, hãy nhìn kỹ ảnh lại nhé!", text_color="#e74c3c")

    def dong_kiem_tra(self):
        """Khi bấm dấu X tắt góc phải"""
        self.dang_kiem_tra = False
        self.khung_flashcard.destroy()

        # Dọn dẹp ô ảnh
        self.lbl_anh_mau.configure(image=None, text="[Chưa có ảnh]")
        self.lbl_tieu_de_bai_phai.configure(text="Chưa chọn bài")

        # Phục hồi UI bài học bình thường
        self.lbl_mo_ta.configure(text="(Vui lòng chọn bài học ở danh sách bên phải)", text_color="#A0A0A0")
        self.lbl_mo_ta.pack(anchor="w", padx=20, pady=5)
        self.khung_nut_duoi.pack(fill="x", side="bottom", pady=15, padx=20)

        # Mở khóa lại danh sách bài học
        for btn in self.nut_bai_hoc_dict.values():
            btn.configure(state="normal")



    # =======================================================
    # TRANG 2: THỰC HÀNH TỰ DO
    # =======================================================
    def tao_trang_thuc_hanh(self):
        trang = ctk.CTkFrame(self.khung_chinh, fg_color="transparent")
        trang.grid_columnconfigure(0, weight=7)
        trang.grid_columnconfigure(1, weight=3)
        trang.grid_rowconfigure(0, weight=1)

        khung_trai = ctk.CTkFrame(trang, fg_color="transparent")
        khung_trai.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        khung_trai.grid_columnconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(1, weight=0)

        khung_cam = ctk.CTkFrame(khung_trai, fg_color=self.mau_card, corner_radius=15)
        khung_cam.grid(row=0, column=0, sticky="nsew", pady=(0, 15))

        khung_dieu_khien = ctk.CTkFrame(khung_cam, fg_color="transparent")
        khung_dieu_khien.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(khung_dieu_khien, text="▶ BẬT CAM", font=self.font_chu_dam, fg_color=self.mau_chu_dao, hover_color=self.mau_hover, command=self.bat_camera, width=100).pack(side="left", padx=5)
        ctk.CTkButton(khung_dieu_khien, text="⏹ TẮT", font=self.font_chu_dam, fg_color="#555555", hover_color="#333333", command=self.tat_camera, width=80).pack(side="left", padx=5)

        khung_man_hinh = ctk.CTkFrame(khung_cam, fg_color="#000000", width=640, height=480)
        khung_man_hinh.pack(pady=10, expand=True)
        khung_man_hinh.grid_propagate(False)

        self.lbl_camera_thuc_hanh = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH ]", text_color="#555555")
        self.lbl_camera_thuc_hanh.place(relx=0.5, rely=0.5, anchor="center")

        khung_duoi = ctk.CTkFrame(khung_trai, fg_color=self.mau_card, corner_radius=15)
        khung_duoi.grid(row=1, column=0, sticky="nsew")

        ctk.CTkLabel(khung_duoi, text="📝 Câu hoàn chỉnh:", font=self.font_tieu_de).pack(anchor="w", padx=20, pady=(15, 5))

        self.lbl_cau_hoan_chinh = ctk.CTkLabel(khung_duoi, text="", font=("Segoe UI", 28, "bold"), text_color="#00E676", fg_color="#1E1E1E", corner_radius=10, height=60, anchor="w")
        self.lbl_cau_hoan_chinh.pack(fill="x", padx=20, pady=10)

        khung_nut_duoi = ctk.CTkFrame(khung_duoi, fg_color="transparent")
        khung_nut_duoi.pack(fill="x", side="bottom", pady=15, padx=20)

        ctk.CTkButton(khung_nut_duoi, text="Dấu cách (Space)", font=self.font_chu_dam, fg_color="#3498db", hover_color="#2980b9", command=self.thuc_hanh_them_khoang_trang).pack(side="left", padx=5)
        ctk.CTkButton(khung_nut_duoi, text="⌫ Xóa 1 ký tự", font=self.font_chu_dam, fg_color="#e67e22", hover_color="#d35400", command=self.thuc_hanh_xoa_ky_tu).pack(side="left", padx=5)
        ctk.CTkButton(khung_nut_duoi, text="🗑 Xóa toàn bộ", font=self.font_chu_dam, fg_color="#c0392b", hover_color="#a93226", command=self.thuc_hanh_xoa_het).pack(side="right", padx=5)

        khung_phai = ctk.CTkFrame(trang, fg_color=self.mau_card, corner_radius=15)
        khung_phai.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(khung_phai, text="AI ĐANG NHẬN DIỆN", font=self.font_tieu_de).pack(pady=(30, 10))

        self.lbl_thuchanh_ket_qua = ctk.CTkLabel(khung_phai, text="...", font=("Segoe UI Black", 120, "bold"), text_color="#FFCC00")
        self.lbl_thuchanh_ket_qua.pack(pady=(40, 20), expand=True)

        self.lbl_thuchanh_tin_cay = ctk.CTkLabel(khung_phai, text="Đang chờ...", font=self.font_chu)
        self.lbl_thuchanh_tin_cay.pack(pady=10)

        ctk.CTkButton(khung_phai, text="➕ THÊM VÀO CÂU", font=("Segoe UI", 20, "bold"), height=70, fg_color="#27ae60", hover_color="#2ecc71", command=self.thuc_hanh_them_chu).pack(fill="x", side="bottom", padx=20, pady=30)

        return trang

    def thuc_hanh_them_chu(self):
        if hasattr(self, 'logic_thuc_hanh') and self.logic_thuc_hanh:
            cau = self.logic_thuc_hanh.them_chu_vao_cau()
            self.lbl_cau_hoan_chinh.configure(text=cau)

    def thuc_hanh_them_khoang_trang(self):
        if hasattr(self, 'logic_thuc_hanh') and self.logic_thuc_hanh:
            cau = self.logic_thuc_hanh.them_khoang_trang()
            self.lbl_cau_hoan_chinh.configure(text=cau)

    def thuc_hanh_xoa_ky_tu(self):
        if hasattr(self, 'logic_thuc_hanh') and self.logic_thuc_hanh:
            cau = self.logic_thuc_hanh.xoa_ky_tu_cuoi()
            self.lbl_cau_hoan_chinh.configure(text=cau)

    def thuc_hanh_xoa_het(self):
        if hasattr(self, 'logic_thuc_hanh') and self.logic_thuc_hanh:
            cau = self.logic_thuc_hanh.xoa_toan_bo()
            self.lbl_cau_hoan_chinh.configure(text=cau)

    # =======================================================
    # LUỒNG XỬ LÝ CAMERA
    # =======================================================
    def bat_camera(self):
        if not self.camera_running:
            self.camera_running = True
            self.latest_frame = None
            self.camera_thread = threading.Thread(target=self.luong_camera_ngam, daemon=True)
            self.camera_thread.start()
            self.cap_nhat_giao_dien()

    def tat_camera(self):
        self.camera_running = False
        try:
            self.lbl_camera_main.configure(image="", text="[ ĐANG TẮT CAMERA... ]")
            self.lbl_ket_qua_hoc.configure(text="Chưa bật camera", text_color="#FFCC00")
        except:
            pass

        try:
            self.lbl_camera_thuc_hanh.configure(image="", text="[ ĐANG TẮT CAMERA... ]")
            self.lbl_thuchanh_ket_qua.configure(text="...", text_color="#FFCC00")
            self.lbl_thuchanh_tin_cay.configure(text="Đang chờ...")
        except:
            pass

    def luong_camera_ngam(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        while self.camera_running and cap and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)

                if self.engine is not None:
                    frame_ve, chu_doan, do_tin, nguon = self.engine.xu_ly_frame(frame)
                else:
                    frame_ve, chu_doan, do_tin, nguon = frame, "...", 0.0, "..."

                rgb_frame = cv2.cvtColor(frame_ve, cv2.COLOR_BGR2RGB)

                self.latest_frame = rgb_frame
                self.latest_prediction = (chu_doan, do_tin, nguon)
            time.sleep(0.01)

        if cap is not None:
            cap.release()

        try:
            self.lbl_camera_main.configure(image="", text="[ MÀN HÌNH ĐÃ TẮT ]")
            self.lbl_camera_thuc_hanh.configure(image="", text="[ MÀN HÌNH ĐÃ TẮT ]")
        except:
            pass
    # =======================================================
    # TRANG 3: HỒ SƠ & BẢNG XẾP HẠNG
    # =======================================================
    def tao_trang_ho_so(self):
        trang = ctk.CTkFrame(self.khung_chinh, fg_color="transparent")
        ctk.CTkLabel(trang, text="TRUNG TÂM HỒ SƠ & THÀNH TÍCH", font=self.font_tieu_de_lon, text_color=self.mau_chu_dao).pack(pady=(20, 30))

        # Khung chia 2 cột
        khung_chia_cot = ctk.CTkFrame(trang, fg_color="transparent")
        khung_chia_cot.pack(fill="both", expand=True, padx=20)
        khung_chia_cot.grid_columnconfigure(0, weight=4)
        khung_chia_cot.grid_columnconfigure(1, weight=6)

        # === CỘT TRÁI: THÔNG TIN CÁ NHÂN (LUÔN HIỂN THỊ) ===
        khung_trai_hs = ctk.CTkFrame(khung_chia_cot, fg_color=self.mau_card, corner_radius=15)
        khung_trai_hs.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(khung_trai_hs, text="👤 THÔNG TIN CỦA TÔI", font=self.font_tieu_de).pack(pady=20)
        self.lbl_hs_ten = ctk.CTkLabel(khung_trai_hs, text="Tên: ...", font=self.font_chu_dam)
        self.lbl_hs_ten.pack(pady=10)
        self.lbl_hs_khen_thuong = ctk.CTkLabel(khung_trai_hs, text="🏆 Kỷ Lục: 0", font=("Segoe UI", 26, "bold"), text_color="#FFCC00")
        self.lbl_hs_khen_thuong.pack(pady=15)
        self.lbl_hs_so_lan = ctk.CTkLabel(khung_trai_hs, text="Số lần chơi: 0", font=self.font_chu)
        self.lbl_hs_so_lan.pack(pady=10)

        self.btn_dang_xuat = ctk.CTkButton(khung_trai_hs, text="Đăng Xuất", fg_color="#c0392b", hover_color="#a93226", command=self.xu_ly_dang_xuat)
        # Nút này sẽ được hiện lên nếu là User, ẩn đi nếu là Guest

        # === CỘT PHẢI: KHUNG ĐA NĂNG (LOGIN HOẶC LEADERBOARD) ===
        self.khung_phai_hs = ctk.CTkFrame(khung_chia_cot, fg_color=self.mau_sidebar, corner_radius=15)
        self.khung_phai_hs.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.lbl_tieu_de_phai = ctk.CTkLabel(self.khung_phai_hs, text="ĐANG TẢI...", font=self.font_tieu_de)
        self.lbl_tieu_de_phai.pack(pady=20)

        # 1. Bảng Đăng Nhập (Sẽ nhét vào cột phải nếu là Guest)
        self.khung_dang_nhap = ctk.CTkFrame(self.khung_phai_hs, fg_color="transparent")
        self.txt_user = ctk.CTkEntry(self.khung_dang_nhap, placeholder_text="Tên đăng nhập", width=300, height=40)
        self.txt_user.pack(pady=10)
        self.txt_pass = ctk.CTkEntry(self.khung_dang_nhap, placeholder_text="Mật khẩu", show="*", width=300, height=40)
        self.txt_pass.pack(pady=10)
        self.txt_ten = ctk.CTkEntry(self.khung_dang_nhap, placeholder_text="Tên hiển thị (chỉ dùng khi đăng ký)", width=300, height=40)
        self.txt_ten.pack(pady=10)

        self.lbl_loi_auth = ctk.CTkLabel(self.khung_dang_nhap, text="", text_color="#e74c3c")
        self.lbl_loi_auth.pack(pady=5)

        khung_nut_auth = ctk.CTkFrame(self.khung_dang_nhap, fg_color="transparent")
        khung_nut_auth.pack(pady=10)
        ctk.CTkButton(khung_nut_auth, text="Đăng Nhập", command=self.xu_ly_dang_nhap, width=140).pack(side="left", padx=10)
        ctk.CTkButton(khung_nut_auth, text="Đăng Ký", fg_color="#27ae60", hover_color="#2ecc71", command=self.xu_ly_dang_ky, width=140).pack(side="left", padx=10)

        # 2. Bảng Xếp Hạng (Sẽ nhét vào cột phải nếu là User)
        self.khung_danh_sach_top = ctk.CTkScrollableFrame(self.khung_phai_hs, fg_color="transparent")

        return trang

    def ve_lai_giao_dien_ho_so(self):
        """Kiểm tra thân phận và sắp xếp lại giao diện cho phù hợp"""
        if not self.logic_ho_so: return

        # Luôn luôn cập nhật thông tin cột trái
        du_lieu = self.logic_ho_so.lay_thong_tin()
        self.lbl_hs_ten.configure(text=f"Học viên: {du_lieu['ten_hien_thi']}")
        self.lbl_hs_khen_thuong.configure(text=f"🏆 Kỷ Lục: {du_lieu['diem_cao_nhat']} điểm")
        self.lbl_hs_so_lan.configure(text=f"🎮 Đã chơi: {du_lieu['so_lan_choi_game']} lần")

        # Kiểm tra xem có phải là Guest không
        is_guest = (self.logic_ho_so.id_tai_khoan_hien_tai == self.logic_ho_so.id_guest)

        if is_guest:
            # Nếu là KHÁCH: Cột phải hiện form Đăng Nhập
            self.khung_danh_sach_top.pack_forget()
            self.btn_dang_xuat.pack_forget() # Khách thì không có nút đăng xuất

            self.lbl_tieu_de_phai.configure(text="🔒 ĐĂNG NHẬP ĐỂ MỞ KHÓA BẢNG XẾP HẠNG", text_color="#e67e22")
            self.khung_dang_nhap.pack(fill="both", expand=True, padx=20)
        else:
            # Nếu là USER: Cột phải hiện Bảng Xếp Hạng
            self.khung_dang_nhap.pack_forget()
            self.btn_dang_xuat.pack(side="bottom", pady=20) # Hiện nút đăng xuất

            self.lbl_tieu_de_phai.configure(text="🌟 BẢNG VÀNG THÀNH TÍCH", text_color="#2ecc71")
            self.khung_danh_sach_top.pack(fill="both", expand=True, padx=20, pady=10)

            # Quét DB và in ra Top Người Chơi
            for widget in self.khung_danh_sach_top.winfo_children():
                widget.destroy()
            try:
                top_players = self.logic_ho_so.lay_bang_xep_hang(top_n=5)
                if not top_players:
                    ctk.CTkLabel(self.khung_danh_sach_top, text="Chưa có ai ghi điểm. Hãy là người đầu tiên!", text_color="#888").pack(pady=20)
                else:
                    huy_hieu = ["🥇", "🥈", "🥉", "🏅", "🏅"]
                    for i, (ten, diem) in enumerate(top_players):
                        thanh = ctk.CTkFrame(self.khung_danh_sach_top, fg_color="#3A3B3C", corner_radius=8)
                        thanh.pack(fill="x", pady=5)
                        icon = huy_hieu[i] if i < len(huy_hieu) else "⭐"
                        ctk.CTkLabel(thanh, text=f"{icon} Hạng {i+1}: {ten}", font=self.font_chu_dam).pack(side="left", padx=15, pady=10)
                        ctk.CTkLabel(thanh, text=f"{diem} điểm", font=self.font_chu_dam, text_color="#FFCC00").pack(side="right", padx=15, pady=10)
            except Exception as e:
                print(f"Lỗi Leaderboard: {e}")

    # Các hàm xử lý Auth
    def xu_ly_dang_nhap(self):
        ok, msg = self.logic_ho_so.dang_nhap(self.txt_user.get(), self.txt_pass.get())
        if ok:
            self.lbl_loi_auth.configure(text="")
            self.txt_user.delete(0, 'end')
            self.txt_pass.delete(0, 'end')
            self.ve_lai_giao_dien_ho_so()
            self.cap_nhat_ui_danh_sach_bai_hoc()
        else: self.lbl_loi_auth.configure(text=msg)

    def xu_ly_dang_ky(self):
        ok, msg = self.logic_ho_so.dang_ky(self.txt_user.get(), self.txt_pass.get(), self.txt_ten.get())
        if ok:
            self.lbl_loi_auth.configure(text="")
            self.txt_user.delete(0, 'end')
            self.txt_pass.delete(0, 'end')
            self.txt_ten.delete(0, 'end')
            self.ve_lai_giao_dien_ho_so()
            self.cap_nhat_ui_danh_sach_bai_hoc()
        else: self.lbl_loi_auth.configure(text=msg)

    def xu_ly_dang_xuat(self):
        self.logic_ho_so.dang_xuat()
        self.ve_lai_giao_dien_ho_so()
        self.cap_nhat_ui_danh_sach_bai_hoc()
    # =======================================================
    # TRANG 4: MINIGAME (GIAO DIỆN NEON SIÊU CHÁY)
    # =======================================================
    def tao_trang_tro_choi(self):
        trang = ctk.CTkFrame(self.khung_chinh, fg_color="transparent")
        trang.grid_columnconfigure(0, weight=7)
        trang.grid_columnconfigure(1, weight=3)
        trang.grid_rowconfigure(0, weight=1)

        # Trái: Camera
        khung_trai = ctk.CTkFrame(trang, fg_color="transparent")
        khung_trai.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        khung_trai.grid_columnconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(0, weight=1)

        khung_cam = ctk.CTkFrame(khung_trai, fg_color=self.mau_card, corner_radius=15)
        khung_cam.grid(row=0, column=0, sticky="nsew")

        khung_dieu_khien = ctk.CTkFrame(khung_cam, fg_color="transparent")
        khung_dieu_khien.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(khung_dieu_khien, text="▶ BẬT CAM", font=self.font_chu_dam, fg_color=self.mau_chu_dao, hover_color=self.mau_hover, command=self.bat_camera, width=100).pack(side="left", padx=5)
        ctk.CTkButton(khung_dieu_khien, text="⏹ TẮT", font=self.font_chu_dam, fg_color="#555555", hover_color="#333333", command=self.tat_camera, width=80).pack(side="left", padx=5)

        khung_man_hinh = ctk.CTkFrame(khung_cam, fg_color="#000000", width=640, height=480)
        khung_man_hinh.pack(pady=10, expand=True)
        khung_man_hinh.grid_propagate(False)

        self.lbl_camera_game = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH ]", text_color="#555555")
        self.lbl_camera_game.place(relx=0.5, rely=0.5, anchor="center")

        # Phải: Bảng điều khiển Game phong cách Neon
        self.khung_phai_game = ctk.CTkFrame(trang, fg_color=self.mau_card, corner_radius=15)
        self.khung_phai_game.grid(row=0, column=1, sticky="nsew")

        khung_header = ctk.CTkFrame(self.khung_phai_game, fg_color="transparent")
        khung_header.pack(fill="x", padx=20, pady=20)

        self.lbl_game_diem = ctk.CTkLabel(khung_header, text="ĐIỂM: 0", font=("Segoe UI Black", 24, "bold"), text_color="#FFF")
        self.lbl_game_diem.pack(side="left")

        self.lbl_game_cap_do = ctk.CTkLabel(khung_header, text="LV 1", font=("Segoe UI Black", 24, "bold"), text_color="#00FFCC")
        self.lbl_game_cap_do.pack(side="left", padx=20)

        self.lbl_game_combo = ctk.CTkLabel(khung_header, text="COMBO x0", font=("Segoe UI Black", 20, "italic"), text_color="#FFCC00")
        self.lbl_game_combo.pack(side="right")

        self.khung_target = ctk.CTkFrame(self.khung_phai_game, fg_color="#222", corner_radius=20, width=250, height=250)
        self.khung_target.pack(pady=20)
        self.khung_target.pack_propagate(False)

        self.lbl_game_cau_hoi = ctk.CTkLabel(self.khung_target, text="READY", font=("Segoe UI Black", 70, "bold"), text_color="#FFCC00")
        self.lbl_game_cau_hoi.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_game_tim = ctk.CTkLabel(self.khung_phai_game, text="❤️ ❤️ ❤️", font=("Segoe UI", 35), text_color="#E50914")
        self.lbl_game_tim.pack(pady=10)

        self.thanh_thoi_gian = ctk.CTkProgressBar(self.khung_phai_game, width=280, height=18, progress_color=self.mau_thanh_cong, fg_color="#333", corner_radius=10)
        self.thanh_thoi_gian.set(1.0)
        self.thanh_thoi_gian.pack(pady=10)

        self.lbl_game_tin_nhan = ctk.CTkLabel(self.khung_phai_game, text="Nhấn BẮT ĐẦU để chơi!", font=self.font_tieu_de, wraplength=300)
        self.lbl_game_tin_nhan.pack(pady=15)

        khung_nut_game = ctk.CTkFrame(self.khung_phai_game, fg_color="transparent")
        khung_nut_game.pack(fill="x", side="bottom", padx=20, pady=30)

        self.btn_toggle_game = ctk.CTkButton(khung_nut_game, text="🏁 BẮT ĐẦU", font=("Segoe UI Black", 20), height=60, fg_color=self.mau_chu_dao, hover_color=self.mau_hover, command=self.toggle_game)
        self.btn_toggle_game.pack(fill="x")

        return trang

    # --- CÁC HÀM HIỆU ỨNG VÀ LOGIC GAME ---
    def hieu_ung_bay_len(self, text, color, x_rel, y_rel_start):
        try:
            lbl_float = ctk.CTkLabel(self.khung_phai_game, text=text, font=("Segoe UI Black", 40, "bold"), text_color=color)
            lbl_float.place(relx=x_rel, rely=y_rel_start, anchor="center")

            def move_up(widget, current_y, steps):
                if steps > 0 and widget.winfo_exists():
                    widget.place(relx=x_rel, rely=current_y, anchor="center")
                    self.after(30, lambda: move_up(widget, current_y - 0.015, steps - 1))
                elif widget.winfo_exists():
                    widget.destroy()
            move_up(lbl_float, y_rel_start, 25)
        except: pass

    def hieu_ung_chop_mau(self, widget, mau_sang, mau_goc, so_lan=4):
        if so_lan > 0:
            mau_hien_tai = mau_sang if so_lan % 2 == 0 else mau_goc
            widget.configure(text_color=mau_hien_tai)
            self.after(100, lambda: self.hieu_ung_chop_mau(widget, mau_sang, mau_goc, so_lan - 1))
        else:
            widget.configure(text_color=mau_goc)

    def toggle_game(self):
        if not self.camera_running:
            self.lbl_game_tin_nhan.configure(text="⚠️ Hãy BẬT CAM trước khi chơi!", text_color="#FFCC00")
            return

        if hasattr(self, 'logic_game') and self.logic_game:
            if self.logic_game.dang_choi:
                # Đang chơi -> Bấm dừng
                self.logic_game.dang_choi = False

                # --- LƯU ĐIỂM VÀO DB KHI TỰ BỎ CUỘC ---
                if hasattr(self, 'logic_ho_so') and self.logic_ho_so:
                    self.logic_ho_so.cap_nhat_sau_khi_choi(self.logic_game.diem_so)

                self.btn_toggle_game.configure(text="🏁 CHƠI LẠI", fg_color=self.mau_chu_dao, hover_color=self.mau_hover)
                self.lbl_game_tin_nhan.configure(text=f"Đã dừng! Ghi nhận: {self.logic_game.diem_so} điểm.", text_color="white")
            else:
                # Bắt đầu game mới
                cau_hoi = self.logic_game.bat_dau_game() # Đã sửa: Chỉ nhận 1 biến

                self.lbl_game_cau_hoi.configure(text=f"{cau_hoi}", font=("Segoe UI Black", 100, "bold"), text_color="#FFF")
                self.lbl_game_diem.configure(text="ĐIỂM: 0")
                self.lbl_game_combo.configure(text="COMBO x0", text_color="#FFCC00")
                self.lbl_game_cap_do.configure(text="LV 1")
                self.lbl_game_tim.configure(text="❤️ ❤️ ❤️")
                self.thanh_thoi_gian.set(1.0)
                self.lbl_game_tin_nhan.configure(text="Múa tay thật nhanh để sinh tồn!", text_color=self.mau_thanh_cong)
                self.btn_toggle_game.configure(text="⏹ DỪNG LẠI", fg_color="#555555", hover_color="#333333")

    def cap_nhat_giao_dien(self):
        if self.camera_running and self.latest_frame is not None:
            img = ctk.CTkImage(light_image=Image.fromarray(self.latest_frame), size=(640, 480))
            chu, tin_cay, nguon = self.latest_prediction

            # ================= XỬ LÝ MÀN HỌC TẬP =================
            if self.trang_hien_tai == "Học Tập":
                self.lbl_camera_main.configure(image=img, text="")

                # --- 1. NHÁNH CHẤM ĐIỂM CHẾ ĐỘ KIỂM TRA (FLASHCARD) ---
                if getattr(self, 'dang_kiem_tra', False):
                    # Chỉ quét Cam khi Flashcard đang ở Mode 1 (Múa tay) và đang có mục tiêu
                    if getattr(self, 'loai_cau_hoi', 0) == 1 and getattr(self, 'muc_tieu_quiz_hien_tai', None):
                        is_correct = self.logic_hoc.cham_diem_kiem_tra(chu, tin_cay, self.muc_tieu_quiz_hien_tai)
                        if is_correct:
                            self.lbl_fc_trang_thai.configure(text="✅ CHÍNH XÁC! Đổi thẻ mới...",
                                                             text_color=self.mau_thanh_cong)
                            self.muc_tieu_quiz_hien_tai = None  # Khóa tạm thời để cam không chấm liên tục nhiều lần
                            self.after(1500, self.load_cau_hoi_flashcard)

                # --- 2. NHÁNH CHẤM ĐIỂM BÀI HỌC BÌNH THƯỜNG (Code gốc của bạn) ---
                elif not getattr(self, 'dang_kiem_tra', False) and self.logic_hoc and self.logic_hoc.muc_tieu_hien_tai:
                    trang_thai, thong_bao = self.logic_hoc.kiem_tra_ket_qua(chu, tin_cay)

                    if trang_thai == "DUNG":
                        self.lbl_ket_qua_hoc.configure(text=thong_bao, text_color=self.mau_thanh_cong)

                        if self.bai_hien_tai and self.bai_hien_tai not in self.bai_da_hoc:
                            self.bai_da_hoc.add(self.bai_hien_tai)

                            # --- GỌI SHIPPER LƯU XUỐNG DATABASE ---
                            if hasattr(self, 'logic_ho_so') and self.logic_ho_so:
                                self.logic_ho_so.danh_dau_da_hoc(self.bai_hien_tai)
                            # --------------------------------------

                            if self.bai_hien_tai in self.nut_bai_hoc_dict:
                                self.nut_bai_hoc_dict[self.bai_hien_tai].configure(
                                    fg_color="#00E676", text_color="#000000", text=f"✅ {self.bai_hien_tai}"
                                )
                    elif trang_thai == "SAI":
                        self.lbl_ket_qua_hoc.configure(text=thong_bao, text_color=self.mau_chu_dao)
                    else:
                        self.lbl_ket_qua_hoc.configure(text=thong_bao, text_color="#FFCC00")

            # ================= XỬ LÝ MÀN THỰC HÀNH =================
            elif self.trang_hien_tai == "Thực Hành Tự Do":
                if hasattr(self, 'lbl_camera_thuc_hanh'):
                    self.lbl_camera_thuc_hanh.configure(image=img, text="")

                if hasattr(self, 'logic_thuc_hanh') and self.logic_thuc_hanh:
                    chu_ht, tb, mau = self.logic_thuc_hanh.xu_ly_ket_qua(chu, tin_cay)

                    # --- LOGIC TỰ ĐỘNG GHÉP CHỮ KHI RÚT TAY ---
                    if chu_ht != "...":
                        # Đang thấy chữ hợp lệ -> Lưu lại và reset đồng hồ
                        tb = f"{tb} | Engine: {nguon}"
                        self.chu_cho_them = chu_ht
                        self.thoi_diem_mat_tay = 0
                    else:
                        # Camera không thấy tay
                        if self.chu_cho_them != "":
                            if self.thoi_diem_mat_tay == 0:
                                self.thoi_diem_mat_tay = time.time() # Bắt đầu đếm ngược
                            elif time.time() - self.thoi_diem_mat_tay > self.delay_tu_dong_them:
                                # Đã qua 1 giây rút tay -> Hành động!
                                if self.chu_cho_them == "SPACE":
                                    self.thuc_hanh_them_khoang_trang()
                                else:
                                    self.logic_thuc_hanh.chu_hien_tai = self.chu_cho_them
                                    self.thuc_hanh_them_chu()

                                self.chu_cho_them = ""
                                self.thoi_diem_mat_tay = 0

                    self.lbl_thuchanh_ket_qua.configure(text=chu_ht, text_color=mau)
                    self.lbl_thuchanh_tin_cay.configure(text=tb)


            # ================= XỬ LÝ MÀN MINIGAME =================
            elif self.trang_hien_tai == "Minigame":
                if hasattr(self, 'lbl_camera_game'):
                    self.lbl_camera_game.configure(image=img, text="")

                if hasattr(self, 'logic_game') and self.logic_game and self.logic_game.dang_choi:
                    # Đã sửa: Gọi đúng hàm kiem_tra_lien_tuc với 7 giá trị trả về
                    trang_thai, cau_hoi, tim, diem, tg_con, combo, cap_do = self.logic_game.kiem_tra_lien_tuc(chu, tin_cay)

                    self.lbl_game_cau_hoi.configure(text=cau_hoi)
                    self.lbl_game_diem.configure(text=f"ĐIỂM: {diem}")
                    self.lbl_game_tim.configure(text="❤️ " * tim if tim > 0 else "💀")
                    self.lbl_game_cap_do.configure(text=f"LV {cap_do}")

                    if combo >= 3:
                        self.lbl_game_combo.configure(text=f"COMBO x{combo} 🔥", text_color=self.mau_chu_dao)
                    elif combo > 0:
                        self.lbl_game_combo.configure(text=f"COMBO x{combo}", text_color="#FFCC00")
                    else:
                        self.lbl_game_combo.configure(text="")

                    if self.logic_game.thoi_gian_gioi_han > 0:
                        phan_tram = tg_con / self.logic_game.thoi_gian_gioi_han
                        self.thanh_thoi_gian.set(phan_tram)
                        if phan_tram > 0.5:
                            self.thanh_thoi_gian.configure(progress_color=self.mau_thanh_cong)
                        elif phan_tram > 0.2:
                            self.thanh_thoi_gian.configure(progress_color="#FFCC00")
                        else:
                            self.thanh_thoi_gian.configure(progress_color=self.mau_chu_dao)

                    if trang_thai == "DUNG":
                        self.hieu_ung_chop_mau(self.lbl_game_cau_hoi, self.mau_thanh_cong, "#FFF")
                        self.lbl_game_tin_nhan.configure(text="PERFECT!", text_color=self.mau_thanh_cong)
                        self.hieu_ung_bay_len(f"+{10 * combo}", self.mau_thanh_cong, x_rel=0.5, y_rel_start=0.45)

                        if self.logic_game.so_cau_dung > 0 and self.logic_game.so_cau_dung % 5 == 0:
                            self.hieu_ung_bay_len("LEVEL UP!", "#00FFCC", x_rel=0.5, y_rel_start=0.55)

                    elif trang_thai == "HET_GIO":
                        self.hieu_ung_chop_mau(self.lbl_game_cau_hoi, self.mau_chu_dao, "#FFF")
                        self.lbl_game_tin_nhan.configure(text="Mất quá lâu! Trừ 1 ❤️", text_color=self.mau_chu_dao)
                        self.hieu_ung_bay_len("-1 ❤️", self.mau_chu_dao, x_rel=0.5, y_rel_start=0.6)

                    elif trang_thai == "SAI_HET_TIM":
                        self.hieu_ung_bay_len("-1 ❤️", self.mau_chu_dao, x_rel=0.5, y_rel_start=0.6)

                        # --- GHI ĐIỂM VÀO DB KHI GAME OVER ---
                        if hasattr(self, 'logic_ho_so') and self.logic_ho_so:
                            self.logic_ho_so.cap_nhat_sau_khi_choi(diem)

                        self.lbl_game_tin_nhan.configure(text=f"💀 GAME OVER! Đã lưu {diem} điểm.", text_color=self.mau_chu_dao)
                        self.btn_toggle_game.configure(text="🏁 CHƠI LẠI", fg_color=self.mau_chu_dao, hover_color=self.mau_hover)

        if self.camera_running:
            self.after(20, self.cap_nhat_giao_dien)

if __name__ == "__main__":
    app = UngDungNhanDien()
    app.mainloop()