import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import random
import json

# import mplcursors


def draw_vector_field_a(paragraphs, cumulative_scores):
    """Vẽ biểu đồ xu hướng tích lũy (Market Sentiment Trend)"""
    X_smooth = np.linspace(paragraphs.min(), paragraphs.max(), 300)
    spl = make_interp_spline(paragraphs, cumulative_scores, k=3)
    Y_smooth = spl(X_smooth)

    plt.figure(figsize=(10, 5))
    plt.plot(
        X_smooth, Y_smooth, color="red", linewidth=2, label="Market Sentiment Trend"
    )

    # Đánh dấu các điểm gốc
    plt.scatter(paragraphs, cumulative_scores, color="red", s=30, alpha=0.5)

    plt.title("Coffee Market Trajectory Analysis (Cumulative)")
    plt.xlabel("Report Progression (Paragraphs)")
    plt.ylabel("Cumulative Momentum")
    plt.grid(True, alpha=0.2)
    plt.legend()
    plt.show()


def draw_vector_field_a_2(scores):
    """Vẽ biểu đồ với hiệu ứng Highlight khi di chuột vào từng đường kịch bản"""
    n = len(scores)
    x_axis = np.arange(1, n + 1)
    original_cum_y = np.cumsum(scores)

    fig, ax = plt.subplots(figsize=(12, 7))

    # 1. Vẽ các đường mô phỏng
    num_samples = 200
    colors = plt.cm.jet(np.linspace(0, 1, num_samples))

    sim_lines = []  # Danh sách lưu các đối tượng line để bắt sự kiện
    for i in range(num_samples):
        perm = random.sample(list(scores), len(scores))
        cum_y = np.cumsum(perm)

        x_sim_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
        spl = make_interp_spline(x_axis, cum_y, k=3)
        y_sim_smooth = spl(x_sim_smooth)
        # Lưu đối tượng line vào list
        (line,) = ax.plot(
            x_sim_smooth, y_sim_smooth, color=colors[i], alpha=0.1, zorder=1
        )
        sim_lines.append(line)

    # 2. Vẽ "Main Narrative Curve" (Đường thực tế)
    x_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
    spl = make_interp_spline(x_axis, original_cum_y, k=3)
    y_smooth = spl(x_smooth)

    main_color = "#2ecc71" if original_cum_y[-1] >= 0 else "#e74c3c"
    (main_line,) = ax.plot(
        x_smooth,
        y_smooth,
        color=main_color,
        linewidth=4,
        label="Báo cáo Gốc (Main Path)",
        zorder=5,
    )
    ax.scatter(
        x_axis, original_cum_y, color=main_color, s=60, edgecolors="white", zorder=6
    )

    # --- LOGIC INTERACTIVE (HIGHLIGHT) ---
    # cursor = mplcursors.cursor(sim_lines, hover=True)

    # @cursor.connect("add")
    # def on_add(sel):
    #     # Khi chuột trỏ vào một đường:
    #     # 1. Làm nổi bật đường đó
    #     sel.artist.set_alpha(1.0)
    #     sel.artist.set_linewidth(2.5)
    #     # 2. Hiển thị tooltip tùy chỉnh (nếu muốn)
    #     sel.annotation.set_text(f"Simulation Path")
    #     sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

    # @cursor.connect("remove")
    # def on_remove(sel):
    #     # Khi chuột rời đi: Trả lại trạng thái mờ như cũ
    #     sel.artist.set_alpha(0.1)
    #     sel.artist.set_linewidth(1)

    # --- CÁC THIẾT LẬP KHÁC ---
    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.4)
    ax.set_title("Phân tích Quỹ đạo Động lượng", fontsize=14, fontweight="bold")
    ax.set_xlabel("Paragraph Index")
    ax.set_ylabel("Momentum Accumulation")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend(loc="upper left")

    plt.show()


def process_coffee_data(json_input):
    """
    Hàm chính: Nhận JSON, trích xuất dữ liệu và gọi 2 hàm vẽ biểu đồ.
    """
    # Nếu input là string, chuyển thành dict
    if isinstance(json_input, str):
        data = json.loads(json_input)
    else:
        data = json_input

    report = data.get("analysis_report", [])

    # 1. Trích xuất Paragraph Index
    paragraphs = np.array([item["index"] for item in report])

    # 3. Trích xuất Y Momentum
    y_momentum = [item["momentum"] for item in report]
    # y_momentum = [0.25, 0.35, 0.2, 0.8, 0.75, 0.4, 0.65, 0.85, 0.9, -0.75, 0.7, 0.88, 0.35, -0.45, -0.6, 0.55, 0.65, 0.5, -0.3, -0.4, 0.6, 0.7, -0.3, -0.4, 0.3, -0.5, -0.2, 0.8, 0.75, 0.85, 0.5, -0.3, 0.6, 0.4, 0.8, 0.85, -0.4]

    print("====================================")
    print("chunk y_momentum:")
    print(y_momentum)
    print("====================================")
    print(f"--- Đã trích xuất {len(y_momentum)} đoạn văn ---")
    print("====================================")

    # Gọi hàm vẽ 1
    # draw_vector_field_a(paragraphs, cumulative_scores)

    # Gọi hàm vẽ 2
    draw_vector_field_a_2(y_momentum)


