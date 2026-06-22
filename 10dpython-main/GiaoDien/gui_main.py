import os
import sys
import warnings

# Khử toàn bộ dải rác đỏ Protobuf của Google
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
warnings.filterwarnings("ignore", category=UserWarning)

import threading
import time
import cv2
import customtkinter as ctk
from PIL import Image

try:
    from XuLyLogic.logic_bai_hoc import QuanLyBaiHoc
except Exception:
    QuanLyBaiHoc = None
try:
    from XuLyLogic.logic_thuc_hanh_tu_do import QuanLyThucHanhTuDo
except Exception:
    QuanLyThucHanhTuDo = None
try:
    from XuLyLogic.logic_ho_so import QuanLyHoSo
except Exception:
    QuanLyHoSo = None
try:
    from XuLyLogic.logic_tro_choi import QuanLyTroChoi
except Exception:
    QuanLyTroChoi = None
try:
    from XuLyLogic.engine_nhan_dien_v2 import BoXuLyNhanDienKetHop
except Exception:
    BoXuLyNhanDienKetHop = None

try:
    from GiaoDien.panel_hoc_tap import PanelHocTap
except Exception:
    PanelHocTap = ctk.CTkFrame
try:
    from GiaoDien.panel_thuc_hanh import PanelThucHanh
except Exception:
    PanelThucHanh = ctk.CTkFrame
try:
    from GiaoDien.panel_tro_choi import PanelTroChoi
except Exception:
    PanelTroChoi = ctk.CTkFrame
try:
    from GiaoDien.panel_ho_so import PanelHoSo
except Exception:
    PanelHoSo = ctk.CTkFrame


