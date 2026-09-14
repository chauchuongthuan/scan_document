import json
import random
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline


def get_spline_degree(num_points):
    """Xác định bậc k an toàn dựa trên số lượng điểm dữ liệu"""
    return min(3, max(1, num_points - 1))


def draw_vector_field_a(paragraphs, cumulative_scores):
    """Vẽ biểu đồ xu hướng tích lũy (Market Sentiment Trend)"""
    n = len(paragraphs)
    if n == 0:
        return

    plt.figure(figsize=(10, 5))

    if n > 1:
        k_degree = get_spline_degree(n)
        X_smooth = np.linspace(paragraphs.min(), paragraphs.max(), 300)
        spl = make_interp_spline(paragraphs, cumulative_scores, k=k_degree)
        Y_smooth = spl(X_smooth)
        plt.plot(
            X_smooth,
            Y_smooth,
            color="red",
            linewidth=2,
            label="Market Sentiment Trend",
        )
    else:
        plt.plot(
            paragraphs,
            cumulative_scores,
            color="red",
            linewidth=2,
            label="Market Sentiment Trend",
        )

    plt.scatter(paragraphs, cumulative_scores, color="red", s=30, alpha=0.5)
    plt.title("Coffee Market Trajectory Analysis (Cumulative)")
    plt.xlabel("Report Progression (Paragraphs)")
    plt.ylabel("Cumulative Momentum")
    plt.grid(True, alpha=0.2)
    plt.legend()
    plt.show()


def draw_vector_field_a_2(scores):
    """Vẽ biểu đồ với hiệu ứng mô phỏng các kịch bản"""
    n = len(scores)
    if n == 0:
        return

    x_axis = np.arange(1, n + 1)
    original_cum_y = np.cumsum(scores)

    fig, ax = plt.subplots(figsize=(12, 7))

    # Tính bậc k an toàn cho tập dữ liệu hiện tại
    k_degree = get_spline_degree(n)

    # 1. Vẽ các đường mô phỏng
    num_samples = 200
    colors = plt.cm.jet(np.linspace(0, 1, num_samples))

    for i in range(num_samples):
        perm = random.sample(list(scores), len(scores))
        cum_y = np.cumsum(perm)

        if n > 1:
            x_sim_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
            spl = make_interp_spline(x_axis, cum_y, k=k_degree)
            y_sim_smooth = spl(x_sim_smooth)
        else:
            x_sim_smooth, y_sim_smooth = x_axis, cum_y

        ax.plot(
            x_sim_smooth, y_sim_smooth, color=colors[i], alpha=0.1, zorder=1
        )

    # 2. Vẽ "Main Narrative Curve" (Đường thực tế)
    if n > 1:
        x_smooth = np.linspace(x_axis.min(), x_axis.max(), 300)
        # Sử dụng k_degree hoặc k=1 tùy nhu cầu
        spl = make_interp_spline(x_axis, original_cum_y, k=k_degree)
        y_smooth = spl(x_smooth)
    else:
        x_smooth, y_smooth = x_axis, original_cum_y

    main_color = "#2ecc71" if original_cum_y[-1] >= 0 else "#e74c3c"
    ax.plot(
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

    # Thiết lập giao diện
    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.4)
    ax.set_title("Phân tích Quỹ đạo Động lượng", fontsize=14, fontweight="bold")
    ax.set_xlabel("Paragraph Index")
    ax.set_ylabel("Momentum Accumulation")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend(loc="upper left")

    plt.show()


