import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

# 1. Điểm số của đoạn văn (AI phân tích) (cumulative_y)
paragraphs = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
cumulative_scores = np.array([0.0, -0.231, -0.188, -0.198, 0.0, 0.0, 0.0, 1.332, 0.329, 0.271, -0.488, -0.2]) 

# 2. Tạo đường cong mượt (Interpolation)
X_smooth = np.linspace(paragraphs.min(), paragraphs.max(), 300) 
spl = make_interp_spline(paragraphs, cumulative_scores, k=3)
Y_smooth = spl(X_smooth)

# 3. Vẽ biểu đồ
plt.figure(figsize=(10, 5))
plt.plot(X_smooth, Y_smooth, color='blue', linewidth=2, label='Market Sentiment Trend')

plt.title("Coffee Market Trajectory Analysis")
plt.xlabel("Report Progression (Paragraphs)")
plt.ylabel("Cumulative Momentum")
plt.grid(True, alpha=0.2)
plt.show()