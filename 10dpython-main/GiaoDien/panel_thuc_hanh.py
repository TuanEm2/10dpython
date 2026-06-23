import time
import customtkinter as ctk
# Import hàm gọi API đã chuẩn bị trước đó
from XuLyLogic.logic_mo_rong_api import goi_api_mo_rong_cau


class PanelThucHanh(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="transparent")
        self.main_app = main_app  # Giữ liên kết với gui_main để xài chung Camera và AI

        self.chu_cho_them = ""
        self.thoi_diem_mat_tay = 0
        self.delay_tu_dong_them = 1.0
        self.thoi_diem_giu_chu = 0
        self.da_auto_add = False

        self.tao_giao_dien()

    def tao_giao_dien(self):
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        khung_trai = ctk.CTkFrame(self, fg_color="transparent")
        khung_trai.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        khung_trai.grid_columnconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(1, weight=0)

        khung_cam = ctk.CTkFrame(khung_trai, fg_color=self.main_app.mau_card, corner_radius=15)
        khung_cam.grid(row=0, column=0, sticky="nsew", pady=(0, 15))

        khung_dieu_khien = ctk.CTkFrame(khung_cam, fg_color="transparent")
        khung_dieu_khien.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(khung_dieu_khien, text="▶ BẬT CAM", font=self.main_app.font_chu_dam,
                      fg_color=self.main_app.mau_chu_dao, hover_color=self.main_app.mau_hover,
                      command=self.main_app.bat_camera, width=100).pack(side="left", padx=5)
        ctk.CTkButton(khung_dieu_khien, text="⏹ TẮT", font=self.main_app.font_chu_dam, fg_color="#555555",
                      hover_color="#333333", command=self.main_app.tat_camera, width=80).pack(side="left", padx=5)

        khung_man_hinh = ctk.CTkFrame(khung_cam, fg_color="#000000", width=640, height=480)
        khung_man_hinh.pack(pady=10, expand=True)
        khung_man_hinh.grid_propagate(False)

        self.lbl_camera = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH ]", text_color="#555555")
        self.lbl_camera.place(relx=0.5, rely=0.5, anchor="center")

        khung_duoi = ctk.CTkFrame(khung_trai, fg_color=self.main_app.mau_card, corner_radius=15)
        khung_duoi.grid(row=1, column=0, sticky="nsew")

        ctk.CTkLabel(khung_duoi, text="📝 Câu hoàn chỉnh:", font=self.main_app.font_tieu_de).pack(anchor="w", padx=20,
                                                                                                 pady=(15, 5))

        # ĐÂY LÀ NHÃN HIỂN THỊ CÂU HOÀN CHỈNH
        self.lbl_cau_hoan_chinh = ctk.CTkLabel(khung_duoi, text="", font=("Segoe UI", 28, "bold"), text_color="#00E676",
                                               fg_color="#1E1E1E", corner_radius=10, height=60, anchor="w")
        self.lbl_cau_hoan_chinh.pack(fill="x", padx=20, pady=10)

        khung_nut_duoi = ctk.CTkFrame(khung_duoi, fg_color="transparent")
        khung_nut_duoi.pack(fill="x", side="bottom", pady=15, padx=20)

        ctk.CTkButton(khung_nut_duoi, text="Dấu cách (Space)", font=self.main_app.font_chu_dam, fg_color="#3498db",
                      hover_color="#2980b9", command=self.thuc_hanh_them_khoang_trang).pack(side="left", padx=5)
        ctk.CTkButton(khung_nut_duoi, text="⌫ Xóa 1 ký tự", font=self.main_app.font_chu_dam, fg_color="#e67e22",
                      hover_color="#d35400", command=self.thuc_hanh_xoa_ky_tu).pack(side="left", padx=5)
        ctk.CTkButton(khung_nut_duoi, text="🗑 Xóa toàn bộ", font=self.main_app.font_chu_dam, fg_color="#c0392b",
                      hover_color="#a93226", command=self.thuc_hanh_xoa_het).pack(side="right", padx=5)

        khung_phai = ctk.CTkFrame(self, fg_color=self.main_app.mau_card, corner_radius=15)
        khung_phai.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(khung_phai, text="AI ĐANG NHẬN DIỆN", font=self.main_app.font_tieu_de).pack(pady=(30, 10))
        self.lbl_ket_qua = ctk.CTkLabel(khung_phai, text="...", font=("Segoe UI Black", 100, "bold"),
                                        text_color="#FFCC00")
        self.lbl_ket_qua.pack(pady=(40, 20), expand=True)
        self.lbl_tin_cay = ctk.CTkLabel(khung_phai, text="Đang chờ...", font=self.main_app.font_chu)
        self.lbl_tin_cay.pack(pady=10)
        ctk.CTkButton(khung_phai, text="➕ THÊM VÀO CÂU", font=("Segoe UI", 20, "bold"), height=70, fg_color="#27ae60",
                      hover_color="#2ecc71", command=self.thuc_hanh_them_chu).pack(fill="x", side="bottom", padx=20,
                                                                                   pady=30)

    # --- KẾT NỐI VỚI LUỒNG CAMERA TỪ GUI_MAIN ---
    def cap_nhat_khung_hinh(self, img, chu, tin_cay, nguon):
        self.lbl_camera.configure(image=img, text="")
        logic = self.main_app.logic_thuc_hanh

        if logic:
            chu_ht, tb, mau = logic.xu_ly_ket_qua(chu, tin_cay)

            # --- MẸO LÀM ĐẸP CHỮ TRÊN RADAR LỚN ---
            chu_radar = chu_ht.replace("_", " ") if chu_ht != "..." else "..."

            # Co giãn font cho nhãn lớn (Tránh lỗi tràn viền như trong ảnh của bạn)
            so_ky_tu = len(chu_radar)
            co_chu = 100 if so_ky_tu <= 2 else (70 if so_ky_tu <= 6 else (50 if so_ky_tu <= 10 else 35))
            self.lbl_ket_qua.configure(text=chu_radar, text_color=mau, font=("Segoe UI Black", co_chu, "bold"))

            if chu_ht != "...":
                tb = f"{tb} | Engine: {nguon}"
                if self.chu_cho_them != chu_ht:
                    self.chu_cho_them = chu_ht
                    self.thoi_diem_giu_chu = time.time()
                    self.da_auto_add = False
                else:
                    if not self.da_auto_add and (time.time() - self.thoi_diem_giu_chu >= 1.5):
                        if self.chu_cho_them == "SPACE":
                            self.thuc_hanh_them_khoang_trang()
                        else:
                            logic.chu_hien_tai = self.chu_cho_them
                            self.thuc_hanh_them_chu()  # Gọi hàm thêm chữ có bọc API
                        self.da_auto_add = True
                self.thoi_diem_mat_tay = 0
            else:
                if self.chu_cho_them != "":
                    if self.da_auto_add:
                        self.chu_cho_them = ""
                    else:
                        if self.thoi_diem_mat_tay == 0:
                            self.thoi_diem_mat_tay = time.time()
                        elif time.time() - self.thoi_diem_mat_tay > self.delay_tu_dong_them:
                            if self.chu_cho_them == "SPACE":
                                self.thuc_hanh_them_khoang_trang()
                            else:
                                logic.chu_hien_tai = self.chu_cho_them
                                self.thuc_hanh_them_chu()  # Gọi hàm thêm chữ có bọc API
                            self.chu_cho_them = ""
                            self.thoi_diem_mat_tay = 0

            self.lbl_tin_cay.configure(text=tb)

    # ==============================================================
    # HÀM THÊM CHỮ ĐƯỢC TÍCH HỢP TỰ ĐỘNG DỊCH API
    # ==============================================================
    def thuc_hanh_them_chu(self):
        if self.main_app.logic_thuc_hanh:
            # 1. Gọi logic cũ để lấy câu đã được ghép thêm chữ mới
            cau_tho = self.main_app.logic_thuc_hanh.them_chu_vao_cau()

            # 2. Xóa các dấu gạch dưới nếu có (VD: TÔI XIN_CHAO -> TÔI XIN CHAO)
            cau_tho_sach = cau_tho.replace("_", " ")

            # 3. Bắn câu thô lên Server API để lấy câu dịch hoàn chỉnh
            cau_hoan_chinh = goi_api_mo_rong_cau(cau_tho_sach)

            # 4. Hiển thị câu đã dịch lên màn hình
            self.lbl_cau_hoan_chinh.configure(text=cau_hoan_chinh)

    def thuc_hanh_them_khoang_trang(self):
        if self.main_app.logic_thuc_hanh:
            cau_tho = self.main_app.logic_thuc_hanh.them_khoang_trang()
            self.lbl_cau_hoan_chinh.configure(text=goi_api_mo_rong_cau(cau_tho))

    def thuc_hanh_xoa_ky_tu(self):
        if self.main_app.logic_thuc_hanh:
            cau_tho = self.main_app.logic_thuc_hanh.xoa_ky_tu_cuoi()
            # Xóa bớt chữ thì vẫn nên gọi API kiểm tra lại xem có trùng luật từ điển không
            self.lbl_cau_hoan_chinh.configure(text=goi_api_mo_rong_cau(cau_tho))

    def thuc_hanh_xoa_het(self):
        if self.main_app.logic_thuc_hanh:
            self.main_app.logic_thuc_hanh.xoa_toan_bo()
            self.lbl_cau_hoan_chinh.configure(text="")

    def reset_giao_dien(self):
        self.lbl_camera.configure(image="", text="[ ĐANG TẮT CAMERA... ]")
        self.lbl_ket_qua.configure(text="...", text_color="#FFCC00")
        self.lbl_tin_cay.configure(text="Đang chờ...")