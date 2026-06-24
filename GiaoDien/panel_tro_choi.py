import customtkinter as ctk


class PanelTroChoi(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="transparent")
        self.main_app = main_app
        self.tao_giao_dien()

    def tao_giao_dien(self):
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # --- CỘT TRÁI (CAMERA) ---
        khung_trai = ctk.CTkFrame(self, fg_color="transparent")
        khung_trai.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        khung_trai.grid_columnconfigure(0, weight=1)
        khung_trai.grid_rowconfigure(0, weight=1)

        khung_cam = ctk.CTkFrame(khung_trai, fg_color=self.main_app.mau_card, corner_radius=20, border_width=2,
                                 border_color="#1E1E1E")
        khung_cam.grid(row=0, column=0, sticky="nsew")

        khung_dieu_khien = ctk.CTkFrame(khung_cam, fg_color="transparent")
        khung_dieu_khien.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(khung_dieu_khien, text="▶ BẬT CAM", font=self.main_app.font_chu_dam,
                      fg_color=self.main_app.mau_chu_dao, hover_color=self.main_app.mau_hover, corner_radius=10,
                      command=self.main_app.bat_camera, width=100).pack(side="left", padx=5)
        ctk.CTkButton(khung_dieu_khien, text="⏹ TẮT", font=self.main_app.font_chu_dam, fg_color="#555555",
                      hover_color="#333333", corner_radius=10, command=self.main_app.tat_camera, width=80).pack(
            side="left", padx=5)

        khung_man_hinh = ctk.CTkFrame(khung_cam, fg_color="#000000", width=640, height=480, corner_radius=15)
        khung_man_hinh.pack(pady=10, expand=True)
        khung_man_hinh.grid_propagate(False)

        self.lbl_camera = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH CHỜ ]", text_color="#555555",
                                       font=("Segoe UI Black", 20))
        self.lbl_camera.place(relx=0.5, rely=0.5, anchor="center")

        # --- CỘT PHẢI (GAME BẢNG ĐIỀU KHIỂN) ---
        self.khung_phai = ctk.CTkFrame(self, fg_color=self.main_app.mau_card, corner_radius=20, border_width=2,
                                       border_color="#1E1E1E")
        self.khung_phai.grid(row=0, column=1, sticky="nsew")

        khung_header = ctk.CTkFrame(self.khung_phai, fg_color="transparent")
        khung_header.pack(fill="x", padx=15, pady=20)

        khung_diem = ctk.CTkFrame(khung_header, fg_color="#2A2A40", corner_radius=10)
        khung_diem.pack(side="left", padx=5)
        self.lbl_diem = ctk.CTkLabel(khung_diem, text="⭐ 0", font=("Segoe UI Black", 20), text_color="#FFF")
        self.lbl_diem.pack(padx=15, pady=8)

        khung_lv = ctk.CTkFrame(khung_header, fg_color="#162A20", corner_radius=10)
        khung_lv.pack(side="left", padx=5)
        self.lbl_cap_do = ctk.CTkLabel(khung_lv, text="LV 1", font=("Segoe UI Black", 20), text_color="#00FFCC")
        self.lbl_cap_do.pack(padx=15, pady=8)

        self.lbl_combo = ctk.CTkLabel(khung_header, text="", font=("Segoe UI Black", 22, "italic"),
                                      text_color="#FFCC00")
        self.lbl_combo.pack(side="right", padx=10)

        self.khung_target = ctk.CTkFrame(self.khung_phai, fg_color="#1A1A1A", corner_radius=25, border_width=3,
                                         border_color="#333", width=280, height=220)
        self.khung_target.pack(pady=20)
        self.khung_target.pack_propagate(False)

        self.lbl_cau_hoi = ctk.CTkLabel(self.khung_target, text="SẴN SÀNG", font=("Segoe UI Black", 45, "bold"),
                                        text_color="#FFCC00")
        self.lbl_cau_hoi.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_tim = ctk.CTkLabel(self.khung_phai, text="❤️ ❤️ ❤️ ❤️ ❤️", font=("Segoe UI", 38), text_color="#E50914")
        self.lbl_tim.pack(pady=10)

        khung_thoi_gian = ctk.CTkFrame(self.khung_phai, fg_color="transparent")
        khung_thoi_gian.pack(fill="x", padx=30, pady=10)

        self.lbl_text_thoi_gian = ctk.CTkLabel(khung_thoi_gian, text="⏱️ 0.0s", font=("Segoe UI Black", 16),
                                               text_color="#FFF")
        self.lbl_text_thoi_gian.pack(side="top", anchor="w", pady=(0, 5))

        self.thanh_thoi_gian = ctk.CTkProgressBar(khung_thoi_gian, height=20,
                                                  progress_color=self.main_app.mau_thanh_cong, fg_color="#333",
                                                  corner_radius=10)
        self.thanh_thoi_gian.set(1.0)
        self.thanh_thoi_gian.pack(side="bottom", fill="x")

        self.lbl_tin_nhan = ctk.CTkLabel(self.khung_phai, text="Nhấn BẮT ĐẦU để thi tài!",
                                         font=("Segoe UI", 18, "bold"), wraplength=300, text_color="#A0A0A0")
        self.lbl_tin_nhan.pack(pady=15)

        khung_nut = ctk.CTkFrame(self.khung_phai, fg_color="transparent")
        khung_nut.pack(fill="x", side="bottom", padx=25, pady=30)

        self.btn_toggle = ctk.CTkButton(khung_nut, text="🚀 BẮT ĐẦU CHƠI", font=("Segoe UI Black", 22), height=65,
                                        corner_radius=15, fg_color=self.main_app.mau_chu_dao,
                                        hover_color=self.main_app.mau_hover, command=self.toggle_game)
        self.btn_toggle.pack(fill="x")

    def cap_nhat_khung_hinh(self, img, chu, tin_cay, nguon):
        self.lbl_camera.configure(image=img, text="")
        logic = self.main_app.logic_game
        if logic and logic.dang_choi:
            trang_thai, cau_hoi, tim, diem, tg_con, combo, cap_do = logic.kiem_tra_lien_tuc(chu, tin_cay)

            if len(logic.chuoi_muc_tieu) >= 4:
                font_size = 40
            elif len(logic.chuoi_muc_tieu) == 3:
                font_size = 50
            else:
                font_size = 65

            self.lbl_cau_hoi.configure(text=cau_hoi, font=("Segoe UI Black", font_size, "bold"))
            self.lbl_diem.configure(text=f"⭐ {diem}")
            self.lbl_tim.configure(text="❤️ " * tim if tim > 0 else "💀")
            self.lbl_cap_do.configure(text=f"LV {cap_do}")
            self.lbl_text_thoi_gian.configure(text=f"⏱️ {tg_con:.1f}s")

            if combo >= 3:
                self.lbl_combo.configure(text=f"🔥 x{combo}", text_color=self.main_app.mau_chu_dao)
            elif combo > 0:
                self.lbl_combo.configure(text=f"⚡ x{combo}", text_color="#FFCC00")
            else:
                self.lbl_combo.configure(text="")

            if logic.thoi_gian_gioi_han > 0:
                phan_tram = tg_con / logic.thoi_gian_gioi_han
                self.thanh_thoi_gian.set(phan_tram)
                if phan_tram > 0.5:
                    self.thanh_thoi_gian.configure(progress_color=self.main_app.mau_thanh_cong)
                elif phan_tram > 0.25:
                    self.thanh_thoi_gian.configure(progress_color="#F39C12")
                else:
                    self.thanh_thoi_gian.configure(progress_color=self.main_app.mau_chu_dao)

            if trang_thai == "DUNG":
                self.hieu_ung_chop_mau(self.khung_target, "#00FFCC", "#333", 3, is_border=True)
                self.lbl_tin_nhan.configure(text="✨ PERFECT COMBO!", text_color=self.main_app.mau_thanh_cong)
                diem_cong = 10 * len(logic.chuoi_muc_tieu) * combo
                self.hieu_ung_bay_len(f"+{diem_cong}", self.main_app.mau_thanh_cong, 0.5, 0.4)
                if logic.so_cau_dung > 0 and logic.so_cau_dung % 5 == 0:
                    self.hieu_ung_bay_len("🚀 LEVEL UP!", "#00FFCC", 0.5, 0.55)

            elif trang_thai == "DANG_CHUOI":
                self.hieu_ung_chop_mau(self.khung_target, "#FFCC00", "#333", 2, is_border=True)
                self.lbl_tin_nhan.configure(text="Đã ghi nhận, tiếp tục...", text_color="#FFCC00")

            elif trang_thai == "HET_GIO":
                self.hieu_ung_chop_mau(self.khung_target, self.main_app.mau_chu_dao, "#333", 3, is_border=True)
                self.lbl_tin_nhan.configure(text="⏱️ Quá chậm! Đứt chuỗi (-1 ❤️)", text_color=self.main_app.mau_chu_dao)
                self.hieu_ung_bay_len("-1 ❤️", self.main_app.mau_chu_dao, 0.5, 0.6)

            elif trang_thai == "SAI_HET_TIM":
                self.lbl_tim.configure(text="💀")
                self.hieu_ung_bay_len("-1 ❤️", self.main_app.mau_chu_dao, 0.5, 0.6)
                self.lbl_text_thoi_gian.configure(text="⏱️ 0.0s")
                self.thanh_thoi_gian.set(0)

                if hasattr(self.main_app, 'logic_ho_so') and self.main_app.logic_ho_so:
                    self.main_app.logic_ho_so.cap_nhat_sau_khi_choi(diem)

                self.lbl_tin_nhan.configure(text=f"💀 GAME OVER! Bạn ghi được {diem} điểm.",
                                            text_color=self.main_app.mau_chu_dao)
                self.btn_toggle.configure(text="🔄 CHƠI LẠI", fg_color=self.main_app.mau_chu_dao,
                                          hover_color=self.main_app.mau_hover)

    def hieu_ung_bay_len(self, text, color, x_rel, y_rel_start):
        try:
            lbl_float = ctk.CTkLabel(self.khung_phai, text=text, font=("Segoe UI Black", 40, "bold"), text_color=color)
            lbl_float.place(relx=x_rel, rely=y_rel_start, anchor="center")

            def move_up(widget, current_y, steps):
                if steps > 0 and widget.winfo_exists():
                    widget.place(relx=x_rel, rely=current_y, anchor="center")
                    self.after(30, lambda: move_up(widget, current_y - 0.015, steps - 1))
                elif widget.winfo_exists():
                    widget.destroy()

            move_up(lbl_float, y_rel_start, 25)
        except:
            pass

    def hieu_ung_chop_mau(self, widget, mau_sang, mau_goc, so_lan=4, is_border=False):
        if so_lan > 0:
            if is_border:
                widget.configure(border_color=mau_sang if so_lan % 2 == 0 else mau_goc)
            else:
                widget.configure(text_color=mau_sang if so_lan % 2 == 0 else mau_goc)
            self.after(100, lambda: self.hieu_ung_chop_mau(widget, mau_sang, mau_goc, so_lan - 1, is_border))
        else:
            if is_border:
                widget.configure(border_color=mau_goc)
            else:
                widget.configure(text_color=mau_goc)

    def toggle_game(self):
        if not self.main_app.camera_running:
            self.lbl_tin_nhan.configure(text="⚠️ BẬT CAMERA TRƯỚC KHI CHƠI!", text_color="#FFCC00")
            return

        logic = self.main_app.logic_game
        if logic:
            if logic.dang_choi:
                logic.dang_choi = False
                if self.main_app.logic_ho_so: self.main_app.logic_ho_so.cap_nhat_sau_khi_choi(logic.diem_so)
                self.btn_toggle.configure(text="🔄 CHƠI LẠI", fg_color=self.main_app.mau_chu_dao,
                                          hover_color=self.main_app.mau_hover)
                self.lbl_tin_nhan.configure(text=f"Đã dừng! Ghi nhận: {logic.diem_so} điểm.", text_color="#FFF")
            else:
                cau_hoi = logic.bat_dau_game()
                self.lbl_cau_hoi.configure(text=f"{cau_hoi}", font=("Segoe UI Black", 65, "bold"), text_color="#FFF")
                self.lbl_diem.configure(text="⭐ 0")
                self.lbl_combo.configure(text="", text_color="#FFCC00")
                self.lbl_cap_do.configure(text="LV 1")
                self.lbl_tim.configure(text="❤️ ❤️ ❤️ ❤️ ❤️")
                self.lbl_text_thoi_gian.configure(text="⏱️ Sẵn sàng")
                self.thanh_thoi_gian.set(1.0)
                self.lbl_tin_nhan.configure(text="Múa tay chuẩn xác để duy trì Sinh Tồn!",
                                            text_color=self.main_app.mau_thanh_cong)
                self.khung_target.configure(border_color="#333")
                self.btn_toggle.configure(text="⏹ DỪNG CHƠI", fg_color="#555555", hover_color="#333333")

    def reset_giao_dien(self):
        # Hàm này được gọi từ gui_main khi bấm "Tắt"
        self.lbl_camera.configure(image="", text="[ MÀN HÌNH CHỜ ]")