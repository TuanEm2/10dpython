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
        self.cau_hoan_chinh = self.cau_hoan_chinh[:-1]
        return self.cau_hoan_chinh

    def xoa_toan_bo(self):
        self.cau_hoan_chinh = ""
        return self.cau_hoan_chinh

    def hien_thi_cau_hoan_chinh_thong_minh(self, cau_hoan_chinh):
        """Tự động co giãn cỡ font và gập dòng khi văn bản quá dài"""
        noi_dung = str(cau_hoan_chinh).strip()
        so_ky_tu = len(noi_dung)

        # 1. Thuật toán bậc thang tính cỡ chữ dựa vào mật độ ký tự
        if so_ky_tu <= 12:
            co_chu = 32  # Khổng lồ, rõ nét cho các từ đơn
        elif so_ky_tu <= 24:
            co_chu = 24  # Vừa vặn cho một câu ngắn
        elif so_ky_tu <= 42:
            co_chu = 18  # Thu nhỏ gọn gàng cho câu dài
        else:
            co_chu = 14  # Kích thước siêu tiết kiệm diện tích

        # 2. Cập nhật giao diện kèm "Khóa gập dòng" (wraplength)
        # Giả sử chiều ngang của Card chứa text là 640px, ta bẻ dòng ở mốc 600px
        self.lbl_ket_qua.configure(
            text=noi_dung if noi_dung else "...",
            font=("Segoe UI", co_chu, "bold"),
            wraplength=600  # <--- CHÌA KHÓA VÀNG CHỐNG TRÀN VIỀN!
        )