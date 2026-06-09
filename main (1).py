import os


def hien_thi_menu():
    while True:
        print("\n" + "=" * 45)
        print(" HỆ THỐNG NHẬN DIỆN NGÔN NGỮ KÝ HIỆU (A-Z)")
        print("=" * 45)
        print("1. [BƯỚC 1] Thu thập dữ liệu")
        print("2. [BƯỚC 2] Huấn luyện AI")
        print("3. [BƯỚC 3] Nhận diện thực tế")
        print("0. Thoát")
        print("=" * 45)

        lua_chon = input("Chọn chức năng: ").strip()
        if lua_chon == '1':
            os.system('python thu_thap_tinh.py')
        elif lua_chon == '2':
            os.system('python huan_luyen_tinh.py')
        elif lua_chon == '3':
            os.system('python nhan_dien.py')
        elif lua_chon == '0':
            break


if __name__ == "__main__":
    hien_thi_menu()