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
    plt.plot(X_smooth, Y_smooth, color='red', linewidth=2, label='Market Sentiment Trend')
    
    # Đánh dấu các điểm gốc
    plt.scatter(paragraphs, cumulative_scores, color='red', s=30, alpha=0.5)

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
    
    sim_lines = [] # Danh sách lưu các đối tượng line để bắt sự kiện
    for i in range(num_samples):
        perm = random.sample(list(scores), len(scores)) 
        cum_y = np.cumsum(perm)
        
        x_sim_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
        spl = make_interp_spline(x_axis, cum_y, k=3)
        y_sim_smooth = spl(x_sim_smooth)
        # Lưu đối tượng line vào list
        line, = ax.plot(x_sim_smooth, y_sim_smooth, color=colors[i], alpha=0.1, zorder=1)
        sim_lines.append(line)

    # 2. Vẽ "Main Narrative Curve" (Đường thực tế)
    x_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
    spl = make_interp_spline(x_axis, original_cum_y, k=3)
    y_smooth = spl(x_smooth)

    main_color = '#2ecc71' if original_cum_y[-1] >= 0 else '#e74c3c'
    main_line, = ax.plot(x_smooth, y_smooth, color=main_color, linewidth=4, 
                         label='Báo cáo Gốc (Main Path)', zorder=5)
    ax.scatter(x_axis, original_cum_y, color=main_color, s=60, edgecolors='white', zorder=6)

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
    ax.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.4)
    ax.set_title("Phân tích Quỹ đạo Động lượng", fontsize=14, fontweight='bold')
    ax.set_xlabel("Paragraph Index")
    ax.set_ylabel("Momentum Accumulation")
    ax.grid(True, which='both', linestyle=':', alpha=0.5)
    ax.legend(loc='upper left')
    
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
    paragraphs = np.array([item["paragraph_index"] if "paragraph_index" in item else item["sentence_index"] for item in report])
    
    # 2. Trích xuất Cumulative Y
    cumulative_scores = np.array([item["vector_field"]["cumulative_y"] for item in report])
    
    # 3. Trích xuất Y Momentum
    effective_momentum = [item["decay_metrics"]["effective_momentum"] for item in report]
    
    # C2: tự nhập array
    # effective_momentum = [0.248, -0.443, 0.428, -0.323, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.222, 1.332]
    print("====================================")
    print("effective_momentum:")
    print(effective_momentum)
    print("====================================")
    print(f"--- Đã trích xuất {len(paragraphs)} đoạn văn ---")
    print("====================================")
    
    # Gọi hàm vẽ 1
    # draw_vector_field_a(paragraphs, cumulative_scores)
    
    # Gọi hàm vẽ 2
    draw_vector_field_a_2(effective_momentum)

