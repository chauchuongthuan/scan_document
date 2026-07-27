import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import random

# 1. Dữ liệu Động lượng (y_momentum)
# scores = [0.65, 0.95, 0.88, 0.75, 0.92, 0.55, 0, -0.85, 0, 0, 0.82, -0.9, -0.7, 0.78]
scores = [-0.4, 0.0, 0.69, 0.8, 0.85, -0.2, -0.15, 0.75, -0.5, 0.0, 0.8, 0.9, -0.3, 0.5, 0.6]

scores = sorted(scores, reverse=True)

print("sort:::", scores)
n = len(scores)
x_axis = np.arange(1, n + 1)

plt.figure(figsize=(12, 7))

# 2. KHẮC PHỤC: Thay vì tạo list 480 triệu phần tử, ta chỉ tạo 200 mẫu ngẫu nhiên
num_samples = 200
for _ in range(num_samples):
    # Trộn ngẫu nhiên bản sao của scores
    perm = random.sample(scores, len(scores)) 
    cum_y = np.cumsum(perm)
    plt.plot(x_axis, cum_y, color='gray', alpha=0.1, linewidth=1)

# 3. Vẽ "Main Narrative Curve" (Giữ nguyên phần này)
original_cum_y = np.cumsum(scores)
x_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
spl = make_interp_spline(x_axis, original_cum_y, k=3)
y_smooth = spl(x_smooth)

main_color = '#2ecc71' if original_cum_y[-1] >= 0 else '#e74c3c'
plt.plot(x_smooth, y_smooth, color=main_color, linewidth=4, label='Báo cáo Gốc (Main Path)', zorder=5)
plt.scatter(x_axis, original_cum_y, color=main_color, s=60, edgecolors='white', zorder=6)

# ... (Các phần trang trí còn lại giữ nguyên)
plt.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.4)
plt.title("Phân tích Quỹ đạo Động lượng Thị trường Coffee", fontsize=14, fontweight='bold')
plt.grid(True, which='both', linestyle=':', alpha=0.5)
plt.legend(loc='upper left')
plt.show()