import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

# 1. Dữ liệu từ AI (Đã bao gồm cả Sentiment + Stock Bias trong y_momentum)
paragraphs = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])

# Giả sử nội dung tích cực nhưng Stock tăng (Bearish) kéo đường cong xuống thấp hơn thực tế tâm lý
# y_momentum này được lấy từ kết quả AI xử lý
# y_momentums = np.array([ 0.271, -0.488, -0.2, 0.0, -0.231, -0.188, -0.198, 0.0, 0.0, 0.0, 1.332, 0.329])
# y_momentums = np.array([0.248, -0.443, 0.428, -0.323, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.222, 1.332])
y_momentums = np.array([0.75, 0.5, 0.4, 0.6, -0.45, -0.55, 0.5, 0.3, -0.35, 0.6, 0.5, 0.0, 0.15, 0.2, 0.0, 0.0, 0.15, -0.35, 0.85, -0.3, 0.9, 0.85, 0.4])
cumulative_scores = np.cumsum(y_momentums)

# 2. Tạo đường cong mượt
X_smooth = np.linspace(paragraphs.min(), paragraphs.max(), 300) 
spl = make_interp_spline(paragraphs, cumulative_scores, k=3)
Y_smooth = spl(X_smooth)

# 3. Vẽ biểu đồ
plt.figure(figsize=(10, 5))
plt.plot(X_smooth, Y_smooth, color='#e67e22', linewidth=3, label='Adjusted Market')

# Thêm đường 0 để dễ quan sát âm/dương
plt.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.5)

plt.title("Coffee Market Trajectory Analysis")
plt.xlabel("Report Progression (Paragraphs)")
plt.ylabel("Adjusted Cumulative Momentum")
plt.grid(True, alpha=0.2)
plt.legend()
plt.show()