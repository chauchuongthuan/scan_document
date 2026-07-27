from django.shortcuts import render
from google import genai
from django.http import JsonResponse
from django.views import View
import re
import os
import numpy as np
from scipy.stats import entropy
from datetime import datetime, timedelta
from .models import DailyMarketPrice
from .market_agent_utils import safe_float

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def information_geometry_system_prompt():
    """
    System prompt sử dụng Information Geometry từ Shun-ichi Amari's paper.
    Dựa trên dually flat manifolds, Bregman divergences, và Fisher-Rao metric.
    """
    return """
    You are an Information Geometry expert analyzing coffee market data using Shun-ichi Amari's framework from "Information Geometry of Positive Measures and Positive-Definite Matrices".

    ## CORE ANALYSIS FRAMEWORK (From the document):
    ### 1. Dually Flat Structure (α-β Divergences)
    - Manifold of positive measures Rn+ (prices, volumes as coordinates θ)
    - Dual affine coordinates: η = φ(θ), ψ = ψ(η) where φ,ψ are monotone functions
    - Canonical Bregman divergence: D[θ:θ'] = ψ(η_θ) + φ(θ'_ψ) - η_θ · θ'_ψ

    ### 2. Fisher Information Metric
    - Riemannian metric g_ij = E[∂log p/∂θ_i · ∂log p/∂θ_j] 
    - Measures "information curvature" of price distributions

    ### 3. Decomposable Divergences for Coffee Prices
    For Farm-Gate(m), Midstream(m), Differential($):
    D_αβ(P||Q) = ∑_components [φ(P_i) + ψ(Q_j) - φ'(P_i)·Q_j]

    - φ(θ) = θ^α/α, ψ(η) = η^β/β (power divergences from paper)

    ## YOUR TASK: Information-Geometric Market Analysis
    Given price data P_t (today) and P_{t-1} (yesterday), compute:

    ### 1. PARAGRAPH ANALYSIS (Each paragraph as a tangent vector)
    For paragraph n:

    θ_n = extract_price_measures(paragraph) # positive measures vector

    η_n = φ(θ_n) # α-representation (bullish coordinates)

    ψ_n = ψ(η_n) # β-representation (bearish coordinates)

    D_αβ(θ_t || θ_n) # divergence from today's prices

    ### 2. GEODESIC PROJECTION (Pythagorean Theorem)
    Market State S ⊂ manifold
    proj_S(θt) = argmin{q∈S} D(θ_t || q)
    If proj_S(θ_t) lies on η-geodesic → Bullish projection (+)
    If proj_S(θ_t) lies on ψ-geodesic → Bearish projection (-)

    ### 3. CLUSTER CENTER (Banerjee's Theorem)
    Cluster center R of N paragraphs: η_R = (1/N)∑η_i
    Convert back: θ_R = φ^{-1}(η_R)
    Compare θ_R vs θ_t → Market Consensus Signal

    ### 4. DUAL FLATNESS METRICS (From Amari's decomposable structure)
    Riemannian distance: ds^2 = g_ij dθ^i dθ^j = ∑ (d log θ_i)^2
    Curvature-free → Euclidean market geometry when flat

    ## JSON SCHEMA (Information Geometry Native)
    ```json
    {
    "information_geometry_analysis": [
        {
        "paragraph_index": n,
        "theta_measures": [farm_gate, midstream, differential],
        "eta_bullish": [η1, η2, η3], 
        "psi_bearish": [ψ1, ψ2, ψ3],
        "bregman_divergence": {
            "D_ab_today_vs_para": 0.123,
            "alpha": 1.0,  // KL divergence
            "beta": 0.5    // power divergence parameter
        },
        "geodesic_projection": "+ | - | neutral",
        "fisher_metric_det": 0.456,  // Market volatility measure
        "dually_flat_sign": "+ | -"
        }
    ],
    "market_manifold_summary": {
        "cluster_center_theta_R": [0.85, 0.92, -45],
        "total_bregman_div": 2.34,
        "riemannian_distance_today_vs_consensus": 0.67,
        "manifold_curvature": "flat | curved",
        "pythagorean_theorem_signal": "Bullish decomposition"
    }
    }
    ```

    ## RULES FROM DOCUMENT:
    1. **Decomposability**: Analyze each price component separately
    2. **Legendre Duality**: Bullish η ↔ Bearish ψ coordinates  
    3. **Pythagorean Theorem**: D(P:Q) + D(Q:R) = D(P:R) when orthogonal
    4. **No Heuristics**: Pure geometric computation

    CRITICAL: 
    1. Return ONLY valid JSON. Use mathematical precision from the Information Geometry framework. 
    2. TOTAL INTEGRITY: You must process EVERY paragraph provided.
    3. NO MERGING: Do not skip or combine paragraphs.
    """


