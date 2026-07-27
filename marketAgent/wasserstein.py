import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def apply_wk_means(file_path, price_col='Close', date_col='Date', k=2, h1=20, h2=5):
    # 1. Đọc dữ liệu từ file CSV
    df = pd.read_csv(file_path)
    
    dates = pd.to_datetime(df[date_col], format='%d/%m/%Y')
    prices = df[price_col].values
    
    # --- GIỮ NGUYÊN HOÀN TOÀN LOGIC THUẬT TOÁN ---
    log_returns = np.diff(np.log(prices))
    
    # 2. Tạo phân đoạn (Stream Lift)
    segments = []
    for i in range(0, len(log_returns) - h1 + 1, h2):
        segment = log_returns[i : i + h1]
        segments.append(np.sort(segment)) 
    
    segments = np.array(segments)
    M = len(segments)
    
    # 3. Thuật toán WK-means
    # CỐ ĐỊNH SEED Ở ĐÂY ĐỂ TRÁNH NHẢY MÀU KHI CHẠY LẠI
    np.random.seed(30) # số bất kì
    
    indices = np.random.choice(M, k, replace=False)
    centroids = segments[indices]
    labels = np.zeros(M)
    
    for _ in range(50):
        new_labels = []
        for seg in segments:
            distances = [np.mean(np.abs(seg - c)) for c in centroids]
            new_labels.append(np.argmin(distances))
        new_labels = np.array(new_labels)
        
        new_centroids = []
        for j in range(k):
            cluster_data = segments[new_labels == j]
            if len(cluster_data) > 0:
                new_centroids.append(np.median(cluster_data, axis=0))
            else:
                new_centroids.append(centroids[j])
        centroids = np.array(new_centroids)
        labels = new_labels

    return dates, labels, prices, h1, h2

# ==========================================
# GỌI HÀM VÀ VẼ ĐỒ THỊ
# ==========================================
dates, labels, prices, h1, h2 = apply_wk_means("D:/PER_WORKSPACE/scan_document/media/data_kcn.csv", k=2, h1=20, h2=1)

plt.figure(figsize=(15, 7))

# Vẽ đường giá gốc theo Trục X là Ngày
plt.plot(dates, prices, color='blue', alpha=0.8, linewidth=1.5, label='Close Price')

# Đoạn tô màu vùng dựa trên nhãn ngày
for i, label in enumerate(labels):
    start_idx = i * h2
    end_idx = min(start_idx + h1, len(dates) - 1)
    
    start_date = dates.iloc[start_idx]
    end_date = dates.iloc[end_idx]
    
    color = 'green' if label == 0 else 'red'
    plt.axvspan(start_date, end_date, color=color, alpha=0.15)

# Cấu hình hiển thị ngày tháng rõ ràng
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=6, maxticks=12))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
plt.gcf().autofmt_xdate()
plt.grid(True, linestyle='--', alpha=0.4)

plt.title('WK-Means Clustering - Price Time Series with Regimes (RCN)', fontsize=14, fontweight='bold')
plt.ylabel('Price', fontsize=12)
plt.legend(loc='upper left')

plt.tight_layout()
plt.show()