# --- CÁCH SỬ DỤNG ---
process_coffee_data(
    r"""
{
  "semantic_layers_found": [
    "Agronomy & Weather (Nông học & Thời tiết)",
    "Supply & Farmer Psychology (Nguồn cung & Tâm lý nông dân)",
    "Midstream & Local Trade (Thương mại nội địa)"
  ],
  "analysis_report": [
    {
      "index": 1,
      "text": "Yesterday night and today's morning we have heard of circulating false narratives and rumors alledging a 'widespread flash flood in Lam Dong' affecting coffee plantations areas.",
      "parent_layer": "Supply & Farmer Psychology (Nguồn cung & Tâm lý nông dân)",
      "logical_connection": "False panic creates temporary bullish speculative sentiment in the market.",
      "impact_sign": "+",
      "momentum": 0.3
    },
    {
      "index": 2,
      "text": "Official reports from the Lam Dong Local Government Committee confirm that the impact of the 8th to 10th September weather event is strictly localised in South Gia Nghia, valley areas of Gia Nghia, and clusters around Dak R'mang of Ta Dung and not Lam Dong in general.",
      "parent_layer": "Agronomy & Weather (Nông học & Thời tiết)",
      "logical_connection": "Clarification of physical scope reverses false panic sentiment, introducing market stabilization.",
      "impact_sign": "-",
      "momentum": -0.4
    },
    {
      "index": 3,
      "text": "Total economic damage province-wide stands at a minor 3 billion VND, primarily driven by small-scale road erosion.",
      "parent_layer": "Midstream & Local Trade (Thương mại nội địa)",
      "logical_connection": "Negligible economic loss indicates near-zero disruption to local supply chain infrastructure.",
      "impact_sign": "-",
      "momentum": -0.2
    },
    {
      "index": 4,
      "text": "Across all sectors, only 14.4 hectares of mixed crops (mostly short-term vegetables and fruits) experienced temporary waterlogging.",
      "parent_layer": "Agronomy & Weather (Nông học & Thời tiết)",
      "logical_connection": "Minimal overall agricultural impact confirms absence of widespread crop destruction.",
      "impact_sign": "-",
      "momentum": -0.3
    },
    {
      "index": 5,
      "text": "There is ZERO reported wide-scale or hectare-based damage to coffee plantations thus far.",
      "parent_layer": "Agronomy & Weather (Nông học & Thời tiết)",
      "logical_connection": "Direct debunking of coffee supply damage removes supply threat risk completely.",
      "impact_sign": "-",
      "momentum": -0.8
    },
    {
      "index": 6,
      "text": "Severe water levels were restricted to low-lying residential clusters and riverbanks along the Dak Nong stream (Nam Gia Nghia ward), the lower basin of the Gia Nghia reservoir, and Dak R'mang village (Ta Dung).",
      "parent_layer": "Agronomy & Weather (Nông học & Thời tiết)",
      "logical_connection": "Flooding geography confirms residential/valley impact rather than agricultural elevated zones.",
      "impact_sign": "neutral",
      "momentum": 0.0
    },
    {
      "index": 7,
      "text": "These are valley-bottom living areas, not the slope and hillside ridges where coffee is grown in Dak Nong.",
      "parent_layer": "Agronomy & Weather (Nông học & Thời tiết)",
      "logical_connection": "Topographical protection isolates coffee crops from valley flooding risks.",
      "impact_sign": "-",
      "momentum": -0.5
    },
    {
      "index": 8,
      "text": "Additionally, the flooded zones are near the Moi stream are located in Suoi Kiet commune, which is a dry coastal eco-zone that produces rubber and cashew not coffee.",
      "parent_layer": "Agronomy & Weather (Nông học & Thời tiết)",
      "logical_connection": "Crop non-relevance eliminates any secondary supply concerns for coffee.",
      "impact_sign": "-",
      "momentum": -0.3
    },
    {
      "index": 9,
      "text": "Over 100,000 hectares of the region's coffee spanning from Lam Ha of Lam Dong, Dak Mil, Dam Rong, Quang Son, and Quang Tin, remain entirely secure, operational, and unaffected by the flash flood caused by rainfall.",
      "parent_layer": "Agronomy & Weather (Nông học & Thời tiết)",
      "logical_connection": "High-density confirmation of massive production safety solidifies strong bearish normalization of prices.",
      "impact_sign": "-",
      "momentum": -0.9
    },
    {
      "index": 10,
      "text": "The main affected areas are local housing within the valley trough and near river banks.",
      "parent_layer": "Supply & Farmer Psychology (Nguồn cung & Tâm lý nông dân)",
      "logical_connection": "Final reiteration reinforces that coffee infrastructure and supply remain fully intact.",
      "impact_sign": "-",
      "momentum": -0.2
    }
  ],
  "overall_market_bias": "Bearish / Neutralizing Bullish Speculation (Supply Unaffected)"
}
    """
)
