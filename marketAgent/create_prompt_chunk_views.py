from django.shortcuts import render
from google import genai
from django.http import JsonResponse
from django.views import View
import os
import json
from datetime import datetime, timedelta
from .models import DailyMarketPrice
from .market_agent_utils import (
    safe_float,
    convert_json_string_to_object
)

# Khởi tạo client Gemini
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

def build_system_prompt():
    """
    Prompt hệ thống thực hiện chiến thuật "Phân rã đa tầng".
    Yêu cầu AI xác định Layer ý nghĩa trước khi chia nhỏ đến mức cụm từ.
    """
    return """
    You are a world-class Quantitative Coffee Market Analyst. 
    
    ## MISSION: SEMANTIC DECONSTRUCTION & LOGICAL MAPPING
    Your goal is to break down a market report into "Micro-Chunks" (phrases, clauses, or specific data points) while preserving the high-level logic.

    ### PHASE 1: SEMANTIC LAYERING (The "Brain")
    Analyze the input text to identify high-level semantic layers. Common layers in this domain include:
    - Supply & Farmer Psychology (Nguồn cung & Tâm lý nông dân)
    - Midstream & Local Trade (Thương mại nội địa)
    - Export & FOB Dynamics (Xuất khẩu & Chênh lệch giá)
    - Agronomy & Weather (Nông học & Thời tiết)
    - Global Macro & Geopolitics (Vĩ mô & Địa chính trị)
    - Local Logistics & Energy (Hậu cần & Năng lượng nội địa)

    ### PHASE 2: MICRO-CHUNKING (The "Nerves")
    Deconstruct the text into the smallest meaningful units. A chunk can be:
    - A full sentence.
    - A specific clause (e.g., "...while exporters remain cautious").
    - A critical data point (e.g., "Urea jumped +40%").
    Every chunk MUST have a sequential `index`.

    ### PHASE 3: LOGICAL INHERITANCE & WEIGHTING
    For each Micro-Chunk assign a momentum_score between -1.0 and 1.0:
    +0.7 to +1.0: Strong Bullish.
    +0.1 to +0.4: Weak Bullish.
    0: Neutral.
    -0.1 to -0.4: Weak Bearish.
    -0.7 to -1.0: Strong Bearish.

    *Beta Decay Principle (Time-Weighting):
        Information loses its market impact as time progresses and newer data emerges. You must calculate the effective_momentum using a decay factor beta = 0.05.
        Formula: M_{effective} = √(|M_{intrinsic}|^2 * (1 - beta)^(N - n))
        * M_{effective} has the same sign as M_{intrinsic}
        N: Total number of chunks in the report.
        n: Current chunk index.
        beta: 0.05 (The absorption rate of information).
        Logic: The final chunk (n=N) retains 100% of its weight. The first chunk (n=1) is the most decayed.

    *Market State Operator Logic (Non-commutative & Phase Transition):
        Information as an Operator: Treat each chunk as a mathematical operator acting on the current "Market State" vector. The result of $Chunk(n)$ depends entirely on the state left by $Chunk(n-1)$.
        Non-commutative Phase Shift: If a chunk introduces a "Trend Reversal" (e.g., from Bullish to Bearish), apply a Phase Shift factor of 1.5x to the intrinsic_momentum. The order $A \to B$ creates a different market "spectrum" than $B \to A$.
        Spectral Density (Information Intensity): Instead of simple decay, calculate the "intensity" of a chunk based on its technical density (numbers, specific locations like 'Dak Lak' or 'Minas Gerais', and crop dates). High-density chunks "resist" $beta$ decay and retain 20% more weight over $N$ steps.
        The "Trace" Rule: The cumulative_momentum at paragraph $n$ must reflect the "trace" (the sum of eigenvalues) of all preceding information. If the sequence of chunks shows a narrowing volatility, reduce the effective_momentum of late-session noise by an additional 10%.
    *Algebraic Structure Layer (Lie, Clifford, Cayley‑Dickson Enhancement):
        Purpose: Use abstract algebraic structures to model more deeply how the market "digests" information. The rules below REFINE the calculations of Intrinsic Momentum, Beta Decay, Phase Shift and Cumulative Momentum without altering the original formulas.
        1 Lie Bracket for Non‑commutative Interaction:
            - Treat each consecutive pair of chunks (n‑1, n) as two operators. Compute a metaphorical "Lie bracket": L = |impact of (A then B) – impact of (B then A)|.
            - If L > 0.3 → the information has strong order dependence (news A appearing first creates a significantly different effect than if it appeared later). In this case:
                * Increase the Phase Shift by an additional 0.2x (i.e., 1.7x instead of 1.5x) if a Trend Reversal is detected.
                * If L > 0.6 (extreme surprise), multiply the current paragraph's intrinsic_momentum by an amplification factor of 1.2 (sharp reversal) or 0.8 (sharp weakening) after applying the Phase Shift, while preserving the sign.
        2 Clifford Semantic Geometry:
            - Construct an abstract vector space with principal axes: price, weather, supply‑demand, geopolitics, logistics.
            - Represent each paragraph as a multivector in a Clifford algebra. The geometric product between consecutive chunks tells whether they are "in phase" (positive result) or "out of phase" (negative result).
            - Application: If the current paragraph is out of phase with the immediately preceding paragraph (e.g., clearly bullish followed by clearly bearish), then the effective_momentum of the current paragraph is strengthened by 15% (the market reacts more violently to contradictory signals). If they are in phase, reduce effective_momentum by 10% (consensus information causes less movement).
            - Paragraphs containing many specific place names and numbers (e.g., Dak Lak, 85,000 VND) are considered "grade‑1 vectors" with high Spectral Density → they automatically trigger the existing rule of retaining 20% more weight against decay (as per section 4).
    ### RETURN THE JSON RESULT in the structure:
    {
        "semantic_layers_found": ["Layer A", "Layer B"],
        "analysis_report": [
            {
                "index": 1,
                "text": "...",
                "parent_layer": "...",
                "logical_connection": "The inherited logic from the parent layer",
                "impact_sign": "+ | - | neutral",
                "momentum": 0.85
            }
        ],
        "overall_market_bias": "..."
    }
    """

