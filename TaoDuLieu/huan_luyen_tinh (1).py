import os
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


def chay_huan_luyen():
    print("\n--- BƯỚC 2: HUẤN LUYỆN RANDOM FOREST ---") 
    csv_file = 'dataset_tinh.csv'
    model_file = 'model_tinh.pkl'

    if not os.path.exists(csv_file):
        print(f"[LỖI] Chưa có file '{csv_file}'. Hãy chạy BƯỚC 1 trước!")
        return

    try:
        data = pd.read_csv(csv_file)
        if len(data) < 10:
            print("[LỖI] CSV trống hoặc quá ít dữ liệu!")
            return

        X = data.iloc[:, 1:].values
        y = data.iloc[:, 0].values  # Random Forest của sklearn tự hiểu nhãn String (A, B, C...)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print("-> Đang huấn luyện Rừng Ngẫu Nhiên (Vui lòng đợi)...")
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        print("-> Đang chấm điểm độ chính xác...")
        y_pred = model.predict(X_test)
        print(f"\n[KẾT QUẢ] ĐỘ CHÍNH XÁC: {accuracy_score(y_test, y_pred) * 100:.2f}%")
        print("\nBẢNG ĐIỂM CHI TIẾT:")
        print(classification_report(y_test, y_pred))

        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        print(f"\n[THÀNH CÔNG] Đã lưu bộ não vào file: '{model_file}'")

    except Exception as e:
        print(f"[LỖI] Quá trình huấn luyện thất bại: {e}")


if __name__ == "__main__":
    chay_huan_luyen()