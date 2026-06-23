class QuanLyThucHanhTuDo:
    def __init__(self):
        # Chỉ hiển thị kết quả nếu độ tin cậy của AI lớn hơn ngưỡng này
        self.nguong_tin_cay = 0.60
        self.cau_hoan_chinh = ""
        self.chu_hien_tai = ""

    def xu_ly_ket_qua(self, chu_ai_doan, do_tin_cay):
        """
        Nhận kết quả thô từ AI và quyết định xem giao diện nên hiển thị gì.
        Trả về: (Chữ hiển thị, Dòng thông báo tin cậy, Mã màu)
        """
        if chu_ai_doan and chu_ai_doan != "None" and do_tin_cay >= self.nguong_tin_cay:
            phan_tram = int(do_tin_cay * 100)
            thong_bao = f"Độ tin cậy: {phan_tram}%"
            mau_sac = "#2ecc71" # Màu xanh lá
            self.chu_hien_tai = chu_ai_doan
            return chu_ai_doan, thong_bao, mau_sac
        else:
            self.chu_hien_tai = ""
            return "...", "Đang quét...", "#7f8c8d"

    # ================= CÁC HÀM XỬ LÝ GHÉP CÂU =================
    def them_chu_vao_cau(self):
        if self.chu_hien_tai and self.chu_hien_tai != "...":
            self.cau_hoan_chinh += self.chu_hien_tai
        return self.cau_hoan_chinh

    def them_khoang_trang(self):
        # Ngăn chặn việc bấm 2 dấu cách liên tiếp
        if len(self.cau_hoan_chinh) > 0 and self.cau_hoan_chinh[-1] != " ":
            self.cau_hoan_chinh += " "
        return self.cau_hoan_chinh

    def xoa_ky_tu_cuoi(self):
        if len(self.cau_hoan_chinh) > 0:
            self.cau_hoan_chinh = self.cau_hoan_chinh[:-1]
        return self.cau_hoan_chinh

    def xoa_toan_bo(self):
        self.cau_hoan_chinh = ""
        return self.cau_hoan_chinh

    def phan_tich_van_ban_thanh_anh(self, van_ban):
        import os
        import re
        import numpy as np
        import pickle

        # 1. BỘ LỌC CHUẨN HÓA TIẾNG VIỆT
        def xoa_dau_tieng_viet(s):
            s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
            s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
            s = re.sub(r'[ìíịỉĩ]', 'i', s)
            s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
            s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
            s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
            s = re.sub(r'[đ]', 'd', s)
            return s

        van_ban_sach = xoa_dau_tieng_viet(van_ban.lower()).upper()
        # Loại bỏ các ký tự đặc biệt, giữ lại chữ cái và khoảng trắng
        van_ban_sach = re.sub(r'[^A-Z0-9\s]', ' ', van_ban_sach)
        van_ban_sach = " ".join(van_ban_sach.split())  # Xóa khoảng trắng thừa

        # 2. THU THẬP TỪ VỰNG TỪ 2 NGUỒN (ẢNH MẪU + NÃO BỘ AI)
        thu_muc_anh = os.path.join(os.getcwd(), "assets", "pic")
        tu_vung_he_thong = []

        # Nguồn 1: Quét thư mục ảnh
        if os.path.exists(thu_muc_anh):
            for f in os.listdir(thu_muc_anh):
                if f.endswith('.png') or f.endswith('.jpg'):
                    tu_vung_he_thong.append(os.path.splitext(f)[0])

        # Nguồn 2: Quét não bộ AI (Để dù thiếu ảnh vẫn nhận ra là 1 cụm)
        try:
            if os.path.exists("KhoDuLieu/model_dong_labels.npy"):
                tu_vung_he_thong.extend(np.load("KhoDuLieu/model_dong_labels.npy").tolist())
            if os.path.exists("KhoDuLieu/model_tinh.pkl"):
                with open("KhoDuLieu/model_tinh.pkl", 'rb') as f:
                    tu_vung_he_thong.extend(pickle.load(f).classes_)
        except Exception:
            pass

        # Loại bỏ từ rác, trùng lặp và SẮP XẾP TỪ DÀI XUỐNG NGẮN (Để bắt từ ghép trước)
        tu_vung_he_thong = list(set(tu_vung_he_thong))
        tu_vung_he_thong = [tu for tu in tu_vung_he_thong if tu.upper() not in ['NONE', '']]
        tu_vung_he_thong.sort(key=len, reverse=True)

        # 3. THUẬT TOÁN TÌM KIẾM THAM LAM (GREEDY MATCHING)
        chuoi_hien_tai = van_ban_sach
        ket_qua_tho = []

        while len(chuoi_hien_tai) > 0:
            match_found = False
            for tu_khoa in tu_vung_he_thong:
                # Biến "XIN_CHAO" thành "XIN CHAO" để so sánh với văn bản người dùng nhập
                tu_khoa_space = tu_khoa.replace('_', ' ')

                # Nếu đoạn văn bản bắt đầu bằng Cụm từ có trong hệ thống -> Bắt lấy nó!
                if chuoi_hien_tai.startswith(tu_khoa_space):
                    ket_qua_tho.append(tu_khoa)  # Giữ lại dấu gạch dưới nguyên thủy
                    chuoi_hien_tai = chuoi_hien_tai[len(tu_khoa_space):].strip()
                    match_found = True
                    break

            # Nếu không có từ ghép nào khớp, bẻ chữ cái đầu tiên ra làm chữ Tĩnh
            if not match_found:
                ky_tu = chuoi_hien_tai[0]
                if ky_tu != ' ': ket_qua_tho.append(ky_tu)
                chuoi_hien_tai = chuoi_hien_tai[1:].strip()

        # 4. CHUẨN BỊ GÓI ẢNH ĐỂ TRÌNH CHIẾU
        danh_sach_anh_ket_qua = []
        for tu in ket_qua_tho:
            file_png = f"{tu}.png"
            file_jpg = f"{tu}.jpg"

            if os.path.exists(os.path.join(thu_muc_anh, file_png)):
                danh_sach_anh_ket_qua.append((file_png, tu))
            elif os.path.exists(os.path.join(thu_muc_anh, file_jpg)):
                danh_sach_anh_ket_qua.append((file_jpg, tu))
            else:
                danh_sach_anh_ket_qua.append(("", tu))  # Biết là cụm từ nhưng báo thiếu ảnh

        return danh_sach_anh_ket_qua