import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer # <--- Thư viện xử lý dữ liệu thiếu
import joblib

# 1. Đọc dữ liệu
try:
    # Giả sử file CSV bạn đã cập nhật thêm các cột: Prev_Open, Prev_High, Prev_Low, Entropy_Score
    data = pd.read_csv('D:/PER_WORKSPACE/scan_document/forecasting/training_data.csv')
    print("Đọc file thành công.")
except FileNotFoundError:
    print("Lỗi: Không tìm thấy file training_data.csv")
    exit()

# === BƯỚC QUAN TRỌNG: LÀM SẠCH DỮ LIỆU ===

# Kiểm tra dòng thiếu Target (Giá mục tiêu) thì bắt buộc phải bỏ (vì không học được)
data_clean = data.dropna(subset=['Target_Price'])

if len(data_clean) == 0:
    print("Lỗi: File dữ liệu rỗng hoặc tất cả dòng Target_Price đều trống!")
    exit()

# =======================================

# 2. Chọn đặc trưng (Features) và Mục tiêu (Target)
# Cập nhật danh sách Feature mới
features = [
    'Prev_Open', 'Prev_High', 'Prev_Low', 'Prev_Close', # Nhóm giá (Ngày cũ)
    'Inventory_Level',                                  # Tồn kho (Ngày cũ)
    'Weather_Score',                                    # Thời tiết (Ngày hiện tại)
    'Entropy_Score'                                     # Tin tức (Ngày hiện tại)
]

X = data_clean[features]
y = data_clean['Target_Price']

# 3. Chia dữ liệu (80% học, 20% thi)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === BƯỚC MỚI: XỬ LÝ DỮ LIỆU THIẾU (IMPUTATION) ===
# Nếu dữ liệu thiếu, điền bằng giá trị trung bình của cột đó
imputer = SimpleImputer(strategy='mean')

# Fit vào tập train và transform cả train lẫn test
X_train_imputed = imputer.fit_transform(X_train)
X_test_imputed = imputer.transform(X_test)

# 4. Huấn luyện mô hình (Random Forest)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train_imputed, y_train)

# 5. Đánh giá mô hình
score = model.score(X_test_imputed, y_test)
print(f"Độ chính xác (R^2) trên tập kiểm tra: {score:.2f}")

# 6. Lưu Mô hình và Imputer
joblib.dump(model, 'ml_models/coffee_price_model.pkl')
joblib.dump(imputer, 'ml_models/coffee_imputer.pkl') # <--- Lưu cái điền khuyết để dùng bên views

print("Đã lưu model và imputer thành công!")