# --- CÁCH SỬ DỤNG ---
process_coffee_data(
    r"""
{
  "analysis_report": [
    {
      "original_index": 1,
      "paragraph_index": 1,
      "consumption_phase": "Opening",
      "paragraph_type": "semantic",
      "paragraph_sign": "neutral",
      "default_text": "Information as of July 27, 2026",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 1,
        "cumulative_y": 0.0,
        "direction_degree": 0.0
      }
    },
    {
      "original_index": 2,
      "paragraph_index": 2,
      "consumption_phase": "Opening",
      "paragraph_type": "price",
      "paragraph_sign": "neutral",
      "default_text": "HCM offers to buy at 95,000-96,000 / offers to sell at 98,000-99,000",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 2,
        "cumulative_y": 0.0,
        "direction_degree": 0.0
      }
    },
    {
      "original_index": 3,
      "paragraph_index": 3,
      "consumption_phase": "Opening",
      "paragraph_type": "price",
      "paragraph_sign": "neutral",
      "default_text": "R2 FOB, Bulk, T11 offers to buy at +20 / offers to sell at +100",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 3,
        "cumulative_y": 0.0,
        "direction_degree": 0.0
      }
    },
    {
      "original_index": 4,
      "paragraph_index": 4,
      "consumption_phase": "Opening",
      "paragraph_type": "price",
      "paragraph_sign": "neutral",
      "default_text": "Bulgarian pepper at 135-137,000 VND/Kg",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 4,
        "cumulative_y": 0.0,
        "direction_degree": 0.0
      }
    },
    {
      "original_index": 5,
      "paragraph_index": 5,
      "consumption_phase": "Mid-day",
      "paragraph_type": "price",
      "paragraph_sign": "neutral",
      "default_text": "Müc differentials offers to buy, R2 5%, Bag FOB HCM (USD/ton)",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 5,
        "cumulative_y": 0.0,
        "direction_degree": 0.0
      }
    },
    {
      "original_index": 6,
      "paragraph_index": 6,
      "consumption_phase": "Mid-day",
      "paragraph_type": "price",
      "paragraph_sign": "neutral",
      "default_text": "Bulk coffee price (VND/Kg): Buon Ma Thuot offers to buy at 94,000-95,000 / offers to sell at 97,000-98,000:",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 6,
        "cumulative_y": 0.0,
        "direction_degree": 0.0
      }
    },
    {
      "original_index": 7,
      "paragraph_index": 7,
      "consumption_phase": "Mid-day",
      "paragraph_type": "semantic",
      "paragraph_sign": "+",
      "default_text": "Coffee prices rose on Friday, thanks to short covering and technical bottom-fishing.",
      "decay_metrics": {
        "intrinsic_momentum": 0.3,
        "decay_factor": 0.05,
        "effective_momentum": 0.222
      },
      "vector_field": {
        "x": 7,
        "cumulative_y": 0.222,
        "direction_degree": 17.59
      }
    },
    {
      "original_index": 8,
      "paragraph_index": 8,
      "consumption_phase": "Afternoon",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "USDA forecasts global coffee production for the 2026/27 crop year will reach a record 189.7 million bags (+6%). Global consumption also reached a record 179.7 million bags, with a supply surplus of approximately 10 million bags. Brazil's production is projected at 71.9 million bags (+14%). Vietnam's production is over 32.5 million bags. Global ending inventories increased to 26.3 million bags.",
      "decay_metrics": {
        "intrinsic_momentum": -0.8,
        "decay_factor": 0.05,
        "effective_momentum": -1.332
      },
      "vector_field": {
        "x": 8,
        "cumulative_y": -1.11,
        "direction_degree": -7.89
      }
    },
    {
      "original_index": 9,
      "paragraph_index": 9,
      "consumption_phase": "Afternoon",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "According to the U.S. Trade Representative (USTR), Brazilian coffee (all varieties) is exempt from the new tariff order (10% - 12.5%). This helps alleviate concerns about disruptions to coffee exports from Brazil to the U.S.",
      "decay_metrics": {
        "intrinsic_momentum": -0.3,
        "decay_factor": 0.05,
        "effective_momentum": -0.248
      },
      "vector_field": {
        "x": 9,
        "cumulative_y": -1.358,
        "direction_degree": -8.58
      }
    },
    {
      "original_index": 10,
      "paragraph_index": 10,
      "consumption_phase": "Afternoon",
      "paragraph_type": "semantic",
      "paragraph_sign": "+",
      "default_text": "In July 2026, Brazilian exports are expected to exceed 3 million bags. The EU's implementation of the EUDR regulation from January 2027 may prompt trading companies to accelerate shipments between October and December 2026, potentially leading to container shortages and increased shipping costs.",
      "decay_metrics": {
        "intrinsic_momentum": 0.3,
        "decay_factor": 0.05,
        "effective_momentum": 0.443
      },
      "vector_field": {
        "x": 10,
        "cumulative_y": -0.915,
        "direction_degree": -5.23
      }
    },
    {
      "original_index": 11,
      "paragraph_index": 11,
      "consumption_phase": "Closing",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "In Brazil, Robusta/Conilon is almost harvested (90%-100%). Arabica is at about 60%-70% harvest.",
      "decay_metrics": {
        "intrinsic_momentum": -0.3,
        "decay_factor": 0.05,
        "effective_momentum": -0.428
      },
      "vector_field": {
        "x": 11,
        "cumulative_y": -1.343,
        "direction_degree": -6.97
      }
    },
    {
      "original_index": 12,
      "paragraph_index": 12,
      "consumption_phase": "Closing",
      "paragraph_type": "semantic",
      "paragraph_sign": "+",
      "default_text": "A cold snap brought rain to São Paulo, Sul de Minas, and Espírito Santo over the weekend, temporarily disrupting harvesting and drying. However, there is no risk of frost (temperatures remain above 15°C). Sunny weather is forecast to return next week.",
      "decay_metrics": {
        "intrinsic_momentum": 0.2,
        "decay_factor": 0.05,
        "effective_momentum": 0.323
      },
      "vector_field": {
        "x": 12,
        "cumulative_y": -1.02,
        "direction_degree": -4.86
      }
    }
  ],
  "market_summary": {
    "summary_all_blog_sign": "-",
    "total_effective_momentum": -1.02,
    "trend_trajectory": "Downward",
    "digestive_journey": "The market session opened neutral with local structural pricing. Mid-day technical short-covering provided a minor bullish bounce. However, the market encountered strong structural bearish pressure in the afternoon following USDA forecasts of a 10M bag global surplus, tariff exemptions for Brazilian coffee, and smooth harvest progression in Brazil. Despite minor late-session bullish offsets from logistics concerns and temporary rain disruptions, the overall market trajectory digested the overarching fundamental supply surplus, maintaining a downward bias."
  }
}
    """
)