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
        self.so_tim = 3
        self.combo = 0
        self.cap_do = 1  # HỆ THỐNG CẤP ĐỘ MỚI
        self.so_cau_dung = 0  # Đếm số câu để tăng cấp

        self.cau_hoi_hien_tai = ""
        self.dang_choi = False

        self.thoi_gian_bat_dau = 0
        self.thoi_gian_gioi_han_goc = 15.0
        self.thoi_gian_gioi_han = self.thoi_gian_gioi_han_goc

        self.dang_delay = False
        self.thoi_diem_delay = 0
        self.thoi_gian_cho = 1.0

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
        return self.cau_hoi_hien_tai

    def tao_cau_hoi_moi(self):
        self.cau_hoi_hien_tai = random.choice(self.danh_sach_cau_hoi)
        self.thoi_gian_bat_dau = time.time()

    def lay_thoi_gian_con_lai(self):
        if not self.dang_choi: return 0.0
        con_lai = self.thoi_gian_gioi_han - (time.time() - self.thoi_gian_bat_dau)
        return max(0.0, con_lai)

    def kiem_tra_lien_tuc(self, chu_ai_doan, do_tin_cay):
        if not self.dang_choi or self.so_tim <= 0:
            return "KET_THUC", self.cau_hoi_hien_tai, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do

        if self.dang_delay:
            if time.time() - self.thoi_diem_delay >= self.thoi_gian_cho:
                self.dang_delay = False
                self.tao_cau_hoi_moi()
            return "DANG_DELAY", self.cau_hoi_hien_tai, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do

        thoi_gian_con = self.lay_thoi_gian_con_lai()

        # 1. Hết giờ -> Mất Combo, Trừ tim
        if thoi_gian_con <= 0:
            self.combo = 0
            self.so_tim -= 1
            if self.so_tim <= 0:
                self.dang_choi = False
                return "SAI_HET_TIM", self.cau_hoi_hien_tai, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do
            else:
                self.dang_delay = True
                self.thoi_diem_delay = time.time()
                return "HET_GIO", self.cau_hoi_hien_tai, self.so_tim, self.diem_so, 0.0, self.combo, self.cap_do

        # 2. Làm đúng -> Tăng Cấp & Cộng điểm
        if chu_ai_doan == self.cau_hoi_hien_tai and do_tin_cay >= 0.60:
            self.combo += 1
            diem_cong = 10 * self.combo
            self.diem_so += diem_cong
            self.so_cau_dung += 1

            # Cứ đúng 5 câu thì Level Up, ép thời gian ngắn lại 2s (khó nhất là 3s/câu)
            if self.so_cau_dung > 0 and self.so_cau_dung % 5 == 0:
                self.cap_do += 1
                self.thoi_gian_gioi_han = max(3.0, self.thoi_gian_gioi_han_goc - (self.cap_do - 1) * 2.0)

            self.dang_delay = True
            self.thoi_diem_delay = time.time()
            return "DUNG", self.cau_hoi_hien_tai, self.so_tim, self.diem_so, thoi_gian_con, self.combo, self.cap_do

        return "DANG_CHOI", self.cau_hoi_hien_tai, self.so_tim, self.diem_so, thoi_gian_con, self.combo, self.cap_do