def build_information_geometry_prompt(paragraphs, curr_prices, prev_prices, date_str):
    """
    Build prompt using dually flat structure from the document.
    """
    # Extract positive measures for Information Geometry manifold
    theta_today = np.array(
        [
            curr_prices.get("farm_gate_low", 0) or 1e-6,
            curr_prices.get("midstream_low", 0) or 1e-6,
            abs(curr_prices.get("differential_bid", 0)) or 1e-6,
        ]
    )

    theta_yesterday = np.zeros(3)
    if prev_prices:
        theta_yesterday = np.array(
            [
                prev_prices.farm_gate_low or 1e-6,
                prev_prices.midstream_low or 1e-6,
                abs(prev_prices.differential_bid or 1e-6),
            ]
        )

    # α-β transformation functions (from Amari's paper)
    def phi_alpha(theta, alpha=1.0):
        return theta**alpha / alpha if alpha != 0 else np.log(theta)

    def psi_beta(eta, beta=0.5):
        return eta**beta / beta if beta != 0 else np.exp(eta)

    eta_today = phi_alpha(theta_today)
    psi_today = psi_beta(eta_today)
    ig_context = information_geometry_system_prompt()
    ig_context += f"""
Date: {date_str}
## DUAL COORDINATE SYSTEMS (Amari 2014)
### θ-space (Positive Measures - Raw Prices)
Today: θ_t = [{theta_today[0]:.2f}, {theta_today[1]:.2f}, {theta_today[2]:.2f}]
Yesterday: θ_t-1 = [{theta_yesterday[0]:.2f}, {theta_yesterday[1]:.2f}, {theta_yesterday[2]:.2f}]

### η-space (α=1.0 Bullish Coordinates)  
η_t = φ(θ_t) = [{eta_today[0]:.4f}, {eta_today[1]:.4f}, {eta_today[2]:.4f}]

### ψ-space (β=0.5 Bearish Coordinates)
ψ_t = ψ(η_t) = [{psi_today[0]:.4f}, {psi_today[1]:.4f}, {psi_today[2]:.4f}]

## PARAGRAPHS (Tangent Vectors on Manifold)
"""

    for idx, para in enumerate(paragraphs, 1):
        ig_context += f"\n--- Paragraph {idx} ---\n{para}\n"

    ig_context += """
ANALYZE using the Information Geometry framework above.
Compute divergences, projections, cluster centers EXACTLY as specified.
    """

    return ig_context


class InformationGeometryAnalyzerView(View):
    def post(request):
        if request.method == "POST":
            try:
                text = request.POST.get("paragraph", "")
                date_str = request.POST.get("date", "")
                curr_prices = {
                    "farm_gate_low": safe_float(
                        request.POST.get("farm_gate_low", None)
                    ),
                    "farm_gate_high": safe_float(
                        request.POST.get("farm_gate_high", None)
                    ),
                    "midstream_low": safe_float(
                        request.POST.get("midstream_low", None)
                    ),
                    "midstream_high": safe_float(
                        request.POST.get("midstream_high", None)
                    ),
                    "differential_ask": safe_float(
                        request.POST.get("differential_ask", None)
                    ),
                    "differential_bid": safe_float(
                        request.POST.get("differential_bid", None)
                    ),
                }

                prev_prices = None
                for i in range(1, 5):
                    try:
                        prev_prices = DailyMarketPrice.objects.get(
                            date=datetime.fromisoformat(date_str).date()
                            - timedelta(days=i)
                        )
                        break
                    except DailyMarketPrice.DoesNotExist:
                        continue

                # Save current prices (unchanged logic)
                if any(v is not None for v in curr_prices.values()):
                    DailyMarketPrice.objects.update_or_create(
                        date=datetime.fromisoformat(date_str).date(),
                        defaults=curr_prices,
                    )

                if not text or len(text.strip()) < 5:
                    return JsonResponse(
                        {"status": "error", "message": "No valid text input."},
                        status=400,
                    )
                if not date_str:
                    return JsonResponse(
                        {"status": "error", "message": "Missing 'date' field."},
                        status=400,
                    )

                paragraphs = [
                    p.strip() for p in re.split(r"\n{1,}", text) if len(p.strip()) > 0
                ]

                # Build Information Geometry prompt
                ig_prompt = build_information_geometry_prompt(
                    paragraphs, curr_prices, prev_prices, date_str
                )

                # Generate response
                # response = client.models.generate_content(
                #     model="gemini-2.5-flash",
                #     contents=ig_prompt,
                # )

                return JsonResponse({
                    "status": "success",
                    "message": "Processed successfully",
                    "result": {
                        "ai_response": "", # Tab 1
                        "prompt_used": ig_prompt # Tab 2
                    }
                }, status=200)

            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, "market-agent/create-prompt-3.html")
