import customtkinter as ctk

class PanelHoSo(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="transparent")
        self.main_app = main_app
        self.tao_giao_dien()

    def tao_giao_dien(self):
        ctk.CTkLabel(self, text="TRUNG TÂM HỒ SƠ & THÀNH TÍCH", font=("Segoe UI Black", 28, "bold"), text_color="#00FFCC").pack(pady=(10, 20))
        khung_chia_cot = ctk.CTkFrame(self, fg_color="transparent")
        khung_chia_cot.pack(fill="both", expand=True, padx=20)
        khung_chia_cot.grid_columnconfigure(0, weight=4)
        khung_chia_cot.grid_columnconfigure(1, weight=6)

        # Cột Trái
        self.khung_trai_wrapper = ctk.CTkFrame(khung_chia_cot, fg_color="transparent")
        self.khung_trai_wrapper.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        khung_trai_hs = ctk.CTkFrame(self.khung_trai_wrapper, fg_color="#1A1A2E", corner_radius=20, border_width=2, border_color="#16213E")
        khung_trai_hs.pack(fill="x", pady=(0, 15))

        khung_ava = ctk.CTkFrame(khung_trai_hs, fg_color="transparent", corner_radius=50, width=100, height=100)
        khung_ava.pack(pady=(25, 10))
        khung_ava.pack_propagate(False)
        self.btn_hs_avatar = ctk.CTkButton(khung_ava, text="🧑‍🚀", font=("Segoe UI", 55), fg_color="transparent", hover_color="#16213E", command=self.xu_ly_doi_avatar)
        self.btn_hs_avatar.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_hs_ten = ctk.CTkLabel(khung_trai_hs, text="Tên: ...", font=("Segoe UI Black", 24, "bold"), text_color="#E94560")
        self.lbl_hs_ten.pack(pady=(0, 5))
        self.btn_doi_ten = ctk.CTkButton(khung_trai_hs, text="✏️ CHỈNH SỬA", font=self.main_app.font_chu_dam, fg_color="#E94560", hover_color="#C81D4E", corner_radius=20, height=35, command=self.xu_ly_doi_ten)
        ctk.CTkFrame(khung_trai_hs, height=2, fg_color="#333").pack(fill="x", padx=40, pady=15)

        self.lbl_hs_khen_thuong = ctk.CTkLabel(khung_trai_hs, text="🏆 Kỷ Lục: 0 điểm", font=("Segoe UI", 20, "bold"), text_color="#FFD700")
        self.lbl_hs_khen_thuong.pack(pady=5)
        self.lbl_hs_so_lan = ctk.CTkLabel(khung_trai_hs, text="🎮 Đã chơi: 0 trận", font=("Segoe UI", 16), text_color="#A0A0A0")
        self.lbl_hs_so_lan.pack(pady=5)
        ctk.CTkFrame(khung_trai_hs, height=2, fg_color="#333").pack(fill="x", padx=40, pady=15)

        ctk.CTkLabel(khung_trai_hs, text="📊 TIẾN ĐỘ HỌC TẬP", font=("Segoe UI", 16, "bold"), text_color="#00FFCC").pack(pady=(0, 5))
        self.lbl_tien_do = ctk.CTkLabel(khung_trai_hs, text="Đã học: 0 / 0 bài", font=self.main_app.font_chu)
        self.lbl_tien_do.pack()
        self.thanh_tien_do = ctk.CTkProgressBar(khung_trai_hs, width=220, height=12, progress_color="#00E676", fg_color="#333", corner_radius=10)
        self.thanh_tien_do.set(0)
        self.thanh_tien_do.pack(pady=(5, 15))

        self.btn_dang_xuat = ctk.CTkButton(khung_trai_hs, text="Đăng Xuất", font=self.main_app.font_chu_dam, fg_color="#555", hover_color="#333", corner_radius=10, command=self.xu_ly_dang_xuat)
        self.btn_dang_xuat.pack(pady=(0, 20))

        khung_thong_ke = ctk.CTkFrame(self.khung_trai_wrapper, fg_color="transparent")
        khung_thong_ke.pack(fill="x")
        khung_thong_ke.grid_columnconfigure(0, weight=1); khung_thong_ke.grid_columnconfigure(1, weight=1)

        self.khung_loi_sai_bg = ctk.CTkFrame(khung_thong_ke, fg_color="#2A1616", corner_radius=15, border_width=1, border_color="#3A1A1A")
        self.khung_loi_sai_bg.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(self.khung_loi_sai_bg, text="⚠️ HAY SAI", font=("Segoe UI Black", 14), text_color="#FF4C4C").pack(pady=(15, 5))
        self.khung_chu_sai = ctk.CTkFrame(self.khung_loi_sai_bg, fg_color="transparent")
        self.khung_chu_sai.pack(pady=(0, 15))

        self.khung_thoi_gian_bg = ctk.CTkFrame(khung_thong_ke, fg_color="#162A20", corner_radius=15, border_width=1, border_color="#1A3A25")
        self.khung_thoi_gian_bg.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(self.khung_thoi_gian_bg, text="⏱️ TỔNG GIỜ", font=("Segoe UI Black", 14), text_color="#00E676").pack(pady=(15, 5))
        self.lbl_hs_thoi_gian = ctk.CTkLabel(self.khung_thoi_gian_bg, text="0h 0p", font=("Segoe UI Black", 20), text_color="#FFF")
        self.lbl_hs_thoi_gian.pack(pady=(0, 15))

        # Cột Phải
        self.khung_phai_hs = ctk.CTkFrame(khung_chia_cot, fg_color="#1A1A2E", corner_radius=20, border_width=2, border_color="#16213E")
        self.khung_phai_hs.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

        self.lbl_tieu_de_phai = ctk.CTkLabel(self.khung_phai_hs, text="ĐANG TẢI...", font=("Segoe UI Black", 20, "bold"))
        self.lbl_tieu_de_phai.pack(pady=(30, 20))

        self.khung_dang_nhap = ctk.CTkTabview(self.khung_phai_hs, width=450, corner_radius=15, fg_color=self.main_app.mau_card, segmented_button_selected_color=self.main_app.mau_chu_dao, segmented_button_selected_hover_color=self.main_app.mau_hover)
        self.khung_dang_nhap.add("🔑 ĐĂNG NHẬP")
        self.khung_dang_nhap.add("📝 TẠO TÀI KHOẢN MỚI")

        self.txt_user_login = ctk.CTkEntry(self.khung_dang_nhap.tab("🔑 ĐĂNG NHẬP"), placeholder_text="Tên đăng nhập", width=300, height=45, font=self.main_app.font_chu, corner_radius=10)
        self.txt_user_login.pack(pady=(30, 10))
        self.txt_pass_login = ctk.CTkEntry(self.khung_dang_nhap.tab("🔑 ĐĂNG NHẬP"), placeholder_text="Mật khẩu", show="*", width=300, height=45, font=self.main_app.font_chu, corner_radius=10)
        self.txt_pass_login.pack(pady=10)
        self.lbl_loi_login = ctk.CTkLabel(self.khung_dang_nhap.tab("🔑 ĐĂNG NHẬP"), text="", text_color="#e74c3c", font=self.main_app.font_chu)
        self.lbl_loi_login.pack(pady=5)
        ctk.CTkButton(self.khung_dang_nhap.tab("🔑 ĐĂNG NHẬP"), text="🔓 BẮT ĐẦU", font=("Segoe UI Black", 16), height=45, corner_radius=10, fg_color=self.main_app.mau_chu_dao, hover_color=self.main_app.mau_hover, command=self.xu_ly_dang_nhap, width=300).pack(pady=(10, 20))

        self.txt_user_reg = ctk.CTkEntry(self.khung_dang_nhap.tab("📝 TẠO TÀI KHOẢN MỚI"), placeholder_text="Nhập tên đăng nhập", width=300, height=45, font=self.main_app.font_chu, corner_radius=10)
        self.txt_user_reg.pack(pady=(15, 10))
        self.txt_pass_reg = ctk.CTkEntry(self.khung_dang_nhap.tab("📝 TẠO TÀI KHOẢN MỚI"), placeholder_text="Tạo mật khẩu", show="*", width=300, height=45, font=self.main_app.font_chu, corner_radius=10)
        self.txt_pass_reg.pack(pady=10)
        self.txt_ten_reg = ctk.CTkEntry(self.khung_dang_nhap.tab("📝 TẠO TÀI KHOẢN MỚI"), placeholder_text="Tên hiển thị", width=300, height=45, font=self.main_app.font_chu, corner_radius=10)
        self.txt_ten_reg.pack(pady=10)
        self.lbl_loi_reg = ctk.CTkLabel(self.khung_dang_nhap.tab("📝 TẠO TÀI KHOẢN MỚI"), text="", text_color="#e74c3c", font=self.main_app.font_chu)
        self.lbl_loi_reg.pack(pady=5)
        ctk.CTkButton(self.khung_dang_nhap.tab("📝 TẠO TÀI KHOẢN MỚI"), text="🚀 GHI DANH", font=("Segoe UI Black", 16), height=45, corner_radius=10, fg_color="#27ae60", hover_color="#2ecc71", command=self.xu_ly_dang_ky, width=300).pack(pady=(10, 20))

        self.khung_danh_sach_top = ctk.CTkScrollableFrame(self.khung_phai_hs, fg_color="transparent", corner_radius=15)

    def cap_nhat_giao_dien(self):
        logic = self.main_app.logic_ho_so
        if not logic: return

        du_lieu = logic.lay_thong_tin()
        self.lbl_hs_ten.configure(text=f"{du_lieu['ten_hien_thi']}")
        self.lbl_hs_khen_thuong.configure(text=f"🏆 Kỷ Lục: {du_lieu['diem_cao_nhat']} điểm")
        self.lbl_hs_so_lan.configure(text=f"🎮 Đã chơi: {du_lieu['so_lan_choi_game']} trận")
        self.btn_hs_avatar.configure(text=du_lieu.get('avatar', '🧑‍🚀'))

        tong_phut = float(du_lieu.get('thoi_gian_hoc', 0.0))
        self.lbl_hs_thoi_gian.configure(text=f"{int(tong_phut // 60)}h {int(tong_phut % 60)}p {int((tong_phut * 60) % 60)}s")

        try:
            tong_so_bai = len(self.main_app.logic_hoc.danh_sach_bai_hoc) if self.main_app.logic_hoc else 0
            da_hoc = len(logic.lay_danh_sach_da_hoc())
            self.lbl_tien_do.configure(text=f"Đã học: {da_hoc} / {tong_so_bai} bài")
            self.thanh_tien_do.set(da_hoc / tong_so_bai if tong_so_bai > 0 else 0)

            for w in self.khung_chu_sai.winfo_children(): w.destroy()
            top_3 = logic.lay_top_loi_sai(3)
            if not top_3: ctk.CTkLabel(self.khung_chu_sai, text="Chưa có", text_color="#A0A0A0").pack()
            else:
                for chu in top_3:
                    ctk.CTkLabel(self.khung_chu_sai, text=chu, font=("Segoe UI Black", 14), text_color="#FFF", fg_color="#C0392B", corner_radius=5, width=40, height=25).pack(side="left", padx=3)
        except Exception: pass

        is_guest = (logic.id_tai_khoan_hien_tai == getattr(logic, 'id_guest', None))

        if is_guest:
            self.btn_doi_ten.pack_forget(); self.btn_hs_avatar.configure(state="disabled")
            self.khung_danh_sach_top.pack_forget(); self.btn_dang_xuat.pack_forget()
            self.lbl_tieu_de_phai.configure(text="🔒 ĐĂNG NHẬP ĐỂ ĐUA TOP", text_color="#e67e22")
            self.khung_dang_nhap.pack(fill="both", expand=True, padx=40, pady=(0, 30))
        else:
            self.btn_doi_ten.pack(pady=10); self.btn_hs_avatar.configure(state="normal")
            self.khung_dang_nhap.pack_forget(); self.btn_dang_xuat.pack(side="bottom", pady=20)
            self.lbl_tieu_de_phai.configure(text="🌟 BẢNG VÀNG THÀNH TÍCH", text_color="#2ecc71")
            self.khung_danh_sach_top.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            for w in self.khung_danh_sach_top.winfo_children(): w.destroy()
            try:
                top_players = logic.lay_bang_xep_hang(5)
                if not top_players: ctk.CTkLabel(self.khung_danh_sach_top, text="Chưa có ai ghi điểm!", text_color="#888").pack(pady=20)
                else:
                    huy_hieu = ["🥇", "🥈", "🥉", "🏅", "🏅"]
                    for i, player in enumerate(top_players):
                        ten = player.get("ten_hien_thi", "") if isinstance(player, dict) else player[0]
                        diem = player.get("diem_cao_nhat", 0) if isinstance(player, dict) else player[1]
                        mau = "#FFD700" if i == 0 else "#C0C0C0" if i == 1 else "#CD7F32" if i == 2 else "#FFFFFF"
                        icon = huy_hieu[i] if i < len(huy_hieu) else "⭐"
                        thanh = ctk.CTkFrame(self.khung_danh_sach_top, fg_color="#2A2A40", corner_radius=10)
                        thanh.pack(fill="x", pady=6)
                        ctk.CTkLabel(thanh, text=f"{icon} {ten}", font=self.main_app.font_chu_dam).pack(side="left", padx=20, pady=15)
                        ctk.CTkLabel(thanh, text=f"{diem} điểm", font=self.main_app.font_chu_dam, text_color="#FFCC00").pack(side="right", padx=20, pady=15)
            except Exception: pass

    def xu_ly_doi_ten(self):
        dialog = ctk.CTkInputDialog(text="Nhập tên hiển thị mới:", title="Đổi Tên Hiển Thị")
        ten_moi = dialog.get_input()
        if ten_moi and self.main_app.logic_ho_so:
            if self.main_app.logic_ho_so.cap_nhat_ten_hien_thi(ten_moi)[0]: self.cap_nhat_giao_dien()

    def xu_ly_dang_nhap(self):
        if not self.main_app.logic_ho_so: return
        ok, msg = self.main_app.logic_ho_so.dang_nhap(self.txt_user_login.get(), self.txt_pass_login.get())
        if ok:
            self.lbl_loi_login.configure(text="")
            self.txt_user_login.delete(0, 'end'); self.txt_pass_login.delete(0, 'end')
            self.cap_nhat_giao_dien()
            self.main_app.panel_hoc_tap.cap_nhat_ui_danh_sach_bai_hoc()
        else: self.lbl_loi_login.configure(text=msg)

    def xu_ly_dang_ky(self):
        if not self.main_app.logic_ho_so: return
        ok, msg = self.main_app.logic_ho_so.dang_ky(self.txt_user_reg.get(), self.txt_pass_reg.get(), self.txt_ten_reg.get())
        if ok:
            self.lbl_loi_reg.configure(text="")
            self.txt_user_reg.delete(0, 'end'); self.txt_pass_reg.delete(0, 'end'); self.txt_ten_reg.delete(0, 'end')
            self.cap_nhat_giao_dien()
            self.main_app.panel_hoc_tap.cap_nhat_ui_danh_sach_bai_hoc()
        else: self.lbl_loi_reg.configure(text=msg)

    def xu_ly_dang_xuat(self):
        if self.main_app.logic_ho_so:
            self.main_app.logic_ho_so.dang_xuat()
            self.cap_nhat_giao_dien()
            self.main_app.panel_hoc_tap.cap_nhat_ui_danh_sach_bai_hoc()

    def xu_ly_doi_avatar(self):
        top = ctk.CTkToplevel(self)
        top.title("Đổi Avatar"); top.geometry("380x300"); top.transient(self); top.grab_set()
        ctk.CTkLabel(top, text="✨ CHỌN AVATAR MỚI", font=("Segoe UI Black", 18), text_color="#00FFCC").pack(pady=(20, 10))
        khung_icons = ctk.CTkFrame(top, fg_color="transparent"); khung_icons.pack(pady=10)
        danh_sach = ["🧑‍🚀", "👨‍💻", "👩‍🏫", "🕵️‍♂️", "🦸‍♀️", "🧙‍♂️", "🤖", "👽", "👻", "🦊", "🐯", "🐼"]
        for i, ava in enumerate(danh_sach):
            ctk.CTkButton(khung_icons, text=ava, font=("Segoe UI", 35), width=60, height=60, fg_color="transparent", hover_color="#2C2C2C",
                          command=lambda a=ava: self.luu_avatar_moi(a, top)).grid(row=i//4, column=i%4, padx=5, pady=5)

    def luu_avatar_moi(self, avatar_chon, cua_so_top):
        if self.main_app.logic_ho_so:
            self.main_app.logic_ho_so.cap_nhat_avatar(avatar_chon)
            self.cap_nhat_giao_dien()
        cua_so_top.destroy()