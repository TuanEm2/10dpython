import os
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.utils import to_categorical

KY_HIEU_DONG  = ['J', 'Z']
SO_FRAME      = 30
SO_TOA_DO     = 63
THU_MUC_DATA  = 'dataset_dong'
MODEL_DIR     = 'KhoDuLieu'
MODEL_FILE    = os.path.join(MODEL_DIR, 'model_dong.h5')
LABEL_FILE    = os.path.join(MODEL_DIR, 'model_dong_labels.npy')

def doc_dataset():
    print("\n--- PHÂN TÍCH VÀ ĐỌC DATASET ĐỘNG ---")
    X_list, y_list = [], []

    for nhan_so, ky_hieu in enumerate(KY_HIEU_DONG):
        thu_muc = os.path.join(THU_MUC_DATA, ky_hieu)
        if not os.path.exists(thu_muc):
            print(f"  [CẢNH BÁO] Trống thư mục dữ liệu: {thu_muc}")
            continue

        cac_file = sorted([f for f in os.listdir(thu_muc) if f.endswith('.npy')])
        dem_loi = 0
        for ten_file in cac_file:
            duong_dan = os.path.join(thu_muc, ten_file)
            try:
                mau = np.load(duong_dan)
                if mau.shape == (SO_FRAME, SO_TOA_DO):
                    X_list.append(mau)
                    y_list.append(nhan_so)
                else:
                    dem_loi += 1
            except Exception:
                dem_loi += 1

        print(f"  [{ky_hieu}] Đọc thành công {len(cac_file) - dem_loi} mẫu mảng chuỗi.")

    if len(X_list) == 0:
        print("[THẤT BẠI] Không tìm thấy dữ liệu .npy hợp lệ.")
        return None, None

    return np.array(X_list), np.array(y_list)

def xay_model_lstm(so_lop_nhan=len(KY_HIEU_DONG)):
    """Kiến trúc mạng sâu chuỗi thời gian nén gọn, chống rò rỉ và học quá mức"""
    model = Sequential([
        LSTM(64, return_sequences=True, activation='relu', input_shape=(SO_FRAME, SO_TOA_DO)),
        LSTM(64, return_sequences=False, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(so_lop_nhan, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

def chay_huan_luyen_dong():
    print("\n--- BƯỚC 2B: HUẤN LUYỆN BỘ NÃO DEEP LEARNING (LSTM) ---")
    os.makedirs(MODEL_DIR, exist_ok=True)

    X, y = doc_dataset()
    if X is None: return

    y_onehot = to_categorical(y, num_classes=len(KY_HIEU_DONG))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_onehot, test_size=0.2, random_state=42, stratify=y
    )

    model = xay_model_lstm()
    model.summary()

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1),
        ModelCheckpoint(MODEL_FILE, monitor='val_accuracy', save_best_only=True, verbose=1)
    ]

    print(f"\n-> Bắt đầu quá trình huấn luyện nơ-ron mạng...")
    model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test), callbacks=callbacks, verbose=1)

    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n[HOÀN THÀNH] ĐỘ CHÍNH XÁC KIỂM THỬ: {acc * 100:.2f}%")

    np.save(LABEL_FILE, np.array(KY_HIEU_DONG))
    print(f"  -> Đã đóng gói Model lưu tại: {MODEL_FILE}")
    print(f"  -> Đã đóng gói Nhãn lưu tại: {LABEL_FILE}")

if __name__ == "__main__":
    chay_huan_luyen_dong()