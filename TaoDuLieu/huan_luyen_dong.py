import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split

# ==========================================
# CẤU HÌNH CƠ BẢN
# ==========================================
KY_HIEU_DONG = ['J', 'Z', 'NONE']  # Đừng quên thêm nhãn NONE để chống nhiễu nhé!
SO_FRAME = 45
SO_TOA_DO = 126
THU_MUC_DATA = 'dataset_dong'
MODEL_DIR = 'KhoDuLieu'
MODEL_FILE = os.path.join(MODEL_DIR, 'model_dong_pytorch.pth')
LABEL_FILE = os.path.join(MODEL_DIR, 'model_dong_labels.npy')

# Tự động chọn GPU (CUDA) nếu có, nếu không thì xài CPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def doc_dataset():
    print("\n--- PHÂN TÍCH VÀ ĐỌC DATASET ĐỘNG (PYTORCH) ---")
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

    if not X_list:
        print("[THẤT BẠI] Không tìm thấy dữ liệu hợp lệ.")
        return None, None
    return np.array(X_list), np.array(y_list)


# ==========================================
# KHỞI TẠO KIẾN TRÚC MẠNG NƠ-RON BẰNG PYTORCH
# ==========================================
class SignLanguageLSTM(nn.Module):
    def __init__(self, num_classes):
        super(SignLanguageLSTM, self).__init__()

        # Lớp 1: Bi-LSTM
        self.lstm1 = nn.LSTM(input_size=SO_TOA_DO, hidden_size=128, bidirectional=True, batch_first=True)
        self.bn1 = nn.BatchNorm1d(256)
        self.dropout1 = nn.Dropout(0.3)

        # Lớp 2: Bi-LSTM
        self.lstm2 = nn.LSTM(input_size=256, hidden_size=64, bidirectional=True, batch_first=True)
        self.bn2 = nn.BatchNorm1d(128)
        self.dropout2 = nn.Dropout(0.3)

        # Các lớp Dense (Fully Connected)
        self.fc1 = nn.Linear(128, 128)
        self.relu = nn.ReLU()
        self.dropout3 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_classes)

    def forward(self, x):
        # x shape: (batch, seq, feature)
        out, _ = self.lstm1(x)

        # PyTorch BatchNorm1d yêu cầu đầu vào shape (batch, features, seq)
        out = out.transpose(1, 2)
        out = self.bn1(out)
        out = out.transpose(1, 2)
        out = self.dropout1(out)

        out, _ = self.lstm2(out)

        # Lấy frame cuối cùng của chuỗi (Tương đương return_sequences=False trong Keras)
        out = out[:, -1, :]

        out = self.bn2(out)
        out = self.dropout2(out)

        out = self.fc1(out)
        out = self.relu(out)
        out = self.dropout3(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.fc3(out)  # Không dùng Softmax ở đây vì CrossEntropyLoss tự động tính
        return out


# ==========================================
# VÒNG LẶP HUẤN LUYỆN
# ==========================================
def chay_huan_luyen():
    print(f"\n--- BƯỚC 2B: HUẤN LUYỆN PYTORCH LSTM TRÊN {device.type.upper()} ---")
    os.makedirs(MODEL_DIR, exist_ok=True)

    X, y = doc_dataset()
    if X is None: return

    # Tách dữ liệu và bọc vào Tensor PyTorch
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    train_data = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
    test_data = TensorDataset(torch.tensor(X_test, dtype=torch.float32), torch.tensor(y_test, dtype=torch.long))

    train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=32, shuffle=False)

    model = SignLanguageLSTM(num_classes=len(KY_HIEU_DONG)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    best_val_loss = float('inf')
    patience_counter = 0
    patience = 15
    epochs = 100

    print("-> Bắt đầu huấn luyện...")
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Đánh giá (Validation)
        model.eval()
        val_loss, correct, total = 0.0, 0, 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        avg_val_loss = val_loss / len(test_loader)
        val_acc = 100 * correct / total

        print(
            f"Epoch {epoch + 1:03d} | Train Loss: {train_loss / len(train_loader):.4f} | Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.2f}%")

        scheduler.step(avg_val_loss)

        # Early Stopping & Lưu Model tốt nhất
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Lưu toàn bộ trọng số (state_dict) của PyTorch
            torch.save(model.state_dict(), MODEL_FILE)
            print("  [*] Đã lưu mô hình mới tốt nhất!")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\n[DỪNG SỚM] Mô hình không cải thiện sau {patience} epochs.")
                break

    np.save(LABEL_FILE, np.array(KY_HIEU_DONG))
    print(f"\n[HOÀN THÀNH] Đã đóng gói Trọng số PyTorch tại: {MODEL_FILE}")


if __name__ == "__main__":
    chay_huan_luyen()