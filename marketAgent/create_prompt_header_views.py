from django.shortcuts import render
from google import genai
from django.http import JsonResponse
from django.views import View
import re
import os
from datetime import datetime, timedelta
from .models import DailyMarketPrice
from .market_agent_utils import (
    safe_float,
    convert_json_string_to_object
)
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

class CreatePromptForEachHeaderView(View):
    def post(request):
        if request.method == 'POST':
            try:
                text = request.POST.get('paragraph', '')
                
                # Prepare price data for the prompt
                content = """
                    You are a professional financial analyst for the coffee commodity market. Your task is to analyze the daily report below.
                    You MUST follow the rules below and return a JSON CODE BLOCK, without any other text.

                    ANALYSIS RULES
                    1. By day, each day counts as one paragraph
                    2. Price Impact Sign (+ / - / neutral):
                        "price" Paragraphs: Compare Today vs. Yesterday. (+ if higher, - if lower).
                        "semantic" Paragraphs: + (Bullish - scarcity/high cost), - (Bearish - abundance/low cost).
                    3. Intrinsic Momentum Calculation:
                        Assign an intrinsic_momentum score between -1.0 and 1.0 based on the raw sentiment of the paragraph:
                        +0.7 to +1.0: Strong Bullish (Supply collapse, extreme weather).
                        +0.1 to +0.4: Weak Bullish (Slight delays, minor demand uptick).
                        0: Neutral/Structural.
                        -0.1 to -0.4: Weak Bearish (Normal harvest, slight surplus).
                        -0.7 to -1.0: Strong Bearish (Record bumper crop, demand collapse).
                    4. Beta Decay Principle (Time-Weighting):
                        Information loses its market impact as time progresses and newer data emerges. You must calculate the effective_momentum using a decay factor beta = 0.05.
                        Formula: M_{effective} = √(|M_{intrinsic}|^2 * (1 - beta)^(N - n))
                        * M_{effective} has the same sign as M_{intrinsic}
                        N: Total number of paragraphs in the report.
                        n: Current paragraph index.
                        beta: 0.05 (The absorption rate of information).
                        Logic: The final paragraph (n=N) retains 100% of its weight. The first paragraph (n=1) is the most decayed.
                    5. Market State Operator Logic (Non-commutative & Phase Transition):
                        Information as an Operator: Treat each paragraph as a mathematical operator acting on the current "Market State" vector. The result of $Paragraph(n)$ depends entirely on the state left by $Paragraph(n-1)$.
                        Non-commutative Phase Shift: If a paragraph introduces a "Trend Reversal" (e.g., from Bullish to Bearish), apply a Phase Shift factor of 1.5x to the intrinsic_momentum. The order $A \to B$ creates a different market "spectrum" than $B \to A$.
                        Spectral Density (Information Intensity): Instead of simple decay, calculate the "intensity" of a paragraph based on its technical density (numbers, specific locations like 'Dak Lak' or 'Minas Gerais', and crop dates). High-density paragraphs "resist" $beta$ decay and retain 20% more weight over $N$ steps.
                        The "Trace" Rule: The cumulative_momentum at paragraph $n$ must reflect the "trace" (the sum of eigenvalues) of all preceding information. If the sequence of paragraphs shows a narrowing volatility, reduce the effective_momentum of late-session noise by an additional 10%.
                    6. Algebraic Structure Layer (Lie, Clifford, Cayley‑Dickson Enhancement):
                        Purpose: Use abstract algebraic structures to model more deeply how the market "digests" information. The rules below REFINE the calculations of Intrinsic Momentum, Beta Decay, Phase Shift and Cumulative Momentum without altering the original formulas.
                        6.1 Lie Bracket for Non‑commutative Interaction:
                            - Treat each consecutive pair of paragraphs (n‑1, n) as two operators. Compute a metaphorical "Lie bracket": L = |impact of (A then B) – impact of (B then A)|.
                            - If L > 0.3 → the information has strong order dependence (news A appearing first creates a significantly different effect than if it appeared later). In this case:
                                * Increase the Phase Shift by an additional 0.2x (i.e., 1.7x instead of 1.5x) if a Trend Reversal is detected.
                                * If L > 0.6 (extreme surprise), multiply the current paragraph's intrinsic_momentum by an amplification factor of 1.2 (sharp reversal) or 0.8 (sharp weakening) after applying the Phase Shift, while preserving the sign.
                        6.2 Clifford Semantic Geometry:
                            - Construct an abstract vector space with principal axes: price, weather, supply‑demand, geopolitics, logistics.
                            - Represent each paragraph as a multivector in a Clifford algebra. The geometric product between consecutive paragraphs tells whether they are "in phase" (positive result) or "out of phase" (negative result).
                            - Application: If the current paragraph is out of phase with the immediately preceding paragraph (e.g., clearly bullish followed by clearly bearish), then the effective_momentum of the current paragraph is strengthened by 15% (the market reacts more violently to contradictory signals). If they are in phase, reduce effective_momentum by 10% (consensus information causes less movement).
                            - Paragraphs containing many specific place names and numbers (e.g., Dak Lak, 85,000 VND) are considered "grade‑1 vectors" with high Spectral Density → they automatically trigger the existing rule of retaining 20% more weight against decay (as per section 4).
                    7. Cumulative Momentum & Trajectory:
                        cumulative_momentum: The running sum of effective_momentum from paragraph 1 to n.
                        Differential Rule: An increase in the cumulative value (e.g., -0.80 to -0.50) is BULLISH (+). A decrease (e.g., -0.50 to -0.80) is BEARISH (-).
                        When computing cumulative_momentum in the reordered timeline, apply the Lie adjustment (5.1) and Clifford adjustment (5.2) to each consecutive pair, and simultaneously track the "dimensional" layer via Cayley‑Dickson thinking to assign the appropriate decay factor (5.3).

                    INPUT DATA (ANALYZE THIS)
                """
                content += text
                # Add the JSON structure
                content += """
                    CRITICAL CONSTRAINTS
                    TOTAL INTEGRITY: You must process EVERY paragraph provided.
                    NO MERGING: Do not skip or combine paragraphs.
                    JSON ONLY: No conversational filler.
                    RETURN THE JSON RESULT in the structure:
                    The "analysis_report" array MUST be sorted by the logical time of market consumption.
                    {
                        "analysis_report": [
                            {
                                "original_index": n,
                                "paragraph_index": n,
                                "paragraph_type": "price | semantic",
                                "paragraph_sign": "+ | - | neutral",
                                "default_text": "...",
                                "decay_metrics": {
                                    "intrinsic_momentum": 0.0,
                                    "decay_factor": 0.0,
                                    "effective_momentum": 0.0
                                },
                                "vector_field": {
                                    "x": n,
                                    "cumulative_y": 0.0,
                                    "direction_degree": 0.0
                                }
                            }
                        ],
                        "market_summary": {
                            "summary_all_blog_sign": "+ | -",
                            "total_effective_momentum": 0.0,
                            "trend_trajectory": "Upward | Downward | Sideways",
                            "digestive_journey": "Description of how the market sentiment evolved after applying Beta Decay."
                        }
                    }
                """
                # response = client.models.generate_content(
                #     model="gemini-2.5-flash",
                #     contents=content,
                # )
                return JsonResponse({
                    "status": "success",
                    "message": "Created successfully",
                    "result": {
                        # "ai_response": response.text,
                        "ai_response": "",
                        "prompt_used": content
                    }
                }, status=200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, 'market-agent/create-prompt-4.html')
