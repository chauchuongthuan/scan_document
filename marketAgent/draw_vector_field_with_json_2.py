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

    print("====================================")
    print("chunk y_momentum:")
    print(y_momentum)
    print("====================================")
    print(f"--- Đã trích xuất {len(paragraphs)} đoạn văn ---")
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
    "Midstream & Local Trade",
    "Export & FOB Dynamics",
    "Supply & Farmer Psychology",
    "Global Macro & Geopolitics",
    "Agronomy & Weather",
    "Local Logistics & Energy"
  ],
  "analysis_report": [
    {
      "index": 1,
      "text": "Information as of July 27, 2026",
      "parent_layer": "Global Macro & Geopolitics",
      "logical_connection": "Temporal baseline anchor for market reference.",
      "impact_sign": "neutral",
      "momentum": 0.0
    },
    {
      "index": 2,
      "text": "HCM offers to buy at 95,000-96,000 / offers to sell at 98,000-99,000",
      "parent_layer": "Midstream & Local Trade",
      "logical_connection": "Local price spread reflects wide bid-ask gaps and domestic market illiquidity.",
      "impact_sign": "-",
      "momentum": -0.15
    },
    {
      "index": 3,
      "text": "R2 FOB, Bulk, T11 offers to buy at +20 / offers to sell at +100",
      "parent_layer": "Export & FOB Dynamics",
      "logical_connection": "Wide differential spread indicates buyer-seller mismatch on forward export terms.",
      "impact_sign": "-",
      "momentum": -0.2
    },
    {
      "index": 4,
      "text": "Bulgarian pepper at 135-137,000 VND/Kg",
      "parent_layer": "Midstream & Local Trade",
      "logical_connection": "Cross-commodity price reference highlighting high alternative crop liquidity.",
      "impact_sign": "neutral",
      "momentum": 0.0
    },
    {
      "index": 5,
      "text": "Müc differentials offers to buy, R2 5%, Bag FOB HCM (USD/ton)",
      "parent_layer": "Export & FOB Dynamics",
      "logical_connection": "Categorical baseline for physical export differential pricing.",
      "impact_sign": "neutral",
      "momentum": 0.0
    },
    {
      "index": 6,
      "text": "Bulk coffee price (VND/Kg): Buon Ma Thuot offers to buy at 94,000-95,000 / offers to sell at 97,000-98,000",
      "parent_layer": "Midstream & Local Trade",
      "logical_connection": "Origin physical market pricing showing wide bid-ask spread and price consolidation.",
      "impact_sign": "-",
      "momentum": -0.15
    },
    {
      "index": 7,
      "text": "Coffee prices rose on Friday, thanks to short covering and technical bottom-fishing.",
      "parent_layer": "Global Macro & Geopolitics",
      "logical_connection": "Short-term technical bounce providing temporary price relief.",
      "impact_sign": "+",
      "momentum": 0.35
    },
    {
      "index": 8,
      "text": "USDA forecasts global coffee production for the 2026/27 crop year will reach a record 189.7 million bags (+6%).",
      "parent_layer": "Supply & Farmer Psychology",
      "logical_connection": "Strong fundamental bearish driver from global production surge.",
      "impact_sign": "-",
      "momentum": -0.85
    },
    {
      "index": 9,
      "text": "Global consumption also reached a record 179.7 million bags,",
      "parent_layer": "Global Macro & Geopolitics",
      "logical_connection": "Demand growth partially offsetting supply surge.",
      "impact_sign": "+",
      "momentum": 0.3
    },
    {
      "index": 10,
      "text": "with a supply surplus of approximately 10 million bags.",
      "parent_layer": "Supply & Farmer Psychology",
      "logical_connection": "Heavy structural surplus placing long-term pressure on prices.",
      "impact_sign": "-",
      "momentum": -0.9
    },
    {
      "index": 11,
      "text": "Brazil's production is projected at 71.9 million bags (+14%).",
      "parent_layer": "Supply & Farmer Psychology",
      "logical_connection": "Massive supply addition from the top global producer.",
      "impact_sign": "-",
      "momentum": -0.85
    },
    {
      "index": 12,
      "text": "Vietnam's production is over 32.5 million bags.",
      "parent_layer": "Supply & Farmer Psychology",
      "logical_connection": "Stable Robusta supply anchor from key exporter.",
      "impact_sign": "-",
      "momentum": -0.4
    },
    {
      "index": 13,
      "text": "Global ending inventories increased to 26.3 million bags.",
      "parent_layer": "Supply & Farmer Psychology",
      "logical_connection": "Rebuilding buffer stock diminishes supply deficit fears.",
      "impact_sign": "-",
      "momentum": -0.75
    },
    {
      "index": 14,
      "text": "According to the U.S. Trade Representative (USTR), Brazilian coffee (all varieties) is exempt from the new tariff order (10% - 12.5%).",
      "parent_layer": "Global Macro & Geopolitics",
      "logical_connection": "Removal of tariff friction clears trade pathways for Brazilian coffee.",
      "impact_sign": "-",
      "momentum": -0.5
    },
    {
      "index": 15,
      "text": "This helps alleviate concerns about disruptions to coffee exports from Brazil to the U.S.",
      "parent_layer": "Export & FOB Dynamics",
      "logical_connection": "Smooth trade flow confirmation reduces risk premium.",
      "impact_sign": "-",
      "momentum": -0.4
    },
    {
      "index": 16,
      "text": "In July 2026, Brazilian exports are expected to exceed 3 million bags.",
      "parent_layer": "Export & FOB Dynamics",
      "logical_connection": "High physical flow flooding destination markets.",
      "impact_sign": "-",
      "momentum": -0.6
    },
    {
      "index": 17,
      "text": "The EU's implementation of the EUDR regulation from January 2027 may prompt trading companies to accelerate shipments between October and December 2026,",
      "parent_layer": "Global Macro & Geopolitics",
      "logical_connection": "Regulatory deadline inducing a near-term rush in trade volume.",
      "impact_sign": "+",
      "momentum": 0.45
    },
    {
      "index": 18,
      "text": "potentially leading to container shortages and increased shipping costs.",
      "parent_layer": "Local Logistics & Energy",
      "logical_connection": "Logistical bottlenecks create temporary bullish friction for spot availability.",
      "impact_sign": "+",
      "momentum": 0.55
    },
    {
      "index": 19,
      "text": "In Brazil, Robusta/Conilon is almost harvested (90%-100%).",
      "parent_layer": "Agronomy & Weather",
      "logical_connection": "Completion of Robusta harvest secures physical supply.",
      "impact_sign": "-",
      "momentum": -0.5
    },
    {
      "index": 20,
      "text": "Arabica is at about 60%-70% harvest.",
      "parent_layer": "Agronomy & Weather",
      "logical_connection": "Steady harvest progress maintains steady inflow into supply chains.",
      "impact_sign": "-",
      "momentum": -0.3
    },
    {
      "index": 21,
      "text": "A cold snap brought rain to São Paulo, Sul de Minas, and Espírito Santo over the weekend, temporarily disrupting harvesting and drying.",
      "parent_layer": "Agronomy & Weather",
      "logical_connection": "Minor weather delays trigger localized short-term bullish reactions.",
      "impact_sign": "+",
      "momentum": 0.35
    },
    {
      "index": 22,
      "text": "However, there is no risk of frost (temperatures remain above 15°C).",
      "parent_layer": "Agronomy & Weather",
      "logical_connection": "Absence of extreme weather premium caps upside potential.",
      "impact_sign": "-",
      "momentum": -0.6
    },
    {
      "index": 23,
      "text": "Sunny weather is forecast to return next week.",
      "parent_layer": "Agronomy & Weather",
      "logical_connection": "Quick recovery of harvest conditions reassures crop progress.",
      "impact_sign": "-",
      "momentum": -0.5
    }
  ],
  "overall_market_bias": "Strong Bearish (Driven by record global production projections, heavy 10M bag surplus, tariff exemptions for Brazil, and smooth harvest progress, despite minor logistics and short-covering bounces)"
}
    """
)
