import time
import cv2
import threading
import customtkinter as ctk
from PIL import Image

# ====================================================================
# BỘ IMPORT TÁCH BIỆT (CHỐNG LỖI DOMINO KHI TÁCH FILE)
# ====================================================================
# 1. Tầng Logic
try:
    from XuLyLogic.logic_bai_hoc import QuanLyBaiHoc
except Exception as e:
    print(f"Lỗi load Học Tập: {e}"); QuanLyBaiHoc = None

try:
    from XuLyLogic.logic_thuc_hanh_tu_do import QuanLyThucHanhTuDo
except Exception as e:
    print(f"Lỗi load Thực Hành: {e}"); QuanLyThucHanhTuDo = None

try:
    from XuLyLogic.logic_ho_so import QuanLyHoSo
except Exception as e:
    print(f"Lỗi load Hồ Sơ: {e}"); QuanLyHoSo = None

try:
    from XuLyLogic.logic_tro_choi import QuanLyTroChoi
except Exception as e:
    print(f"Lỗi load Trò Chơi: {e}"); QuanLyTroChoi = None

try:
    from XuLyLogic.engine_nhan_dien_v2 import BoXuLyNhanDienKetHop
except Exception as e:
    print(f"Lỗi load AI: {e}"); BoXuLyNhanDienKetHop = None

# 2. Tầng Giao Diện (Panels)
try:
    from GiaoDien.panel_hoc_tap import PanelHocTap
except Exception as e:
    print(f"Lỗi load Panel Học Tập: {e}"); PanelHocTap = ctk.CTkFrame

try:
    from GiaoDien.panel_thuc_hanh import PanelThucHanh
except Exception as e:
    print(f"Lỗi load Panel Thực Hành: {e}"); PanelThucHanh = ctk.CTkFrame

try:
    from GiaoDien.panel_tro_choi import PanelTroChoi
except Exception as e:
    print(f"Lỗi load Panel Trò Chơi: {e}"); PanelTroChoi = ctk.CTkFrame

try:
    from GiaoDien.panel_ho_so import PanelHoSo
except Exception as e:
    print(f"Lỗi load Panel Hồ Sơ: {e}"); PanelHoSo = ctk.CTkFrame


