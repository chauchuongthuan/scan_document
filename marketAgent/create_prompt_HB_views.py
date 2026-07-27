from django.shortcuts import render
from google import genai
from django.http import JsonResponse
from django.views import View
import re
import os
from datetime import datetime, timedelta
from .models import DailyMarketPrice
import nltk
from nltk.tokenize import sent_tokenize
import json
import numpy as np
from .market_agent_utils import (
    safe_float,
    convert_json_string_to_object
)
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

def build_system_prompt():
    """
    System Prompt: Defines the Marketing Expert persona and analysis rules.
    """
    return """
    You are a world-class Marketing Strategist and Content Writer specializing in digital psychology and conversion rate optimization (CRO) across social media platforms (Facebook, TikTok, Instagram, LinkedIn).

    Your ONLY task is to analyze social media posts and determine their impact sign (+, -, or neutral) regarding revenue growth and customer attraction.

    ## Your Analysis Rules:

    ### Impact Sign (+ / - / neutral)
    - `+` (Bullish/High Conversion): The content is highly likely to drive sales, capture leads, or significantly increase brand desire. 
      (e.g., Strong Hook, clear Pain Point solution, high benefit-driven language, clear CTA, urgency).
    - `-` (Bearish/Low Performance): The content is likely to be ignored, waste budget, or damage brand reputation.
      (e.g., No CTA, confusing messaging, focusing only on features, inconsistent brand voice).
    - `neutral` (Informational/Maintenance): Content for brand awareness or general info without a direct push for conversion.
      (e.g., Holiday greetings, general news, office culture).

    You MUST return a JSON array matching the schema provided in the user prompt.
    """

def build_user_prompt(paragraphs, date_str):
    """
    Simplified user prompt for social media content analysis.
    """
    paragraph_texts = []
    for idx, para in enumerate(paragraphs, start=1):
        paragraph_texts.append(f"--- [Post/Paragraph {idx}] ---\n{para}\n")
    
    paragraphs_str = "\n".join(paragraph_texts)

    return f"""
    Here are the social media posts/paragraphs published on {date_str}. Please analyze their marketing effectiveness.

    ## Content to Analyze
    {paragraphs_str}

    Please return the JSON array based on these paragraphs, following all rules from the system prompt.
    """

