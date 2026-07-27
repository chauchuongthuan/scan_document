import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from itertools import permutations
import random

# 1. Dữ liệu y_momentum đã được AI điều chỉnh (Text + Stock Bias)
scores = [0.0, -0.231, -0.188, -0.198, 0.0, 0.0, 0.0, 1.332, 0.329, 0.271, -0.488, -0.2]
n = len(scores)
x_axis = np.arange(1, n + 1)


plt.figure(figsize=(12, 7))

# 2. Vẽ đám mây biến động
all_perms = list(permutations(scores))
if len(all_perms) > 200:
    all_perms = random.sample(all_perms, 200)

for perm in all_perms:
    cum_y = np.cumsum(perm)
    plt.plot(x_axis, cum_y, color='gray', alpha=0.03, linewidth=0.8)

# 3. Vẽ đường dẫn chính (Đường AI trả về theo thứ tự báo cáo)
original_cum_y = np.cumsum(scores)
x_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
spl = make_interp_spline(x_axis, original_cum_y, k=3)
y_smooth = spl(x_smooth)

main_color = '#2ecc71' if original_cum_y[-1] >= 0 else '#e74c3c'

plt.plot(x_smooth, y_smooth, color=main_color, linewidth=4, label='Báo cáo Gốc (Adjusted Path)', zorder=5)
plt.scatter(x_axis, original_cum_y, color=main_color, s=60, edgecolors='white', zorder=6)

# 4. Trang trí
plt.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.4)
plt.title("Phân tích Động lượng Thị trường (Sentiment & Macro Adjustment)", fontsize=14, fontweight='bold')
plt.xlabel("Tiến trình Báo cáo", fontsize=12)
plt.ylabel("Động lượng Tích lũy", fontsize=12)
plt.grid(True, which='both', linestyle=':', alpha=0.5)
plt.legend(loc='upper left')

plt.fill_between(x_smooth, y_smooth, 0, color=main_color, alpha=0.1)

plt.show()