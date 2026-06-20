import mysql.connector
from mysql.connector import Error
import os
import uuid

class QuanLyHoSo:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.database = "database_hoc_tap"

        self.file_session = "session_login.txt"
        self.file_device = "device_id.txt"

        self.username_guest = f"_guest_{self._lay_ma_thiet_bi()}"
        self.id_guest = None

        self._khoi_tao_database()
        self.id_tai_khoan_hien_tai = self._doc_session_dang_nhap()

    def _lay_ma_thiet_bi(self):
        if os.path.exists(self.file_device):
            with open(self.file_device, 'r') as f:
                return f.read().strip()
        else:
            new_id = str(uuid.uuid4().hex)[:16]
            with open(self.file_device, 'w') as f:
                f.write(new_id)
            return new_id

    def _doc_session_dang_nhap(self):
        if os.path.exists(self.file_session):
            try:
                with open(self.file_session, 'r') as f:
                    saved_id = int(f.read().strip())

                conn = self._ket_noi()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM NguoiDung WHERE id=%s", (saved_id,))
                    if cursor.fetchone():
                        conn.close()
                        return saved_id
                    conn.close()
            except Exception: pass
        return self.id_guest

    def _luu_session(self, user_id):
        with open(self.file_session, 'w') as f: f.write(str(user_id))

    def _xoa_session(self):
        if os.path.exists(self.file_session): os.remove(self.file_session)

    def _ket_noi(self):
        try:
            return mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        except Error as e:
            print(f"❌ LỖI KẾT NỐI DB: {e}")
            return None

    def _khoi_tao_database(self):
        conn = self._ket_noi()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS NguoiDung
            (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) UNIQUE, password VARCHAR(255), 
             ten_hien_thi VARCHAR(255), diem_cao_nhat INT DEFAULT 0, so_lan_choi_game INT DEFAULT 0)''')

            try: cursor.execute("ALTER TABLE NguoiDung ADD COLUMN thoi_gian_hoc FLOAT DEFAULT 0.0")
            except: pass

            try: cursor.execute("ALTER TABLE NguoiDung ADD COLUMN avatar VARCHAR(50) DEFAULT '🧑‍🚀'")
            except: pass

            cursor.execute('''CREATE TABLE IF NOT EXISTS TienDoHocTap
            (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, ten_bai_hoc VARCHAR(255), 
             UNIQUE KEY uq_user_bai (user_id, ten_bai_hoc))''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS ThongKeLoiSai
            (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, tu_sai VARCHAR(255), so_lan_sai INT DEFAULT 1,
             FOREIGN KEY (user_id) REFERENCES NguoiDung(id) ON DELETE CASCADE,
             UNIQUE KEY uq_user_tu (user_id, tu_sai))''')

            cursor.execute("SELECT id FROM NguoiDung WHERE username=%s", (self.username_guest,))
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO NguoiDung (username, password, ten_hien_thi) VALUES (%s, '', 'Khách Vãng Lai')", (self.username_guest,))
                self.id_guest = cursor.lastrowid
            else: self.id_guest = row[0]

            conn.commit()
            cursor.close()
            conn.close()

    def dang_nhap(self, username, password):
        conn = self._ket_noi()
        if not conn: return False, "Mất kết nối Database!"
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM NguoiDung WHERE username=%s AND password=%s", (username, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.id_tai_khoan_hien_tai = row[0]
            self._luu_session(row[0])
            return True, "Đăng nhập thành công!"
        return False, "Sai tài khoản hoặc mật khẩu!"

    def dang_ky(self, username, password, ten_hien_thi):
        if not username or not password or not ten_hien_thi: return False, "Vui lòng điền đủ thông tin!"
        conn = self._ket_noi()
        if not conn: return False, "Mất kết nối Database!"
        cursor = conn.cursor()
        try:
            # 1. Rút dữ liệu (Bao gồm cả thời gian học)
            cursor.execute("SELECT diem_cao_nhat, so_lan_choi_game, thoi_gian_hoc FROM NguoiDung WHERE id=%s",
                           (self.id_guest,))
            row = cursor.fetchone()
            diem = row[0] if row else 0
            so_lan = row[1] if row else 0
            thoi_gian = row[2] if (row and len(row) > 2 and row[2]) else 0.0

            # 2. Đẩy sang nhà mới
            cursor.execute(
                "INSERT INTO NguoiDung (username, password, ten_hien_thi, diem_cao_nhat, so_lan_choi_game, thoi_gian_hoc) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, password, ten_hien_thi, diem, so_lan, thoi_gian))
            new_id = cursor.lastrowid

            # 3. Di cư Tiến độ và Lỗi sai
            cursor.execute(
                "INSERT IGNORE INTO TienDoHocTap (user_id, ten_bai_hoc) SELECT %s, ten_bai_hoc FROM TienDoHocTap WHERE user_id=%s",
                (new_id, self.id_guest))
            cursor.execute(
                "INSERT IGNORE INTO ThongKeLoiSai (user_id, tu_sai, so_lan_sai) SELECT %s, tu_sai, so_lan_sai FROM ThongKeLoiSai WHERE user_id=%s",
                (new_id, self.id_guest))

            # 4. Reset tài khoản khách
            cursor.execute("UPDATE NguoiDung SET diem_cao_nhat=0, so_lan_choi_game=0, thoi_gian_hoc=0.0 WHERE id=%s",
                           (self.id_guest,))
            cursor.execute("DELETE FROM TienDoHocTap WHERE user_id=%s", (self.id_guest,))
            cursor.execute("DELETE FROM ThongKeLoiSai WHERE user_id=%s", (self.id_guest,))

            conn.commit()
            self.id_tai_khoan_hien_tai = new_id
            self._luu_session(new_id)
            return True, "Tạo tài khoản thành công!"
        except mysql.connector.IntegrityError:
            return False, "Tên đăng nhập đã tồn tại!"
        finally:
            conn.close()

    def dang_xuat(self):
        self.id_tai_khoan_hien_tai = self.id_guest
        self._xoa_session()
        return True, "Đã đăng xuất."

    def lay_thong_tin(self):
        conn = self._ket_noi()
        if not conn: return {"ten_hien_thi": "Lỗi mạng", "diem_cao_nhat": 0, "so_lan_choi_game": 0, "thoi_gian_hoc": 0.0, "avatar": "🧑‍🚀"}
        cursor = conn.cursor()
        cursor.execute("SELECT ten_hien_thi, diem_cao_nhat, so_lan_choi_game, thoi_gian_hoc, avatar FROM NguoiDung WHERE id=%s", (self.id_tai_khoan_hien_tai,))
        row = cursor.fetchone()
        conn.close()
        if row:
            ava = row[4] if (len(row) > 4 and row[4]) else "🧑‍🚀"
            return {"ten_hien_thi": row[0], "diem_cao_nhat": row[1], "so_lan_choi_game": row[2], "thoi_gian_hoc": row[3] if row[3] else 0.0, "avatar": ava}
        return {"ten_hien_thi": "", "diem_cao_nhat": 0, "so_lan_choi_game": 0, "thoi_gian_hoc": 0.0, "avatar": "🧑‍🚀"}

    def cap_nhat_sau_khi_choi(self, diem_moi):
        du_lieu_cu = self.lay_thong_tin()
        conn = self._ket_noi()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE NguoiDung SET diem_cao_nhat=%s, so_lan_choi_game=%s WHERE id=%s",
                           (max(diem_moi, du_lieu_cu["diem_cao_nhat"]), du_lieu_cu["so_lan_choi_game"] + 1, self.id_tai_khoan_hien_tai))
            conn.commit()
            conn.close()

    def danh_dau_da_hoc(self, ten_bai_hoc):
        conn = self._ket_noi()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT IGNORE INTO TienDoHocTap (user_id, ten_bai_hoc) VALUES (%s, %s)", (self.id_tai_khoan_hien_tai, ten_bai_hoc))
            conn.commit()
            conn.close()

    def lay_danh_sach_da_hoc(self):
        conn = self._ket_noi()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT ten_bai_hoc FROM TienDoHocTap WHERE user_id=%s", (self.id_tai_khoan_hien_tai,))
        ds = [row[0] for row in cursor.fetchall()]
        conn.close()
        return ds

    def lay_bang_xep_hang(self, top_n=5):
        conn = self._ket_noi()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT ten_hien_thi, diem_cao_nhat FROM NguoiDung WHERE diem_cao_nhat > 0 AND username NOT LIKE '_guest_%' ORDER BY diem_cao_nhat DESC LIMIT %s", (top_n,))
        data = cursor.fetchall()
        conn.close()
        return data

    def cap_nhat_ten_hien_thi(self, ten_moi):
        if not ten_moi or ten_moi.strip() == "": return False, "Tên không được để trống!"
        conn = self._ket_noi()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE NguoiDung SET ten_hien_thi=%s WHERE id=%s", (ten_moi, self.id_tai_khoan_hien_tai))
            conn.commit()
            conn.close()
            return True, "Đổi tên thành công!"
        return False, "Lỗi kết nối CSDL!"

    def cap_nhat_thoi_gian_hoc(self, phut_vua_hoc):
        if phut_vua_hoc <= 0: return
        conn = self._ket_noi()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE NguoiDung SET thoi_gian_hoc = thoi_gian_hoc + %s WHERE id=%s", (phut_vua_hoc, self.id_tai_khoan_hien_tai))
            conn.commit()
            conn.close()

    def ghi_nhan_loi_sai(self, tu_sai):
        conn = self._ket_noi()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ThongKeLoiSai (user_id, tu_sai, so_lan_sai) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE so_lan_sai = so_lan_sai + 1", (self.id_tai_khoan_hien_tai, tu_sai))
            conn.commit()
            conn.close()

    def lay_top_loi_sai(self, top_n=3):
        conn = self._ket_noi()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT tu_sai FROM ThongKeLoiSai WHERE user_id=%s ORDER BY so_lan_sai DESC LIMIT %s", (self.id_tai_khoan_hien_tai, top_n))
        ds = [row[0] for row in cursor.fetchall()]
        conn.close()
        return ds

    def cap_nhat_avatar(self, avatar_moi):
        conn = self._ket_noi()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE NguoiDung SET avatar=%s WHERE id=%s", (avatar_moi, self.id_tai_khoan_hien_tai))
            conn.commit()
            conn.close()