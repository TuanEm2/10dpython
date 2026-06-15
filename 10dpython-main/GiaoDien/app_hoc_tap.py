import customtkinter as ctk
import cv2
from PIL import Image
from XuLyLogic.engine_nhan_dien_v2 import BoXuLyNhanDienKetHop

# Cài đặt giao diện mặc định
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AppHocNgonNguKyHieu(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ứng Dụng Học Ngôn Ngữ Ký Hiệu")
        self.geometry("900x600")

        # KHẮC PHỤC LỖI: Gọi BoXuLyNhanDienKetHop không tham số để tự nạp đường dẫn mặc định đời V2
        self.engine = BoXuLyNhanDienKetHop()

        # Biến quản lý camera
        self.cap = None
        self.camera_dang_chay = False

        # --- TẠO CÁC KHUNG MÀN HÌNH ---
        self.frame_trang_chu = ctk.CTkFrame(self)
        self.tao_man_hinh_trang_chu()

        self.frame_bai_hoc = ctk.CTkFrame(self)
        self.tao_man_hinh_bai_hoc()

        self.frame_camera = ctk.CTkFrame(self)
        self.tao_man_hinh_camera()

        # Bắt đầu bằng việc hiển thị trang chủ
        self.hien_thi_man_hinh(self.frame_trang_chu)

    def hien_thi_man_hinh(self, frame_can_hien):
        """Hàm dùng để chuyển đổi qua lại giữa các màn hình"""
        self.frame_trang_chu.pack_forget()
        self.frame_bai_hoc.pack_forget()
        self.frame_camera.pack_forget()
        frame_can_hien.pack(fill="both", expand=True)

    # --- CHI TIẾT TỪNG MÀN HÌNH ---
    def tao_man_hinh_trang_chu(self):
        label_tieude = ctk.CTkLabel(self.frame_trang_chu, text="HỆ THỐNG HỌC TẬP VSL", font=("Arial", 30, "bold"))
        label_tieude.pack(pady=100)

        btn_vao_hoc = ctk.CTkButton(self.frame_trang_chu, text="Bắt đầu học", font=("Arial", 20), height=50,
                                    command=lambda: self.hien_thi_man_hinh(self.frame_bai_hoc))
        btn_vao_hoc.pack(pady=20)

    def tao_man_hinh_bai_hoc(self):
        label_tieude = ctk.CTkLabel(self.frame_bai_hoc, text="CHỌN BÀI HỌC", font=("Arial", 25, "bold"))
        label_tieude.pack(pady=30)

        btn_back = ctk.CTkButton(self.frame_bai_hoc, text="< Quay lại", width=100,
                                 command=lambda: self.hien_thi_man_hinh(self.frame_trang_chu))
        btn_back.place(x=20, y=20)

        # Cập nhật danh sách bài học bao gồm cả ký hiệu tĩnh và chuyển động động để kiểm thử trực quan
        danh_sach_bai = ["Bài 1: Chữ A (Tĩnh)", "Bài 2: Chữ B (Tĩnh)", "Bài 3: Chữ J (Động)", "Bài 4: Chữ Z (Động)"]
        for bai in danh_sach_bai:
            btn = ctk.CTkButton(self.frame_bai_hoc, text=bai, font=("Arial", 18), height=40, width=300,
                                command=lambda b=bai: self.mo_camera_cho_bai_hoc(b))
            btn.pack(pady=10)

    def tao_man_hinh_camera(self):
        btn_back = ctk.CTkButton(self.frame_camera, text="< Thoát bài học", width=100, fg_color="#c0392b",
                                 hover_color="#e74c3c",
                                 command=self.dong_camera)
        btn_back.pack(pady=10, anchor="nw", padx=20)

        self.label_ten_bai = ctk.CTkLabel(self.frame_camera, text="Đang học...", font=("Arial", 20, "bold"),
                                          text_color="#f1c40f")
        self.label_ten_bai.pack(pady=5)

        self.label_video = ctk.CTkLabel(self.frame_camera, text="")
        self.label_video.pack(pady=10)

    # --- LOGIC XỬ LÝ CAMERA TRONG GIAO DIỆN ---
    def mo_camera_cho_bai_hoc(self, ten_bai_hoc):
        self.label_ten_bai.configure(text=f"Đang bật camera cho: {ten_bai_hoc}...")
        self.hien_thi_man_hinh(self.frame_camera)

        self.cap = cv2.VideoCapture(0)
        self.camera_dang_chay = True
        self.cap_nhat_khung_hinh()

    def cap_nhat_khung_hinh(self):
        """Hàm này tự động gọi lại chính nó liên tục để tạo thành Video"""
        if self.camera_dang_chay and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)

                # KHẮC PHỤC LỖI: Hứng trọn vẹn đầy đủ 4 biến đầu ra từ Engine V2
                frame, chu_ai_doan, do_tin_cay, nguon = self.engine.xu_ly_frame(frame)

                # Đổi tên hiển thị nguồn bộ não thuật toán để người dùng dễ theo dõi phản hồi
                bo_nao = "Mạng LSTM Động" if nguon == "DONG" else "Rừng Tĩnh (RF)" if nguon == "TINH" else "Đang quét..."

                # Cập nhật thông tin chi tiết lên thanh trạng thái giao diện bài học
                phan_tram = int(do_tin_cay * 100)
                self.label_ten_bai.configure(text=f"AI nhận diện: {chu_ai_doan} ({phan_tram}%) | Xử lý bằng: {bo_nao}")

                # Chuyển hệ màu để hiển thị lên App thông qua mảng ảnh mượt mà
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))

                self.label_video.configure(image=ctk_image)
                self.label_video.image = ctk_image

            # Duy trì cập nhật luồng khung hình sau mỗi 15 mili-giây
            self.after(15, self.cap_nhat_khung_hinh)

    def dong_camera(self):
        self.camera_dang_chay = False
        if self.cap:
            self.cap.release()
        self.label_video.configure(image=None)
        self.hien_thi_man_hinh(self.frame_bai_hoc)


# Khởi chạy ứng dụng học tập tích hợp đa mô hình toàn diện
if __name__ == "__main__":
    app = AppHocNgonNguKyHieu()
    app.mainloop()