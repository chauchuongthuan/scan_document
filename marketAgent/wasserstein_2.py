import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def gaussian_kernel(x, y, sigma=0.1):
    """Tính toán Gaussian Kernel cho MMD [2, 9]."""
    dist_sq = np.sum((x[:, None] - y[None, :])**2)
    return np.exp(-dist_sq / (2 * sigma**2))

def calculate_mmd(sample_x, sample_y, sigma=0.1):
    """Tính toán chỉ số MMD dựa trên công thức (53) trong tài liệu [10]."""
    n = len(sample_x)
    m = len(sample_y)
    
    # Tính các thành phần của MMD
    k_xx = np.exp(-(np.subtract.outer(sample_x, sample_x)**2) / (2 * sigma**2))
    k_yy = np.exp(-(np.subtract.outer(sample_y, sample_y)**2) / (2 * sigma**2))
    k_xy = np.exp(-(np.subtract.outer(sample_x, sample_y)**2) / (2 * sigma**2))
    
    mmd_sq = np.mean(k_xx) - 2 * np.mean(k_xy) + np.mean(k_yy)
    return np.sqrt(max(mmd_sq, 0))

def apply_wk_means_refined(file_path, price_col='Close', date_col='Date', k=2, h1=35, h2=1):
    df = pd.read_csv(file_path)
    dates = pd.to_datetime(df[date_col], format='%d/%m/%Y')
    prices = df[price_col].values
    log_returns = np.diff(np.log(prices))
    
    # 1. Stream Lift (Phân đoạn dữ liệu) [11, 12]
    segments = []
    for i in range(0, len(log_returns) - h1 + 1, h2):
        segments.append(np.sort(log_returns[i : i + h1]))
    
    segments = np.array(segments)
    M = len(segments)
    
    # 2. WK-means Algorithm [13]
    np.random.seed(20) # Cố định seed để kết quả ổn định
    # np.random.seed(42) # Cố định seed để kết quả ổn định
    indices = np.random.choice(M, k, replace=False)
    centroids = segments[indices]
    labels = np.zeros(M)
    
    for _ in range(50):
        # Assignment step: dùng khoảng cách Wasserstein p=1 (Trung bình sai lệch tuyệt đối) [14]
        distances = np.array([[np.mean(np.abs(seg - c)) for c in centroids] for seg in segments])
        labels = np.argmin(distances, axis=1)
        
        # Update step: dùng Wasserstein Barycenter (Median cho p=1) [15]
        new_centroids = []
        for j in range(k):
            cluster_data = segments[labels == j]
            if len(cluster_data) > 0:
                new_centroids.append(np.median(cluster_data, axis=0))
            else:
                new_centroids.append(centroids[j])
        centroids = np.array(new_centroids)

    # 3. Tính toán xác suất Regime cho mỗi ngày (Soft Coloring logic) [6]
    # Mỗi ngày có thể thuộc nhiều cửa sổ, ta tính trung bình nhãn của chúng
    regime_probs = np.zeros(len(prices))
    counts = np.zeros(len(prices))
    
    for i, label in enumerate(labels):
        start_idx = i * h2
        regime_probs[start_idx : start_idx + h1] += label
        counts[start_idx : start_idx + h1] += 1
    
    # Tránh chia cho 0 và tính trung bình nhãn (0 đến 1)
    avg_labels = np.divide(regime_probs, counts, out=np.zeros_like(regime_probs), where=counts!=0)
    
    return dates, prices, avg_labels, labels, segments

# --- THỰC THI VÀ KIỂM CHỨNG ---
# h1=35 được khuyên dùng để hội tụ độ chính xác [7]
dates, prices, avg_labels, raw_labels, segments = apply_wk_means_refined("D:/PER_WORKSPACE/scan_document/media/data_kcn.csv", h1=35, h2=1)

# Tính toán MMD để kiểm tra độ tin cậy [5, 16]
cluster_0 = segments[raw_labels == 0]
cluster_1 = segments[raw_labels == 1]
if len(cluster_0) > 0 and len(cluster_1) > 0:
    # Lấy mẫu ngẫu nhiên 2 phân đoạn từ 2 cụm để so sánh
    mmd_val = calculate_mmd(cluster_0, cluster_1)
    print(f"MMD Between Clusters (Độ khác biệt): {mmd_val:.4f}")

# --- VẼ BIỂU ĐỒ THEO PHONG CÁCH FIGURE 2 [17] ---
plt.figure(figsize=(15, 8))
plt.plot(dates, prices, color='black', linewidth=1, label='Arabica Price', zorder=2)

# Tô màu mịn dựa trên avg_labels (Xanh -> Đỏ)
for i in range(len(dates)-1):
    # Pha trộn màu: 0.0 (Xanh lá) -> 1.0 (Đỏ)
    color_val = avg_labels[i]
    color = (color_val, 1-color_val, 0) # RGB: R tăng khi label tiến tới 1, G giảm
    plt.axvspan(dates[i], dates[i+1], color=color, alpha=0.3, linewidth=0)

plt.title('WK-Means: Market Regime Clustering for Arabica Coffee', fontsize=14)
ax = plt.gca()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
plt.grid(alpha=0.2)
plt.legend()
plt.show()