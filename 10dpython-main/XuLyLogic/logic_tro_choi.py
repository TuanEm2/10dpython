import random
import time
import pickle
import os


class QuanLyTroChoi:
    def __init__(self):
        self.danh_sach_cau_hoi = self._tai_danh_sach_tu_kho()
        if not self.danh_sach_cau_hoi:
            self.danh_sach_cau_hoi = ["A", "B", "C"]
        self.reset_game()

    def reset_game(self):
        self.diem_so = 0
        self.so_tim = 5
        self.combo = 0
        self.cap_do = 1
        self.so_cau_dung = 0

        self.chuoi_muc_tieu = []
        self.vi_tri_chuoi = 0
        self.cau_hoi_hien_tai = ""

        self.dang_choi = False
        self.thoi_gian_bat_dau = 0
        self.thoi_gian_gioi_han = 15.0

        self.dang_delay = False
        self.thoi_diem_delay = 0

        # --- BỘ TĂNG TỐC TRÒ CHƠI (TURBO LOGIC) ---
        self.thoi_gian_cho = 0.4  # Giảm từ 1.2s -> 0.4s: Xong 1 câu là nhảy câu mới ngay lập tức
        self.delay_giua_chu = 0.0  # Giảm từ 0.5s -> 0.0s: Không có bất kỳ độ trễ nào giữa các chữ trong chuỗi!

        self.thoi_diem_chuyen_chu = 0

    def _tai_danh_sach_tu_kho(self):
        ngan_hang = []
        duong_dan_tinh = os.path.join("KhoDuLieu", "model_tinh.pkl")
        if os.path.exists(duong_dan_tinh):
            try:
                with open(duong_dan_tinh, 'rb') as f:
                    model = pickle.load(f)
                    ngan_hang.extend(model.classes_.tolist())
            except:
                pass

        duong_dan_dong = os.path.join("KhoDuLieu", "model_dong_labels.npy")
        if os.path.exists(duong_dan_dong):
            try:
                import numpy as np
                nhan_dong = np.load(duong_dan_dong)
                ngan_hang.extend([n for n in nhan_dong if n not in ['NONE', 'None']])
            except:
                pass
        return list(set(ngan_hang))

    def bat_dau_game(self):
        self.reset_game()
        self.dang_choi = True
        self.dang_delay = False
        self.tao_cau_hoi_moi()
        return self.lay_chuoi_hien_thi()

    def tao_cau_hoi_moi(self):
        do_dai = min(4, 1 + (self.cap_do - 1) // 2)

        self.chuoi_muc_tieu = []
        for _ in range(do_dai):
            chu_moi = random.choice(self.danh_sach_cau_hoi)
            # Khóa chống trùng lặp chữ liên tiếp
            while len(self.chuoi_muc_tieu) > 0 and chu_moi == self.chuoi_muc_tieu[-1]:
                chu_moi = random.choice(self.danh_sach_cau_hoi)
            self.chuoi_muc_tieu.append(chu_moi)

        self.vi_tri_chuoi = 0
        self.thoi_gian_bat_dau = time.time()
        self.thoi_diem_chuyen_chu = time.time()

        thoi_gian_1_chu = max(3.0, 5.0 - (self.cap_do * 0.2))
        self.thoi_gian_gioi_han = thoi_gian_1_chu * do_dai

    def lay_chuoi_hien_thi(self):
        chuoi_ui = []
        for i, chu in enumerate(self.chuoi_muc_tieu):
            if i < self.vi_tri_chuoi:
                chuoi_ui.append("✓")
            elif i == self.vi_tri_chuoi:
                chuoi_ui.append(f"[{chu}]")
            else:
                chuoi_ui.append(chu)
        return "  ".join(chuoi_ui)

    def lay_thoi_gian_con_lai(self):
        if not self.dang_choi: return 0.0
        con_lai = self.thoi_gian_gioi_han - (time.time() - self.thoi_gian_bat_dau)
        return max(0.0, con_lai)

    def kiem_tra_lien_tuc(self, chu_ai_doan, do_tin_cay):
        chuoi_ui = self.lay_chuoi_hien_thi()

        if not self.dang_choi or self.so_tim <= 0:
            return "KET_THUC", chuoi_ui, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do

        if self.dang_delay:
            if time.time() - self.thoi_diem_delay >= self.thoi_gian_cho:
                self.dang_delay = False
                self.tao_cau_hoi_moi()
                chuoi_ui = self.lay_chuoi_hien_thi()
            return "DANG_DELAY", chuoi_ui, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do

        thoi_gian_con = self.lay_thoi_gian_con_lai()

        if thoi_gian_con <= 0:
            self.combo = 0
            self.so_tim -= 1
            if self.so_tim <= 0:
                self.dang_choi = False
                return "SAI_HET_TIM", chuoi_ui, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do
            else:
                self.dang_delay = True
                self.thoi_diem_delay = time.time()
                return "HET_GIO", chuoi_ui, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do

        if time.time() - self.thoi_diem_chuyen_chu < self.delay_giua_chu:
            return "DANG_CHOI", chuoi_ui, self.so_tim, self.diem_so, thoi_gian_con, self.combo, self.cap_do

        chu_muc_tieu = self.chuoi_muc_tieu[self.vi_tri_chuoi]

        # --- CẢI TIẾN: HẠ NGƯỠNG ĐỂ BẮT ĐIỂM CỰC NHẠY ---
        # Ngay khi AI chớp trúng đáp án với độ tự tin > 50%, Game chộp lấy ngay lập tức!
        if chu_ai_doan == chu_muc_tieu and do_tin_cay >= 0.50:
            self.vi_tri_chuoi += 1
            self.thoi_diem_chuyen_chu = time.time()

            if self.vi_tri_chuoi >= len(self.chuoi_muc_tieu):
                self.combo += 1
                diem_cong = 10 * len(self.chuoi_muc_tieu) * self.combo
                self.diem_so += diem_cong
                self.so_cau_dung += 1

                if self.so_cau_dung > 0 and self.so_cau_dung % 5 == 0:
                    self.cap_do += 1

                self.dang_delay = True
                self.thoi_diem_delay = time.time()
                chuoi_ui = self.lay_chuoi_hien_thi()
                return "DUNG", chuoi_ui, self.so_tim, self.diem_so, thoi_gian_con, self.combo, self.cap_do
            else:
                chuoi_ui = self.lay_chuoi_hien_thi()
                return "DANG_CHUOI", chuoi_ui, self.so_tim, self.diem_so, thoi_gian_con, self.combo, self.cap_do

        return "DANG_CHOI", chuoi_ui, self.so_tim, self.diem_so, thoi_gian_con, self.combo, self.cap_do