class UngDungNhanDien(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SIGNLENS - Hệ Thống Ký Hiệu & Phiên Dịch")
        self.geometry("1300x800")
        self.minsize(1100, 700)

        # Biến trạng thái hệ thống
        self.camera_running = False
        self.camera_thread = None
        self.latest_frame = None
        self.latest_prediction = ("...", 0.0, "...")
        self.cam_start_time = None

        self.dinh_dang_giao_dien()

        # Khởi tạo Logic
        self.engine = BoXuLyNhanDienKetHop() if BoXuLyNhanDienKetHop else None
        self.logic_hoc = QuanLyBaiHoc() if QuanLyBaiHoc else None
        self.logic_thuc_hanh = QuanLyThucHanhTuDo() if QuanLyThucHanhTuDo else None
        self.logic_ho_so = QuanLyHoSo() if QuanLyHoSo else None
        self.logic_game = QuanLyTroChoi() if QuanLyTroChoi else None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.ve_menu_sidebar()

        self.khung_chinh = ctk.CTkFrame(self, fg_color="transparent")
        self.khung_chinh.grid(row=0, column=1, sticky="nsew", padx=(20, 20), pady=20)
        self.khung_chinh.grid_rowconfigure(0, weight=1)
        self.khung_chinh.grid_columnconfigure(0, weight=1)

        # Gắn các Component Giao Diện con vào Khung chính
        self.panel_hoc_tap = PanelHocTap(self.khung_chinh, main_app=self)
        self.panel_thuc_hanh = PanelThucHanh(self.khung_chinh, main_app=self)
        self.panel_tro_choi = PanelTroChoi(self.khung_chinh, main_app=self)
        self.panel_ho_so = PanelHoSo(self.khung_chinh, main_app=self)

        self.trang_hien_tai = "Học Tập"
        self.hien_thi_trang("Học Tập")
        self.protocol("WM_DELETE_WINDOW", self.dong_ung_dung)

    def dinh_dang_giao_dien(self):
        ctk.set_appearance_mode("dark")
        self.mau_nen = "#0D0D0D"
        self.mau_sidebar = "#141414"
        self.mau_card = "#1A1A1A"
        self.mau_chu_dao = "#E50914"
        self.mau_hover = "#B80710"
        self.mau_thanh_cong = "#00FFCC"
        self.configure(fg_color=self.mau_nen)
        self.font_logo = ("Segoe UI Black", 28, "bold")
        self.font_menu = ("Segoe UI", 16, "bold")
        self.font_tieu_de_lon = ("Segoe UI", 28, "bold")
        self.font_tieu_de = ("Segoe UI", 22, "bold")
        self.font_chu = ("Segoe UI", 15)
        self.font_chu_dam = ("Segoe UI", 15, "bold")

    def dong_ung_dung(self):
        self.camera_running = False
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=0.5)
        self.destroy()

    def ve_menu_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=self.mau_sidebar)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)
        ctk.CTkLabel(self.sidebar, text="SIGNLENS", font=self.font_logo, text_color=self.mau_chu_dao).grid(row=0,
                                                                                                           column=0,
                                                                                                           padx=20,
                                                                                                           pady=(30,
                                                                                                                 30))

        self.nut_menu = {}
        for i, ten in enumerate(["Học Tập", "Thực Hành Tự Do", "Minigame", "Hồ Sơ & Xếp Hạng"]):
            btn = ctk.CTkButton(self.sidebar, text=ten, font=self.font_menu, fg_color="transparent",
                                text_color="#A0A0A0", hover_color=self.mau_card, anchor="w",
                                command=lambda m=ten: self.hien_thi_trang(m))
            btn.grid(row=i + 1, column=0, padx=20, pady=10, sticky="ew")
            self.nut_menu[ten] = btn

    def hien_thi_trang(self, ten_trang):
        if self.camera_running: self.tat_camera()
        self.trang_hien_tai = ten_trang

        for ten, nut in self.nut_menu.items():
            nut.configure(fg_color=self.mau_card if ten == ten_trang else "transparent",
                          text_color="white" if ten == ten_trang else "#A0A0A0")

        for w in self.khung_chinh.winfo_children(): w.grid_forget()

        if ten_trang == "Học Tập":
            self.panel_hoc_tap.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Thực Hành Tự Do":
            self.panel_thuc_hanh.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Minigame":
            self.panel_tro_choi.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Hồ Sơ & Xếp Hạng":
            if hasattr(self.panel_ho_so, 'cap_nhat_giao_dien'): self.panel_ho_so.cap_nhat_giao_dien()
            self.panel_ho_so.grid(row=0, column=0, sticky="nsew")

    # ================= LUỒNG XỬ LÝ CAMERA TRUNG TÂM =================
    def bat_camera(self):
        if self.camera_running:
            return

        # Dọn dẹp luồng cũ triệt để trước khi mở
        if self.camera_thread is not None and self.camera_thread.is_alive():
            self.camera_running = False
            self.camera_thread.join()  # Đã gỡ bỏ timeout=1.0
            self.camera_thread = None

        self.camera_running = True
        self.latest_frame = None
        self.camera_thread = threading.Thread(target=self.luong_camera_ngam, daemon=True)
        self.camera_thread.start()
        self.cap_nhat_giao_dien()
        self.cam_start_time = time.time()

    def tat_camera(self):
        if self.cam_start_time:
            phut = (time.time() - self.cam_start_time) / 60.0
            if self.logic_ho_so: self.logic_ho_so.cap_nhat_thoi_gian_hoc(phut)
            self.cam_start_time = None

        self.camera_running = False

        # Khóa chặn đứng đợi phần cứng camera tắt hẳn
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join()
            self.camera_thread = None

        self.latest_frame = None

        try:
            if hasattr(self, 'panel_hoc_tap') and self.panel_hoc_tap.winfo_exists():
                self.panel_hoc_tap.reset_giao_dien()
            if hasattr(self, 'panel_thuc_hanh') and self.panel_thuc_hanh.winfo_exists():
                self.panel_thuc_hanh.reset_giao_dien()
            if hasattr(self, 'panel_tro_choi') and self.panel_tro_choi.winfo_exists():
                self.panel_tro_choi.reset_giao_dien()
        except Exception as e:
            print(f"Bỏ qua lỗi xóa UI: {e}")

    def luong_camera_ngam(self):
        # Ưu tiên DirectShow giúp nhả cổng nhanh, nếu thất bại lùi về mặc định
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1)

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        while self.camera_running and cap and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                if self.engine:
                    frame_ve, chu, tin_cay, nguon = self.engine.xu_ly_frame(frame)
                else:
                    frame_ve, chu, tin_cay, nguon = frame, "...", 0.0, "..."

                self.latest_frame = cv2.cvtColor(frame_ve, cv2.COLOR_BGR2RGB)
                self.latest_prediction = (chu, tin_cay, nguon)

        if cap:
            cap.release()

    def cap_nhat_giao_dien(self):
        if self.camera_running and self.latest_frame is not None:
            try:
                img = ctk.CTkImage(light_image=Image.fromarray(self.latest_frame), size=(640, 480))
                chu, tin_cay, nguon = self.latest_prediction

                if self.trang_hien_tai == "Học Tập":
                    self.panel_hoc_tap.cap_nhat_khung_hinh(img, chu, tin_cay)
                elif self.trang_hien_tai == "Thực Hành Tự Do":
                    self.panel_thuc_hanh.cap_nhat_khung_hinh(img, chu, tin_cay, nguon)
                elif self.trang_hien_tai == "Minigame":
                    self.panel_tro_choi.cap_nhat_khung_hinh(img, chu, tin_cay, nguon)
            except Exception as e:
                print(f"Lỗi Render UI: {e}")

        if self.camera_running:
            self.after(20, self.cap_nhat_giao_dien)


if __name__ == "__main__":
    UngDungNhanDien().mainloop()