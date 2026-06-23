import time
import threading
import os                  # BỔ SUNG DÒNG NÀY
from PIL import Image      # BỔ SUNG DÒNG NÀY
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

        # --- BỔ SUNG NÚT DỊCH CÂU VÀO ĐÂY ---
        self.btn_dich = ctk.CTkButton(khung_nut_duoi, text="🪄 DỊCH CÂU", font=self.main_app.font_chu_dam,
                                      fg_color="#f39c12", hover_color="#d35400", text_color="black",
                                      command=self.thuc_hanh_dich_cau)
        self.btn_dich.pack(side="left", padx=5)
        # ------------------------------------


        ctk.CTkButton(khung_nut_duoi, text="🗑 Xóa toàn bộ", font=self.main_app.font_chu_dam, fg_color="#c0392b",
                      hover_color="#a93226", command=self.thuc_hanh_xoa_het).pack(side="right", padx=5)

        khung_phai = ctk.CTkFrame(self, fg_color=self.main_app.mau_card, corner_radius=15)
        khung_phai.grid(row=0, column=1, sticky="nsew")

        # Thêm thư viện PIL ở đầu file panel_thuc_hanh.py nếu chưa có
        # from PIL import Image

        # --- KHUNG DỊCH NGƯỢC (TEXT-TO-SIGN WINDOW) ĐÃ ĐỒNG BỘ MÀU HỆ THỐNG ---
        self.khung_dich_nguoc = ctk.CTkFrame(khung_phai, fg_color=self.main_app.mau_sidebar, corner_radius=15,
                                             border_width=1,
                                             border_color="#2A2A2A")
        self.khung_dich_nguoc.pack(fill="x", padx=10, pady=15)

        # Tiêu đề khối (Dùng màu xanh mint thành công của app)
        ctk.CTkLabel(self.khung_dich_nguoc, text="✨ CHUYỂN VĂN BẢN THÀNH KÝ HIỆU", font=("Segoe UI", 13, "bold"),
                     text_color=self.main_app.mau_thanh_cong).pack(pady=(10, 5))

        # Ô nhập văn bản (Đồng bộ nền Card tối)
        self.entry_van_ban = ctk.CTkEntry(self.khung_dich_nguoc, placeholder_text="Nhập chữ hoặc câu tiếng Việt...",
                                          font=("Segoe UI", 12), fg_color=self.main_app.mau_card,
                                          border_color="#333333")
        self.entry_van_ban.pack(fill="x", padx=15, pady=5)

        # Nút hành động dịch ngược (Chuyển sang màu đỏ đặc trưng SIGNLENS)
        self.btn_chuyen_doi = ctk.CTkButton(self.khung_dich_nguoc, text="Trình Chiếu Ký Hiệu 👉",
                                            font=("Segoe UI", 12, "bold"), fg_color=self.main_app.mau_chu_dao,
                                            text_color="white",
                                            hover_color=self.main_app.mau_hover, command=self.xu_ly_text_to_sign)
        self.btn_chuyen_doi.pack(pady=5)

        # Nhãn hiển thị hình ảnh động/ký hiệu tuần tự
        self.lbl_hien_thi_ki_hieu = ctk.CTkLabel(self.khung_dich_nguoc, text="Hệ thống sẵn sàng...",
                                                 font=("Segoe UI", 12, "italic"), text_color="#888", width=150,
                                                 height=150)
        self.lbl_hien_thi_ki_hieu.pack(pady=(5, 15))

        # Khai báo các biến bổ trợ luồng chiếu slide ảnh
        self.danh_sach_anh_cho_chieu = []
        self.index_anh_hien_tai = 0
        self.id_after_dich_nguoc = None

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
    # HÀM XỬ LÝ CHUỖI, CO GIÃN FONT VÀ GỌI API THÔNG MINH
    # ==============================================================
    def hien_thi_cau_thong_minh(self, noi_dung):
        """Hàm tự động co giãn font và gập dòng chống tràn viền"""
        noi_dung = str(noi_dung).strip()
        so_ky_tu = len(noi_dung)

        if so_ky_tu <= 12: co_chu = 32
        elif so_ky_tu <= 24: co_chu = 24
        elif so_ky_tu <= 42: co_chu = 18
        else: co_chu = 14

        self.lbl_cau_hoan_chinh.configure(
            text=noi_dung if noi_dung else "...",
            font=("Segoe UI", co_chu, "bold"),
            wraplength=600 # Bẻ dòng nếu câu quá dài
        )

    def _cap_nhat_giao_dien_tho(self, cau_tho):
        """Chỉ gọt bỏ dấu gạch dưới và hiển thị chữ thô, TUYỆT ĐỐI KHÔNG GỌI API"""
        cau_tho_sach = cau_tho.replace("_", " ")
        self.hien_thi_cau_thong_minh(cau_tho_sach)

    def thuc_hanh_them_chu(self):
        if self.main_app.logic_thuc_hanh:
            cau_tho = self.main_app.logic_thuc_hanh.them_chu_vao_cau()
            self._cap_nhat_giao_dien_tho(cau_tho)

    def thuc_hanh_them_khoang_trang(self):
        if self.main_app.logic_thuc_hanh:
            cau_tho = self.main_app.logic_thuc_hanh.them_khoang_trang()
            self._cap_nhat_giao_dien_tho(cau_tho)

    def thuc_hanh_xoa_ky_tu(self):
        if self.main_app.logic_thuc_hanh:
            cau_tho = self.main_app.logic_thuc_hanh.xoa_ky_tu_cuoi()
            self._cap_nhat_giao_dien_tho(cau_tho)

    def thuc_hanh_xoa_het(self):
        if self.main_app.logic_thuc_hanh:
            self.main_app.logic_thuc_hanh.xoa_toan_bo()
            self.hien_thi_cau_thong_minh("")

    # ================= LOGIC DỊCH CÂU MỚI (MANUAL THREADING) =================
    def thuc_hanh_dich_cau(self):
        """Chỉ gọi API khi người dùng bấm nút DỊCH CÂU"""
        if self.main_app.logic_thuc_hanh:
            cau_tho = self.main_app.logic_thuc_hanh.cau_hoan_chinh.replace("_", " ")
            if cau_tho.strip():
                # Khóa nút lại để tránh user bấm spam nhiều lần
                self.btn_dich.configure(state="disabled", text="⏳ Đang dịch...")
                # Bắn API ra luồng phụ để Camera vẫn trơn tru
                threading.Thread(target=self._luong_goi_api_thu_cong, args=(cau_tho,), daemon=True).start()

    def _luong_goi_api_thu_cong(self, cau_tho_sach):
        """Hàm chạy ngầm chờ Server API phản hồi"""
        cau_dich = goi_api_mo_rong_cau(cau_tho_sach)
        # Ép UI cập nhật câu mới
        self.after(0, lambda: self.hien_thi_cau_thong_minh(cau_dich))
        # Mở khóa nút bấm trở lại trạng thái ban đầu
        self.after(0, lambda: self.btn_dich.configure(state="normal", text="🪄 DỊCH CÂU"))

    def reset_giao_dien(self):
        self.lbl_camera.configure(image="", text="[ ĐANG TẮT CAMERA... ]")
        self.lbl_ket_qua.configure(text="...", text_color="#FFCC00")
        self.lbl_tin_cay.configure(text="Đang chờ...")

    def xu_ly_text_to_sign(self):
        """Đọc văn bản từ ô nhập và kích hoạt chuỗi slide ảnh"""
        # Hủy lịch trình chiếu cũ nếu đang chạy dở
        if self.id_after_dich_nguoc:
            self.after_cancel(self.id_after_dich_nguoc)
            self.id_after_dich_nguoc = None

        van_ban = self.entry_van_ban.get().strip()
        if not van_ban:
            self.lbl_hien_thi_ki_hieu.configure(image=None, text="Vui lòng gõ chữ trước khi bấm!")
            return

        if self.main_app.logic_thuc_hanh:
            # Gọi thuật toán phân tích chuỗi từ file logic vừa viết
            danh_sach_anh = self.main_app.logic_thuc_hanh.phan_tich_van_ban_thanh_anh(van_ban)

            if danh_sach_anh:
                self.index_anh_hien_tai = 0
                self.danh_sach_anh_cho_chieu = danh_sach_anh
                # Khóa nút bấm tạm thời để người dùng xem trọn vẹn chuỗi ký hiệu
                self.btn_chuyen_doi.configure(state="disabled", text="⏳ Đang chiếu...")
                self.chieu_anh_ki_hieu_tu_dong()
            else:
                self.lbl_hien_thi_ki_hieu.configure(image=None, text="Không tìm thấy dữ liệu ký hiệu!")

    def chieu_anh_ki_hieu_tu_dong(self):
        """Hàm đệ quy thông minh sử dụng self.after để không gây đóng băng Giao diện (UI Freezing)"""
        if self.index_anh_hien_tai < len(self.danh_sach_anh_cho_chieu):
            ten_file, nhan_chu = self.danh_sach_anh_cho_chieu[self.index_anh_hien_tai]
            duong_dan_anh = os.path.join(os.getcwd(), "assets", "pic", ten_file) if ten_file else ""

            if duong_dan_anh and os.path.exists(duong_dan_anh):
                try:
                    img_pil = Image.open(duong_dan_anh)
                    # Điều chỉnh kích cỡ ảnh (140x140) cho vừa vặn hộp chứa bên phải
                    ctk_img = ctk.CTkImage(light_image=img_pil, size=(140, 140))
                    self.lbl_hien_thi_ki_hieu.configure(image=ctk_img, text=f"Ký tự hiện tại: {nhan_chu}", compound="bottom")
                    self.lbl_hien_thi_ki_hieu.image = ctk_img  # Ép Python giữ bộ nhớ ảnh tránh lỗi rác (garbage collection)
                except Exception as e:
                    print(f"[LỖI TẢI ẢNH]: {e}")
            else:
                # Nếu từ/chữ cái đó bị thiếu ảnh trong thư mục, hiển thị chữ thô để người dùng học tạm
                self.lbl_hien_thi_ki_hieu.configure(image=None, text=f"Ký hiệu: {nhan_chu}\n(Chưa cập nhật ảnh)")

            self.index_anh_hien_tai += 1
            # Cài đặt tốc độ lật ảnh: 1200ms (1.2 giây) chuyển một ảnh ký hiệu. Bạn có thể tăng giảm tùy ý.
            self.id_after_dich_nguoc = self.after(2000, self.chieu_anh_ki_hieu_tu_dong)
        else:
            # Đã trình chiếu xong toàn bộ câu
            self.lbl_hien_thi_ki_hieu.configure(image=None, text="✨ Hoàn thành chuỗi ký hiệu!")
            self.btn_chuyen_doi.configure(state="normal", text="Trình Chiếu Ký Hiệu 👉")
            self.id_after_dich_nguoc = None