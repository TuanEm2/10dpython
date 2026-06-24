import os
import pickle
import numpy as np
import random


class QuanLyBaiHoc:
    def __init__(self):
        self.muc_tieu_hien_tai = ""
        # Đường dẫn tới thư mục ảnh
        self.thu_muc_anh = os.path.join(os.getcwd(), "assets", "pic")
        # Đường dẫn tới thư mục chứa các file mô tả (.txt)
        self.thu_muc_mo_ta = os.path.join(os.getcwd(), "assets", "mo_ta")

        # Hạ ngưỡng xuống 0.6 để phù hợp với cả dữ liệu động (vốn khó nhận diện điểm cao hơn tĩnh)
        self.nguong_tin_cay = 0.60

        # Tự động quét kho dữ liệu để lên giáo trình
        self.danh_sach_bai_hoc = self._lay_danh_sach_bai_hoc()

    def _lay_danh_sach_bai_hoc(self):
        danh_sach = []
        chu_da_them = set()  # BỘ LỌC CHỐNG TRÙNG LẶP
        dem = 1

        # 1. Đọc kho Tĩnh
        duong_dan_tinh = os.path.join("KhoDuLieu", "model_tinh.pkl")
        if os.path.exists(duong_dan_tinh):
            try:
                with open(duong_dan_tinh, 'rb') as f:
                    model = pickle.load(f)
                    for chu in model.classes_:
                        # Làm sạch dữ liệu
                        chu_sach = str(chu).strip().upper()

                        # CHỈ THÊM VÀO NẾU CHỮ NÀY CHƯA TỪNG XUẤT HIỆN
                        if chu_sach not in chu_da_them and chu_sach != "":
                            danh_sach.append(f"Bài {dem}: Chữ {chu_sach} (Tĩnh)")
                            chu_da_them.add(chu_sach)  # Đánh dấu là đã có chữ này
                            dem += 1
            except Exception as e:
                print(f"Lỗi đọc model tĩnh: {e}")

        # 2. Đọc kho Động
        duong_dan_dong = os.path.join("KhoDuLieu", "model_dong_labels.npy")
        if os.path.exists(duong_dan_dong):
            try:
                labels = np.load(duong_dan_dong, allow_pickle=True)
                for chu in labels:
                    chu_sach = str(chu).strip().upper()

                    # Bộ lọc cũng áp dụng luôn cho kho động để tránh trùng với kho tĩnh
                    if chu_sach not in chu_da_them and chu_sach not in ['NONE', '']:
                        danh_sach.append(f"Bài {dem}: Chữ {chu_sach} (Động)")
                        chu_da_them.add(chu_sach)
                        dem += 1
            except Exception as e:
                print(f"Lỗi đọc model động: {e}")

        return danh_sach

    def thiet_lap_bai_hoc(self, ten_bai_hoc):
        self.muc_tieu_hien_tai = self._trich_xuat_chu(ten_bai_hoc)
        duong_dan_anh = os.path.join(self.thu_muc_anh, f"{self.muc_tieu_hien_tai}.png")
        return self.muc_tieu_hien_tai, duong_dan_anh

    def kiem_tra_ket_qua(self, chu_ai_doan, do_tin_cay):
        if not chu_ai_doan or chu_ai_doan == "None":
            return "KHONG_THAY", "Hãy đưa tay lên màn hình"

        if chu_ai_doan == self.muc_tieu_hien_tai and do_tin_cay >= self.nguong_tin_cay:
            return "DUNG", "🎉 CHÍNH XÁC!"
        else:
            return "SAI", f"Chưa đúng. AI nhìn ra: {chu_ai_doan}"

    # ==========================================
    # CÁC HÀM XỬ LÝ LOGIC KIỂM TRA & MÔ TẢ
    # ==========================================
    def _trich_xuat_chu(self, ten_bai):
        """Hàm hỗ trợ cắt chuỗi lấy chữ cái/từ (Hỗ trợ đa định dạng để không bị lỗi mô tả)"""
        try:
            if "Chữ " in ten_bai:
                chuoi_cat = ten_bai.split("Chữ ")[1]
                chu_cai_hoac_tu = chuoi_cat.split(" (")[0]
                return chu_cai_hoac_tu.strip().upper()
            else:
                return str(ten_bai).strip().upper()
        except:
            return "A"

    def lay_mo_ta_huong_dan(self, muc_tieu):
        """Đọc file mô tả tương ứng từ thư mục assets/mo_ta/"""
        duong_dan_file = os.path.join(self.thu_muc_mo_ta, f"{muc_tieu}.txt")

        # Kiểm tra xem file txt của chữ/từ này có tồn tại không
        if os.path.exists(duong_dan_file):
            try:
                # Mở và đọc file với chuẩn UTF-8 để không bị lỗi font tiếng Việt
                with open(duong_dan_file, 'r', encoding='utf-8') as f:
                    mo_ta = f.read().strip()
                    if mo_ta:
                        return mo_ta
            except Exception as e:
                return f"(Lỗi đọc file mô tả: {e})"

        # Nếu chưa tạo file txt cho chữ này, trả về câu mặc định
        return f"Hãy đưa tay lên camera và tạo ký hiệu '{muc_tieu}' theo ảnh mẫu."

    def tao_cau_hoi_kiem_tra(self, danh_sach_da_hoc, cau_hien_tai=None):
        """Bốc ngẫu nhiên 1 bài đã học (tránh lặp lại câu vừa hỏi nếu có thể)"""
        if not danh_sach_da_hoc:
            return None

        ds_hop_le = list(danh_sach_da_hoc)
        # Nếu đã học nhiều hơn 1 bài, loại bỏ câu vừa hỏi để tránh lặp
        if cau_hien_tai and len(ds_hop_le) > 1:
            ds_hop_le = [b for b in ds_hop_le if self._trich_xuat_chu(b) != cau_hien_tai]

        bai_random = random.choice(ds_hop_le)
        return self._trich_xuat_chu(bai_random)

    def cham_diem_kiem_tra(self, chu_ai_doan, do_tin_cay, muc_tieu_kiem_tra):
        """Trả về True nếu học viên làm đúng ký hiệu bài kiểm tra"""
        if chu_ai_doan == muc_tieu_kiem_tra and do_tin_cay >= self.nguong_tin_cay:
            return True
        return False