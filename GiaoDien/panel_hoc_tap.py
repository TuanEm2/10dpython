import os
import random
import time
import customtkinter as ctk
from PIL import Image


class PanelHocTap(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="transparent")
        self.main_app = main_app
        self.bai_da_hoc = set()
        self.bai_hien_tai = None
        self.nut_bai_hoc_dict = {}
        self.dang_kiem_tra = False

        # Khai báo sẵn 2 "kho chứa" giữ ảnh để Python không dọn rác
        self.anh_mau_hien_tai = None
        self.anh_fc_hien_tai = None

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

        self.lbl_ket_qua = ctk.CTkLabel(khung_dieu_khien, text="Chưa bật camera", font=("Segoe UI", 16, "bold"),
                                        text_color="#FFCC00")
        self.lbl_ket_qua.pack(side="right", padx=10)

        khung_man_hinh = ctk.CTkFrame(khung_cam, fg_color="#000000", width=640, height=480)
        khung_man_hinh.pack(pady=10, expand=True)
        khung_man_hinh.grid_propagate(False)
        self.lbl_camera = ctk.CTkLabel(khung_man_hinh, text="[ MÀN HÌNH ]", text_color="#555555")
        self.lbl_camera.place(relx=0.5, rely=0.5, anchor="center")

        self.khung_duoi = ctk.CTkFrame(khung_trai, fg_color=self.main_app.mau_card, corner_radius=15)
        self.khung_duoi.grid(row=1, column=0, sticky="nsew")

        self.lbl_tieu_de_hd = ctk.CTkLabel(self.khung_duoi, text="📝 Hướng dẫn thực hiện:",
                                           font=self.main_app.font_tieu_de)
        self.lbl_tieu_de_hd.pack(anchor="w", padx=20, pady=(15, 5))
        self.lbl_mo_ta = ctk.CTkLabel(self.khung_duoi, text="(Vui lòng chọn bài học ở danh sách bên phải)",
                                      font=self.main_app.font_chu, text_color="#A0A0A0", wraplength=500, justify="left")
        self.lbl_mo_ta.pack(anchor="w", padx=20, pady=5)

        self.khung_nut_duoi = ctk.CTkFrame(self.khung_duoi, fg_color="transparent")
        self.khung_nut_duoi.pack(fill="x", side="bottom", pady=15, padx=20)
        ctk.CTkButton(self.khung_nut_duoi, text="🎯 Kiểm tra tiến độ", fg_color="#8e44ad", hover_color="#9b59b6",
                      font=self.main_app.font_chu_dam, command=self.mo_kiem_tra).pack(side="right", padx=10)

        khung_phai = ctk.CTkFrame(self, fg_color=self.main_app.mau_card, corner_radius=15)
        khung_phai.grid(row=0, column=1, sticky="nsew")

        khung_anh = ctk.CTkFrame(khung_phai, fg_color=self.main_app.mau_sidebar, corner_radius=10)
        khung_anh.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(khung_anh, text="🖼 ẢNH MẪU", font=self.main_app.font_tieu_de).pack(pady=(15, 5))
        self.lbl_anh_mau = ctk.CTkLabel(khung_anh, text="[Chưa có ảnh]", width=150, height=150, fg_color="#1E1E1E",
                                        corner_radius=10)
        self.lbl_anh_mau.pack(pady=10)
        self.lbl_tieu_de_phai = ctk.CTkLabel(khung_anh, text="Chưa chọn bài", font=self.main_app.font_chu_dam)
        self.lbl_tieu_de_phai.pack(pady=(5, 15))

        self.khung_ds_con = ctk.CTkScrollableFrame(khung_phai, fg_color="transparent")
        self.khung_ds_con.pack(fill="both", expand=True, padx=10, pady=(0, 20))
        self.tao_danh_sach_bai_hoc()

    def tao_danh_sach_bai_hoc(self):
        if self.main_app.logic_ho_so: self.bai_da_hoc = set(self.main_app.logic_ho_so.lay_danh_sach_da_hoc())
        if self.main_app.logic_hoc and self.main_app.logic_hoc.danh_sach_bai_hoc:
            for bai in self.main_app.logic_hoc.danh_sach_bai_hoc:
                is_done = bai in self.bai_da_hoc
                btn = ctk.CTkButton(self.khung_ds_con, text=f"✅ {bai}" if is_done else bai, font=self.main_app.font_chu,
                                    fg_color="#00E676" if is_done else "#3A3B3C",
                                    text_color="#000000" if is_done else "white",
                                    hover_color=self.main_app.mau_chu_dao, command=lambda b=bai: self.chon_bai_hoc(b))
                btn.pack(pady=5, fill="x")
                self.nut_bai_hoc_dict[bai] = btn

    def cap_nhat_ui_danh_sach_bai_hoc(self):
        if not self.main_app.logic_ho_so: return
        self.bai_da_hoc = set(self.main_app.logic_ho_so.lay_danh_sach_da_hoc())
        for bai, btn in self.nut_bai_hoc_dict.items():
            is_done = bai in self.bai_da_hoc
            btn.configure(fg_color="#00E676" if is_done else "#3A3B3C", text_color="#000000" if is_done else "white",
                          text=f"✅ {bai}" if is_done else bai)

    def chon_bai_hoc(self, ten_bai):
        if not self.main_app.logic_hoc: return
        self.bai_hien_tai = ten_bai
        muc_tieu, duong_dan_anh = self.main_app.logic_hoc.thiet_lap_bai_hoc(ten_bai)
        self.lbl_tieu_de_phai.configure(text=f"Đang học: Chữ {muc_tieu}")
        self.lbl_ket_qua.configure(text=f"Đang chờ chữ: {muc_tieu}", text_color="#FFCC00")

        # ========================================================
        # THỦ THUẬT: DÙNG ẢNH TRONG SUỐT THAY VÌ 'None' ĐỂ LỪA TKINTER
        anh_rong = ctk.CTkImage(light_image=Image.new("RGBA", (180, 180), (0, 0, 0, 0)), size=(180, 180))
        self.lbl_anh_mau.configure(image=anh_rong)
        self.anh_mau_hien_tai = anh_rong  # Trói vào bộ nhớ
        # ========================================================

        if os.path.exists(duong_dan_anh):
            self.anh_mau_hien_tai = ctk.CTkImage(light_image=Image.open(duong_dan_anh),
                                                 dark_image=Image.open(duong_dan_anh),
                                                 size=(180, 180))
            self.lbl_anh_mau.configure(image=self.anh_mau_hien_tai, text="")
        else:
            self.lbl_anh_mau.configure(image=anh_rong, text="[Thiếu ảnh]")

        if hasattr(self.main_app.logic_hoc, 'lay_mo_ta_huong_dan'):
            self.lbl_mo_ta.configure(text=self.main_app.logic_hoc.lay_mo_ta_huong_dan(muc_tieu))

    def cap_nhat_khung_hinh(self, img, chu, tin_cay):
        self.lbl_camera.configure(image=img, text="")
        self.lbl_camera.image = img
        logic = self.main_app.logic_hoc
        if self.dang_kiem_tra:
            if getattr(self, 'loai_cau_hoi', 0) == 1 and getattr(self, 'muc_tieu_quiz', None):
                if logic.cham_diem_kiem_tra(chu, tin_cay, self.muc_tieu_quiz):
                    self.lbl_fc_trang_thai.configure(text="✅ CHÍNH XÁC! Đổi thẻ mới...",
                                                     text_color=self.main_app.mau_thanh_cong)
                    self.muc_tieu_quiz = None
                    self.after(1500, self.load_cau_hoi_flashcard)
        elif logic and logic.muc_tieu_hien_tai:
            trang_thai, tb = logic.kiem_tra_ket_qua(chu, tin_cay)
            if trang_thai == "DUNG":
                self.lbl_ket_qua.configure(text=tb, text_color=self.main_app.mau_thanh_cong)
                if self.bai_hien_tai and self.bai_hien_tai not in self.bai_da_hoc:
                    self.bai_da_hoc.add(self.bai_hien_tai)
                    if self.main_app.logic_ho_so: self.main_app.logic_ho_so.danh_dau_da_hoc(self.bai_hien_tai)
                    if self.bai_hien_tai in self.nut_bai_hoc_dict: self.nut_bai_hoc_dict[self.bai_hien_tai].configure(
                        fg_color="#00E676", text_color="#000000", text=f"✅ {self.bai_hien_tai}")
            elif trang_thai == "SAI":
                self.lbl_ket_qua.configure(text=tb, text_color=self.main_app.mau_chu_dao)
                if self.main_app.logic_ho_so and time.time() - getattr(self, 'tg_loi', 0) > 3.0:
                    self.main_app.logic_ho_so.ghi_nhan_loi_sai(logic.muc_tieu_hien_tai)
                    self.tg_loi = time.time()
            else:
                self.lbl_ket_qua.configure(text=tb, text_color="#FFCC00")

    def reset_giao_dien(self):
        self.lbl_camera.configure(image=None, text="[ ĐANG TẮT CAMERA... ]")
        self.lbl_ket_qua.configure(text="Chưa bật camera", text_color="#FFCC00")

    # ----- FLASHCARD LOGIC -----
    def mo_kiem_tra(self):
        if len(self.bai_da_hoc) < 5:
            self.lbl_mo_ta.configure(text="⚠️ Học xanh ít nhất 5 bài để mở khóa!", text_color="#e74c3c")
            return
        self.dang_kiem_tra = True
        self.cau_hoi_da_hoi = []
        for btn in self.nut_bai_hoc_dict.values(): btn.configure(state="disabled")

        self.lbl_tieu_de_hd.pack_forget()
        self.lbl_mo_ta.pack_forget()
        self.khung_nut_duoi.pack_forget()

        self.khung_flashcard = ctk.CTkFrame(self.khung_duoi, fg_color="transparent")
        self.khung_flashcard.pack(fill="both", expand=True, padx=20, pady=10)
        h = ctk.CTkFrame(self.khung_flashcard, fg_color="transparent")
        h.pack(fill="x")
        ctk.CTkLabel(h, text="🧠 CHẾ ĐỘ KIỂM TRA", font=self.main_app.font_tieu_de, text_color="#f39c12").pack(
            side="left")
        ctk.CTkButton(h, text="✖ Thoát", width=60, fg_color="#c0392b", hover_color="#a93226",
                      command=self.dong_kiem_tra).pack(side="right")
        self.lbl_fc_cau_hoi = ctk.CTkLabel(self.khung_flashcard, text="Đang tải thẻ...", font=("Segoe UI", 24, "bold"))
        self.lbl_fc_cau_hoi.pack(pady=(15, 5))
        self.lbl_fc_trang_thai = ctk.CTkLabel(self.khung_flashcard, text="...", font=self.main_app.font_chu)
        self.lbl_fc_trang_thai.pack(pady=5)

        self.khung_trac_nghiem = ctk.CTkFrame(self.khung_flashcard, fg_color="transparent")
        self.load_cau_hoi_flashcard()

    def load_cau_hoi_flashcard(self):
        if not self.dang_kiem_tra: return
        ds = [b for b in self.bai_da_hoc if b not in self.cau_hoi_da_hoi]
        if not ds: self.cau_hoi_da_hoi = []; ds = list(self.bai_da_hoc)
        bai_chon = random.choice(ds)
        self.cau_hoi_da_hoi.append(bai_chon)
        self.muc_tieu_quiz = self.main_app.logic_hoc._trich_xuat_chu(bai_chon)

        d_anh = ""
        for duoi in [".png", ".jpg"]:
            if os.path.exists(os.path.join(self.main_app.logic_hoc.thu_muc_anh, f"{self.muc_tieu_quiz}{duoi}")):
                d_anh = os.path.join(self.main_app.logic_hoc.thu_muc_anh, f"{self.muc_tieu_quiz}{duoi}")
                break

        # LUÔN TẠO ẢNH RỖNG (TRONG SUỐT) TRƯỚC ĐỂ CHỐNG LỖI SẬP APP CỦA TKINTER
        anh_rong = ctk.CTkImage(light_image=Image.new("RGBA", (180, 180), (0, 0, 0, 0)), size=(180, 180))
        self.lbl_anh_mau.configure(image=anh_rong)
        self.anh_fc_hien_tai = anh_rong

        # TIẾN HÀNH QUAY SỔ XỐ QUYẾT ĐỊNH LOẠI CÂU HỎI
        self.loai_cau_hoi = random.choices([1, 2], weights=[70, 30])[0]

        if self.loai_cau_hoi == 1:
            # DẠNG 1: YÊU CẦU MÚA TAY -> GIẤU ẢNH ĐI!
            self.khung_trac_nghiem.pack_forget()
            self.lbl_fc_cau_hoi.configure(text=f"Ký hiệu chữ: {self.muc_tieu_quiz}")
            self.lbl_fc_trang_thai.configure(text="Đưa tay lên camera...", text_color="white")
            self.lbl_tieu_de_phai.configure(text="Thử thách Trí nhớ")

            # Hiển thị dấu hỏi chấm thay vì ảnh thật
            self.lbl_anh_mau.configure(image=anh_rong, text="[ ? ]\nHãy nhớ lại ký hiệu", font=("Segoe UI", 16, "bold"))

        else:
            # DẠNG 2: NHÌN ẢNH ĐOÁN CHỮ -> CHIẾU ẢNH LÊN!
            self.lbl_fc_cau_hoi.configure(text="Ảnh bên phải là chữ gì?")
            self.lbl_fc_trang_thai.configure(text="Hãy chọn đáp án đúng", text_color="white")
            self.lbl_tieu_de_phai.configure(text="Câu hỏi Trắc nghiệm")
            self.khung_trac_nghiem.pack(pady=10)
            for w in self.khung_trac_nghiem.winfo_children(): w.destroy()

            # Hiển thị ảnh thật nếu có
            if d_anh:
                self.anh_fc_hien_tai = ctk.CTkImage(Image.open(d_anh), size=(180, 180))
                self.lbl_anh_mau.configure(image=self.anh_fc_hien_tai, text="")
            else:
                self.lbl_anh_mau.configure(image=anh_rong, text="[Thiếu ảnh]")

            # Tạo nút trắc nghiệm bên dưới
            dap_an = [self.muc_tieu_quiz]
            ds_sai = [self.main_app.logic_hoc._trich_xuat_chu(b) for b in self.bai_da_hoc if
                      self.main_app.logic_hoc._trich_xuat_chu(b) != self.muc_tieu_quiz]
            dap_an.extend(random.sample(ds_sai, min(3, len(ds_sai))))
            random.shuffle(dap_an)
            for da in dap_an:
                ctk.CTkButton(self.khung_trac_nghiem, text=da, font=self.main_app.font_chu_dam, width=60,
                              height=40, command=lambda ans=da: self.kiem_tra_trac_nghiem(ans)).pack(side="left",
                                                                                                     padx=10)

    def kiem_tra_trac_nghiem(self, ans):
        if ans == self.muc_tieu_quiz:
            self.lbl_fc_trang_thai.configure(text="✅ CHÍNH XÁC!", text_color=self.main_app.mau_thanh_cong)
            for w in self.khung_trac_nghiem.winfo_children(): w.configure(state="disabled")
            self.after(1500, self.load_cau_hoi_flashcard)
        else:
            self.lbl_fc_trang_thai.configure(text="❌ Sai rồi!", text_color="#e74c3c")
            if self.main_app.logic_ho_so: self.main_app.logic_ho_so.ghi_nhan_loi_sai(self.muc_tieu_quiz)

    def dong_kiem_tra(self):
        self.dang_kiem_tra = False
        if hasattr(self, 'khung_flashcard') and self.khung_flashcard.winfo_exists(): self.khung_flashcard.destroy()

        # ========================================================
        anh_rong = ctk.CTkImage(light_image=Image.new("RGBA", (180, 180), (0, 0, 0, 0)), size=(180, 180))
        self.lbl_anh_mau.configure(image=anh_rong, text="[Chưa có ảnh]")
        self.anh_fc_hien_tai = anh_rong
        self.anh_mau_hien_tai = anh_rong
        # ========================================================

        self.lbl_tieu_de_phai.configure(text="Chưa chọn bài")
        self.lbl_tieu_de_hd.pack(anchor="w", padx=20, pady=(15, 5))
        self.lbl_mo_ta.configure(text="(Vui lòng chọn bài học ở danh sách bên phải)", text_color="#A0A0A0")
        self.lbl_mo_ta.pack(anchor="w", padx=20, pady=5)
        self.khung_nut_duoi.pack(fill="x", side="bottom", pady=15, padx=20)
        for btn in self.nut_bai_hoc_dict.values(): btn.configure(state="normal")