class CreatePromptHBView(View):
    def post(request):
        if request.method == 'POST':
            try:
                text = request.POST.get('paragraph', '')
                # date_str = request.POST.get('date', '')
                
                if not text or len(text.strip()) < 5:
                    return JsonResponse({"status": "error", "message": "No valid text input."}, status=400)
                # if not date_str:
                #     return JsonResponse({"status": "error", "message": "Missing 'date' field (YYYY-MM-DD)."}, status=400)
                
                paragraphs = []
                for line in text.splitlines():
                    line = line.strip()
                    if line:
                        paragraphs.extend(sent_tokenize(line))

                marketing_context = """
                    You are a professional Marketing Strategist and Content Writer. Your task is to analyze the social media posts below.
                    You MUST follow the rules below and return a JSON CODE BLOCK, without any other text.

                    ANALYSIS RULES
                    1. Impact Sign (+ / - / neutral):
                       + : High engagement/conversion potential (Strong Hook, Clear Value, Strong CTA).
                       - : Poor performance potential (Weak Hook, No CTA, boring/confusing).
                       neutral: Brand maintenance, informational only.

                    2. Performance Scoring (momentum_score):
                       Assign a score between -1.0 and 1.0:
                       +0.7 to +1.0: Viral/High Conversion potential (Excellent Hook + Irresistible Offer).
                       +0.1 to +0.4: Good quality, likely to get steady engagement.
                       0: Neutral.
                       -0.1 to -0.4: Weak content, likely to be scrolled past.
                       -0.7 to -1.0: Harmful or extremely poor quality (Spammy, offensive, or confusing).
                    3. Beta Decay Principle (Time-Weighting):
                        Information loses its market impact as time progresses and newer data emerges. You must calculate the effective_momentum using a decay factor beta = 0.05.
                        Formula: M_{effective} = √(|M_{intrinsic}|^2 * (1 - beta)^(N - n))
                        * M_{effective} has the same sign as M_{intrinsic}
                        N: Total number of paragraphs in the report.
                        n: Current paragraph index.
                        beta: 0.05 (The absorption rate of information).
                        Logic: The final paragraph (n=N) retains 100% of its weight. The first paragraph (n=1) is the most decayed.
                    4. Algebraic Structure Layer (Lie, Clifford, Cayley‑Dickson Enhancement):
                        Purpose: Use abstract algebraic structures to model more deeply how the market "digests" information. The rules below REFINE the calculations of Intrinsic Momentum, Beta Decay, Phase Shift and Cumulative Momentum without altering the original formulas.
                        4.1 Lie Bracket for Non‑commutative Interaction:
                            - Treat each consecutive pair of paragraphs (n‑1, n) as two operators. Compute a metaphorical "Lie bracket": L = |impact of (A then B) – impact of (B then A)|.
                            - If L > 0.3 → the information has strong order dependence (news A appearing first creates a significantly different effect than if it appeared later). In this case:
                                * Increase the Phase Shift by an additional 0.2x (i.e., 1.7x instead of 1.5x) if a Trend Reversal is detected.
                                * If L > 0.6 (extreme surprise), multiply the current paragraph's intrinsic_momentum by an amplification factor of 1.2 (sharp reversal) or 0.8 (sharp weakening) after applying the Phase Shift, while preserving the sign.
                        4.2 Clifford Semantic Geometry:
                            - Construct an abstract vector space with principal axes: price, weather, supply‑demand, geopolitics, logistics.
                            - Represent each paragraph as a multivector in a Clifford algebra. The geometric product between consecutive paragraphs tells whether they are "in phase" (positive result) or "out of phase" (negative result).
                            - Application: If the current paragraph is out of phase with the immediately preceding paragraph (e.g., clearly bullish followed by clearly bearish), then the effective_momentum of the current paragraph is strengthened by 15% (the market reacts more violently to contradictory signals). If they are in phase, reduce effective_momentum by 10% (consensus information causes less movement).
                            - Paragraphs containing many specific place names and numbers are considered "grade‑1 vectors" with high Spectral Density → they automatically trigger the existing rule of retaining 20% more weight against decay (as per section 4).
                    5. Metrics:
                       - hook_strength: 0.0 to 1.0
                       - conversion_potential: 0.0 to 1.0
                       - cumulative_momentum: Running sum of momentum_scores.
                """

                # Add each paragraph with its index
                content = marketing_context
                for idx, para in enumerate(paragraphs, 1):
                    content += f"\n--- [Post/Paragraph {idx}] ---\n{para}"

                # CẬP NHẬT: Cấu trúc JSON trả về phù hợp với Marketing
                content += """
                    RETURN THE JSON RESULT in the structure:
                    {
                        "analysis_report": [
                            {
                            "paragraph_index": 1,
                            "paragraph_type": "content_marketing",
                            "paragraph_sign": "+ | - | neutral",
                            "default_text": "Text content",
                            "sign_explanation": "Reasoning based on Hook, Value Prop, and CTA",
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
                        "summary_all_blog_sign": "+ | -",
                        "summary_all_blog_sign_explain": "Overall assessment of this content batch's ability to drive revenue",
                        "final_vector": {
                            "total_momentum": "Sum of all scores",
                            "trend_trajectory": "Growth | Declining | Stable"
                        }
                    }
                """

                # Note: The generation call is commented out as per your original code
                # response = client.models.generate_content(model="gemini-2.0-flash", contents=content)
                
                return JsonResponse({
                    "status": "success",
                    "message": "Marketing prompt created successfully",
                    "result": {
                        "ai_response": "",
                        "prompt_used": content
                    }
                }, status=200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, 'market-agent/create-prompt-HB.html')

class GetEffectiveMomentumPromptHBView(View):
    def post(request):
        if request.method == 'POST':
            try:
                json_input = request.POST.get('paragraph', '')
                if isinstance(json_input, str):
                    data = json.loads(json_input)
                else:
                    data = json_input

                report = data.get("analysis_report", [])
                paragraphs = np.array([item["paragraph_index"] if "paragraph_index" in item else item["sentence_index"] for item in report])

                effective_momentum = [item["decay_metrics"]["effective_momentum"] for item in report]

                print("effective_momentum:::", effective_momentum)
                print("effective_momentum length:::", len(effective_momentum))
                paragraph_length = len(paragraphs)
                return JsonResponse({
                    "status": "success",
                    "message": "Effective momentum calculated successfully",
                    "result": {
                        "effective_momentum": effective_momentum,
                        "paragraph_length": paragraph_length
                    }
                }, status=200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, 'market-agent/get-effective-momentum-HB.html')