def build_user_payload(paragraph, price_context):
    """
    Tạo nội dung prompt người dùng với dữ liệu giá để làm tham chiếu logic.
    """
    return f"""
    Context Data:
    {price_context}

    Input Paragraph to Process:
    \"\"\"{paragraph}\"\"\"

    TASK:
    - Break the report into micro-chunks (phrases or data points).
    - Map each chunk to a semantic layer.
    - Ensure inherited trend consistency but individual momentum weighting.
    - Output only valid JSON.
    """

class CreatePromptView2(View):
    def post(request):
        """Xử lý phân tích văn bản và trả về prompt/kết quả AI."""
        if request.method == 'POST':
            try:
                # 1. Lấy dữ liệu đầu vào
                paragraph = request.POST.get('paragraph', '')
                date_str = request.POST.get('date', '')
                curr_prices = {
                    "farm_gate_low": safe_float(request.POST.get('farm_gate_low', None)),
                    "farm_gate_high": safe_float(request.POST.get('farm_gate_high', None)),
                    "midstream_low": safe_float(request.POST.get('midstream_low', None)),
                    "midstream_high": safe_float(request.POST.get('midstream_high', None)),
                    "differential_ask": safe_float(request.POST.get('differential_ask', None)),
                    "differential_bid": safe_float(request.POST.get('differential_bid', None))
                }
                prev_prices = None

                # Xử lý lấy giá hôm trước từ DB và lưu giá ngày hôm nay
                for i in range(1, 5):
                    try:
                        prev_prices = DailyMarketPrice.objects.get(date=datetime.fromisoformat(date_str).date() - timedelta(days=i))
                        break
                    except DailyMarketPrice.DoesNotExist: continue
                
                if any(v is not None for v in curr_prices.values()):
                    DailyMarketPrice.objects.update_or_create(date=datetime.fromisoformat(date_str).date(), defaults=curr_prices)
                
                if not paragraph or len(paragraph.strip()) < 5:
                    return JsonResponse({"status": "error", "message": "No valid text input."}, status=400)
                if not date_str:
                    return JsonResponse({"status": "error", "message": "Missing 'date' field (YYYY-MM-DD)."}, status=400)

                price_context = ""
                # Add yesterday's prices if available
                if prev_prices:
                    price_context += f"""
                    Farm-Gate (low): {prev_prices.farm_gate_low or 'N/A'}
                    Midstream (low): {prev_prices.midstream_low or 'N/A'}
                    Differential (Bid): {prev_prices.differential_bid or 'N/A'}
                    Differential (Ask): {prev_prices.differential_ask or 'N/A'}
                    """
                else:
                    price_context += """
                    No previous price data available.
                    """

                # Add today's prices
                price_context += """
                    Today's Price (Analysis):
                    Farm-Gate (low): {}
                    Farm-Gate (high): {}
                    Midstream (low): {}
                    Midstream (high): {}
                    Differential (Bid): {}
                    Differential (Ask): {}
                    2. Report to Analyze ({}):
                    """.format(
                        curr_prices['farm_gate_low'] or 'N/A',
                        curr_prices['farm_gate_high'] or 'N/A',
                        curr_prices['midstream_low'] or 'N/A',
                        curr_prices['midstream_high'] or 'N/A',
                        curr_prices['differential_bid'] or 'N/A',
                        curr_prices['differential_ask'] or 'N/A',
                        date_str
                    )
                    
                # 2. Xây dựng Prompt (Dù có gọi API hay không, phần này vẫn được trả về)
                system_instruction = build_system_prompt()
                user_content = build_user_payload(paragraph, price_context)
                
                full_prompt_for_copy = f"SYSTEM INSTRUCTION:\n{system_instruction}\n\nUSER PROMPT:\n{user_content}"

                # 3. Gọi AI (Có thể comment lại nếu chỉ muốn lấy prompt)
                ai_response_data = ""
                
                # Kiểm tra nếu có API KEY thì mới thực thi gọi Gemini
                # api_key = os.environ.get('GEMINI_API_KEY')
                # if api_key:
                #     try:
                #         response = client.models.generate_content(
                #             model="gemini-2.0-flash",
                #             config={
                #                 "system_instruction": system_instruction,
                #                 "response_mime_type": "application/json"
                #             },
                #             contents=user_content,
                #         )
                #         ai_response_data = response.text
                #     except Exception as ai_err:
                #         ai_response_data = f"AI Error: {str(ai_err)}"
                # else:
                #     ai_response_data = "GEMINI_API_KEY not found. Please copy the prompt below to use externally."

                # 4. Trả về kết quả với đúng cấu trúc yêu cầu
                return JsonResponse({
                    "status": "success",
                    "message": "Processed successfully",
                    "result": {
                        "ai_response": ai_response_data, # Tab 1
                        "prompt_used": full_prompt_for_copy # Tab 2
                    }
                }, status=200)

            except Exception as e:
                return JsonResponse({
                    "status": "error", 
                    "message": str(e)
                }, status=500)
        
        return render(request, 'market-agent/create-prompt-2.html')