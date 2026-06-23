import requests

URL_API = "http://127.0.0.1:8000/api/mo-rong-cau"


def goi_api_mo_rong_cau(van_ban_goc):
    """Gửi đoạn ký hiệu lên Server và in log ra Terminal để theo dõi"""
    try:
        text_clean = " ".join(van_ban_goc.strip().split())

        # IN RA TERMINAL ĐỂ BẮT LỖI
        print(f"\n[API CLIENT] 📡 Đang gửi chữ lên Server: '{text_clean}'")

        data_gui = {"text": text_clean}
        # Tăng thời gian chờ lên 2 giây cho chắc chắn
        response = requests.post(URL_API, json=data_gui, timeout=2.0)

        if response.status_code == 200:
            ket_qua = response.json()["expanded_text"]
            print(f"[API CLIENT] ✅ Server trả về thành công: '{ket_qua}'")
            return ket_qua
        else:
            print(f"[API CLIENT] ❌ Lỗi từ Server, mã lỗi: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("[API CLIENT] ❌ Không gọi được! Bạn đã bật file server.py chưa?")
    except requests.exceptions.Timeout:
        print("[API CLIENT] ❌ Máy chủ phản hồi quá chậm (Timeout)!")
    except Exception as e:
        print(f"[API CLIENT] ❌ Lỗi không xác định: {e}")

    # Rớt mạng thì trả về câu gốc
    return van_ban_goc