def process_coffee_data(json_input):
    """Hàm xử lý JSON và gọi biểu đồ"""
    data = json.loads(json_input) if isinstance(json_input, str) else json_input
    report = data.get("analysis_report", [])

    if not report:
        print("Không có dữ liệu báo cáo.")
        return

    # Trích xuất dữ liệu động từ JSON
    paragraphs = np.array(
        [
            item.get("paragraph_index", item.get("sentence_index", idx + 1))
            for idx, item in enumerate(report)
        ]
    )
    cumulative_scores = np.array(
        [item["vector_field"]["cumulative_y"] for item in report]
    )

    # Trích xuất effective_momentum tự động thay vì hardcode
    effective_momentum = [
        item["decay_metrics"]["effective_momentum"] for item in report
    ]

    print("====================================")
    print(f"--- Đã trích xuất {len(effective_momentum)} đoạn văn ---")
    print(effective_momentum)
    print("====================================")
    
    # Gọi hàm vẽ
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
      "default_text": "*MARKET SYNOPSIS*",
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
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "*Debunking Misinformation*: _Localized Flooding Poses Zero Threat to Coffee Supply in Lam Dong_",
      "decay_metrics": {
        "intrinsic_momentum": -0.3,
        "decay_factor": 0.05,
        "effective_momentum": -0.2505
      },
      "vector_field": {
        "x": 2,
        "cumulative_y": -0.2505,
        "direction_degree": 230.17
      }
    },
    {
      "original_index": 3,
      "paragraph_index": 3,
      "consumption_phase": "Opening",
      "paragraph_type": "semantic",
      "paragraph_sign": "neutral",
      "default_text": "*1.Market Context & False Rumors*",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 3,
        "cumulative_y": -0.2505,
        "direction_degree": 180.0
      }
    },
    {
      "original_index": 4,
      "paragraph_index": 4,
      "consumption_phase": "Mid-day",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "*The Situation*: Yesterday night and today's morning we have heard of circulating false narratives and rumors alledging a \"widespread flash flood in *Lam Dong*\" affecting coffee plantations areas.",
      "decay_metrics": {
        "intrinsic_momentum": -0.2,
        "decay_factor": 0.05,
        "effective_momentum": -0.1741
      },
      "vector_field": {
        "x": 4,
        "cumulative_y": -0.4246,
        "direction_degree": 223.36
      }
    },
    {
      "original_index": 5,
      "paragraph_index": 5,
      "consumption_phase": "Mid-day",
      "paragraph_type": "semantic",
      "paragraph_sign": "neutral",
      "default_text": "2.*Verified Local Government Data & On-the-Ground Reality (As of September 11, 2026)*",
      "decay_metrics": {
        "intrinsic_momentum": 0.0,
        "decay_factor": 0.05,
        "effective_momentum": 0.0
      },
      "vector_field": {
        "x": 5,
        "cumulative_y": -0.4246,
        "direction_degree": 180.0
      }
    },
    {
      "original_index": 6,
      "paragraph_index": 6,
      "consumption_phase": "Afternoon",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "Official reports from the Lam Dong Local Government Committee confirm that the impact of the 8th to 10th September weather event is strictly localised in South Gia Nghia, valley areas of Gia Nghia, and clusters around Dak R'mang of Ta Dung and not Lam Dong in general.",
      "decay_metrics": {
        "intrinsic_momentum": -0.3,
        "decay_factor": 0.05,
        "effective_momentum": -0.2769
      },
      "vector_field": {
        "x": 6,
        "cumulative_y": -0.7015,
        "direction_degree": 229.4
      }
    },
    {
      "original_index": 7,
      "paragraph_index": 7,
      "consumption_phase": "Afternoon",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "*Financial & Crop Impact*: Total economic damage province-wide stands at a minor 3 billion VND, primarily driven by small-scale road erosion. Across all sectors, only 14.4 hectares of mixed crops (mostly short-term vegetables and fruits) experienced temporary waterlogging. There is ZERO reported wide-scale or hectare-based damage to coffee plantations thus far.",
      "decay_metrics": {
        "intrinsic_momentum": -0.4,
        "decay_factor": 0.05,
        "effective_momentum": -0.4431
      },
      "vector_field": {
        "x": 7,
        "cumulative_y": -1.1446,
        "direction_degree": 232.31
      }
    },
    {
      "original_index": 8,
      "paragraph_index": 8,
      "consumption_phase": "Closing",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "*Flood Mapping*: Severe water levels were restricted to low-lying residential clusters and riverbanks along the Dak Nong stream (Nam Gia Nghia ward), the lower basin of the Gia Nghia reservoir, and Dak R'mang village (Ta Dung). These are valley-bottom living areas, not the slope and hillside ridges where coffee is grown in Dak Nong. Additionally, the flooded zones are near the Moi stream are located in Suoi Kiet commune, which is a dry coastal eco-zone that produces rubber and cashew not coffee.",
      "decay_metrics": {
        "intrinsic_momentum": -0.35,
        "decay_factor": 0.05,
        "effective_momentum": -0.4093
      },
      "vector_field": {
        "x": 8,
        "cumulative_y": -1.5539,
        "direction_degree": 227.12
      }
    },
    {
      "original_index": 9,
      "paragraph_index": 9,
      "consumption_phase": "Closing",
      "paragraph_type": "semantic",
      "paragraph_sign": "-",
      "default_text": "*Core Coffee Production Area of Dak Nong is Safe*: Over 100,000 hectares of the region's coffee spanning from Lam Ha of Lam Dong, Dak Mil, Dam Rong, Quang Son, and Quang Tin, remain entirely secure, operational, and unaffected by the flash flood caused by rainfall. The main affected areas are local housing within the valley trough and near river banks.",
      "decay_metrics": {
        "intrinsic_momentum": -0.4,
        "decay_factor": 0.05,
        "effective_momentum": -0.48
      },
      "vector_field": {
        "x": 9,
        "cumulative_y": -2.0339,
        "direction_degree": 230.19
      }
    }
  ],
  "market_summary": {
    "summary_all_blog_sign": "-",
    "total_effective_momentum": -2.0339,
    "trend_trajectory": "Downward",
    "digestive_journey": "The report systematically dismantles bullish rumors of supply disruption caused by flash floods in Lam Dong and Dak Nong. Starting with initial debunking, early paragraph decay was moderated by high spectral density (specific locations and damage data). As official government data confirms zero coffee crop damage across over 100,000 hectares, bearish sentiment accumulates steadily through the session, driving total effective momentum downward to -2.0339."
  }
}
    """
)