class UngDungNhanDien(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SIGNLENS - Hệ Thống Ký Hiệu & Phiên Dịch")
        self.geometry("1300x800")
        self.minsize(1100, 700)

        # --- KIẾN TRÚC "LUỒNG BẤT TỬ" GIẢI QUYẾT 100% DEADLOCK USB ---
        self.camera_running = False
        self.app_is_alive = True
        self.cam_wake_event = threading.Event()  # "Công tắc" gọi luồng cam dậy

        self.cam_session_id = 0
        self.latest_frame = None
        self.latest_prediction = ("...", 0.0, "...")
        self.cam_start_time = None

        self.dinh_dang_giao_dien()

        self.engine = BoXuLyNhanDienKetHop() if BoXuLyNhanDienKetHop else None
        self.logic_hoc = QuanLyBaiHoc() if QuanLyBaiHoc else None
        self.logic_thuc_hanh = (
            QuanLyThucHanhTuDo() if QuanLyThucHanhTuDo else None
        )
        self.logic_ho_so = QuanLyHoSo() if QuanLyHoSo else None
        self.logic_game = QuanLyTroChoi() if QuanLyTroChoi else None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.ve_menu_sidebar()

        self.khung_chinh = ctk.CTkFrame(self, fg_color="transparent")
        self.khung_chinh.grid(
            row=0, column=1, sticky="nsew", padx=(20, 20), pady=20
        )
        self.khung_chinh.grid_rowconfigure(0, weight=1)
        self.khung_chinh.grid_columnconfigure(0, weight=1)

        self.panel_hoc_tap = PanelHocTap(self.khung_chinh, main_app=self)
        self.panel_thuc_hanh = PanelThucHanh(self.khung_chinh, main_app=self)
        self.panel_tro_choi = PanelTroChoi(self.khung_chinh, main_app=self)
        self.panel_ho_so = PanelHoSo(self.khung_chinh, main_app=self)

        self.trang_hien_tai = "Học Tập"
        self.hien_thi_trang("Học Tập")

        # KHỞI ĐỘNG LUỒNG BẤT TỬ ĐÚNG 1 LẦN DUY NHẤT
        self.eternal_thread = threading.Thread(
            target=self._vong_lap_phan_cung_bat_tu, daemon=True
        )
        self.eternal_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.dong_ung_dung)

    def _vong_lap_phan_cung_bat_tu(self):
        """Sống cùng tuổi thọ App. Chỉ mở USB khi Event bật, xả sạch USB khi Event tắt"""
        while self.app_is_alive:
            # Luồng hoàn toàn đóng băng tại đây (0% CPU) cho đến khi bấm Bật Cam
            self.cam_wake_event.wait()
            if not self.app_is_alive:
                break

            # Bắt đầu chiếm quyền USB
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            while self.camera_running and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                if self.engine:
                    f_ve, chu, conf, src = self.engine.xu_ly_frame(frame)
                else:
                    f_ve, chu, conf, src = frame, "...", 0.0, "..."

                self.latest_frame = cv2.cvtColor(f_ve, cv2.COLOR_BGR2RGB)
                self.latest_prediction = (chu, conf, src)

            # Người dùng bấm Tắt -> Xả USB sạch sẽ, lặp lại trạng thái ngủ đông wait()
            if cap:
                cap.release()
            self.cam_wake_event.clear()

    def bat_camera(self):
        if self.camera_running:
            return

        self.camera_running = True
        self.cam_session_id += 1
        current_session = self.cam_session_id

        self.latest_frame = None
        self.cam_start_time = time.time()

        # BẬT CÔNG TẮC ĐÁNH THỨC LUỒNG BẤT TỬ!
        self.cam_wake_event.set()

        self.after(20, lambda: self._roi_anh_len_ui(current_session))

    def tat_camera(self):
        self.camera_running = False  # Ra lệnh cho luồng bất tử tự xả cap.release()
        self.cam_session_id += 1

        if self.cam_start_time:
            phut = (time.time() - self.cam_start_time) / 60.0
            if self.logic_ho_so:
                self.logic_ho_so.cap_nhat_thoi_gian_hoc(phut)
            self.cam_start_time = None

        self.latest_frame = None
        if self.engine:
            self.engine.reset_ket_qua()

        try:
            if hasattr(self.panel_hoc_tap, "reset_giao_dien"):
                self.panel_hoc_tap.reset_giao_dien()
            if hasattr(self.panel_thuc_hanh, "reset_giao_dien"):
                self.panel_thuc_hanh.reset_giao_dien()
            if hasattr(self.panel_tro_choi, "reset_giao_dien"):
                self.panel_tro_choi.reset_giao_dien()
        except Exception:
            pass

    def _roi_anh_len_ui(self, session_id):
        if not self.camera_running or session_id != self.cam_session_id:
            return

        if self.latest_frame is not None:
            try:
                p_img = Image.fromarray(self.latest_frame)
                img_ctk = ctk.CTkImage(light_image=p_img, size=(640, 480))
                chu, conf, nguon = self.latest_prediction

                if self.trang_hien_tai == "Học Tập":
                    self.panel_hoc_tap.cap_nhat_khung_hinh(img_ctk, chu, conf)
                elif self.trang_hien_tai == "Thực Hành Tự Do":
                    self.panel_thuc_hanh.cap_nhat_khung_hinh(
                        img_ctk, chu, conf, nguon
                    )
                elif self.trang_hien_tai == "Minigame":
                    self.panel_tro_choi.cap_nhat_khung_hinh(
                        img_ctk, chu, conf, nguon
                    )
            except Exception:
                pass

        if self.camera_running and session_id == self.cam_session_id:
            self.after(20, lambda: self._roi_anh_len_ui(session_id))

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

    def ve_menu_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=250, corner_radius=0, fg_color=self.mau_sidebar
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)
        ctk.CTkLabel(
            self.sidebar,
            text="SIGNLENS",
            font=self.font_logo,
            text_color=self.mau_chu_dao,
        ).grid(row=0, column=0, padx=20, pady=(30, 30))

        self.nut_menu = {}
        for i, ten in enumerate(
            ["Học Tập", "Thực Hành Tự Do", "Minigame", "Hồ Sơ & Xếp Hạng"]
        ):
            btn = ctk.CTkButton(
                self.sidebar,
                text=ten,
                font=self.font_menu,
                fg_color="transparent",
                text_color="#A0A0A0",
                hover_color="#1A1A1A",
                anchor="w",
                command=lambda m=ten: self.hien_thi_trang(m),
            )
            btn.grid(row=i + 1, column=0, padx=20, pady=10, sticky="ew")
            self.nut_menu[ten] = btn

    def hien_thi_trang(self, ten_trang):
        if self.camera_running:
            self.tat_camera()
        self.trang_hien_tai = ten_trang
        for ten, nut in self.nut_menu.items():
            nut.configure(
                fg_color="#1A1A1A" if ten == ten_trang else "transparent",
                text_color="white" if ten == ten_trang else "#A0A0A0",
            )
        for w in self.khung_chinh.winfo_children():
            w.grid_forget()

        if ten_trang == "Học Tập":
            self.panel_hoc_tap.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Thực Hành Tự Do":
            self.panel_thuc_hanh.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Minigame":
            self.panel_tro_choi.grid(row=0, column=0, sticky="nsew")
        elif ten_trang == "Hồ Sơ & Xếp Hạng":
            if hasattr(self.panel_ho_so, "cap_nhat_giao_dien"):
                self.panel_ho_so.cap_nhat_giao_dien()
            self.panel_ho_so.grid(row=0, column=0, sticky="nsew")

    def dong_ung_dung(self):
        self.app_is_alive = False
        self.camera_running = False
        self.cam_wake_event.set()  # Đánh thức để nó tự chui vào lệnh break
        if hasattr(self, "eternal_thread") and self.eternal_thread.is_alive():
            self.eternal_thread.join(timeout=0.5)
        self.destroy()


if __name__ == "__main__":
    UngDungNhanDien().mainloop()