from django.shortcuts import render
from google import genai
from django.http import JsonResponse
from django.views import View
import re
import os
from datetime import datetime, timedelta
from .models import DailyMarketPrice
from .market_agent_utils import safe_float, convert_json_string_to_object
import json
import numpy as np
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def build_system_prompt():
    """
    Prompt hệ thống, "dạy" Gemini chỉ tập trung vào Tác động.
    """
    return """
    You are a world-class financial analyst specializing in the coffee commodity market (Robusta & Arabica). 
    Your ONLY task is to analyze paragraphs and determine their price impact sign (+, -, or neutral).
    ## Your Analysis Rules:
    ### Price Impact Sign (+ / - / neutral)
    - You will be given yesterday's and today's prices.
    - **For "price" paragraphs (Farm-Gate, Midstream, Differential):** Your `paragraph_sign` MUST be based *only* on the numerical comparison.
        - `+` (Bullish): Today's price is higher than yesterday's.
        - `-` (Bearish): Today's price is lower than yesterday's.
        - `neutral`: No change.
        - *Differential Rule:* An increase (e.g., -80 to -50) is BULLISH (+). A decrease (e.g., -50 to -80) is BEARISH (-).
    - **For "semantic" paragraphs (News, Weather, Politics, etc.):** Your `paragraph_sign` is based on the *implied* market impact.
        - `+` (Bullish): Implies scarcity, high demand, high cost (e.g., "drought", "frost", "supply chain issues", "strong demand", "tariffs imposed").
        - `-` (Bearish): Implies abundance, low demand, low cost (e.g., "bumper crop", "favorable weather", "recession fears", "tariff lifting", "unlocking supply", "court blocks tariff").
        - `neutral`: Informational, no clear price impact.
    
    You MUST return a JSON array matching the schema.
    """


def build_user_prompt(paragraphs, curr_prices, prev_prices, date_str):
    prev_data_str = "No data for comparison."
    if prev_prices:
        # FIX: Truy cập thuộc tính của đối tượng DB Model (prev_prices)
        prev_data_str = f"""
    - Yesterday's Farm-Gate (low): {prev_prices.farm_gate_low}
    - Yesterday's Midstream (low): {prev_prices.midstream_low}
    - Yesterday's Differential (Bid): {prev_prices.differential_bid}
    - Yesterday's Differential (Ask): {prev_prices.differential_ask}
    """

    curr_data_str = f"""
    - Today's Farm-Gate (low): {curr_prices.get("farm_gate_low")}
    - Today's Midstream (low): {curr_prices.get("midstream_low")}
    - Today's Differential (Bid): {curr_prices.get("differential_bid")}
    - Today's Differential (Ask): {curr_prices.get("differential_ask")}
    """

    paragraph_texts = []
    for idx, para in enumerate(paragraphs, start=1):
        paragraph_texts.append(f"--- [Paragraph {idx}] ---\n{para}\n")

    paragraphs_str = "\n".join(paragraph_texts)

    return f"""
    Here is the market report for {date_str}. Please analyze it.
    ## Contextual Price Data
    ### Yesterday's Prices (Reference)
    {prev_data_str}
    ### Today's Prices (To be analyzed)
    {curr_data_str}
    ## Report Paragraphs to Analyze
    {paragraphs_str}
    Please return the JSON array based on these paragraphs and price data, following all rules from the system prompt.
    """


class CreatePromptView(View):
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

                # Xử lý lấy giá hôm trước từ DB và lưu giá ngày hôm nay
                for i in range(1, 5):
                    try:
                        prev_prices = DailyMarketPrice.objects.get(
                            date=datetime.fromisoformat(date_str).date()
                            - timedelta(days=i)
                        )
                        break
                    except DailyMarketPrice.DoesNotExist:
                        continue

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
                        {
                            "status": "error",
                            "message": "Missing 'date' field (YYYY-MM-DD).",
                        },
                        status=400,
                    )

                paragraphs = [
                    p.strip() for p in re.split(r"\n{1,}", text) if len(p.strip()) > 0
                ]

                # Prepare price data for the prompt
                price_context = """You are a professional financial analyst for the coffee commodity market. Your task is to analyze the daily report or article below.
                    You MUST follow the rules below and return a JSON CODE BLOCK, without any other text.

                    Based on the provided intraday price chart, you must identify the sequence in which the market "consumed" the information provided in the report.
                    1. IDENTIFY THE TIMELINE: Look at the price action from the start of the session to the end.
                    2. MAP PARAGRAPHS TO MOVEMENTS: 
                       - Which paragraph explains the opening trend? 
                       - Which paragraph explains the mid-day spikes or drops? 
                       - Which paragraph explains the closing recovery or sell-off?
                    3. REORDER FOR THE CURVE: You MUST reorder the paragraphs in the JSON output to reflect this timeline. 
                       - Paragraphs representing morning events come first.
                       - Paragraphs representing late adjustments (like fuel price changes at 15:00 or late weather changes) come later.

                    ANALYSIS RULES
                    1. Price Impact Sign (+ / - / neutral):
                        "price" Paragraphs: Compare Today vs. Yesterday. (+ if higher, - if lower).
                        "semantic" Paragraphs: + (Bullish - scarcity/high cost), - (Bearish - abundance/low cost).
                    2. Intrinsic Momentum Calculation:
                        Assign an intrinsic_momentum score between -1.0 and 1.0 based on the raw sentiment of the paragraph:
                        +0.7 to +1.0: Strong Bullish (Supply collapse, extreme weather).
                        +0.1 to +0.4: Weak Bullish (Slight delays, minor demand uptick).
                        0: Neutral/Structural.
                        -0.1 to -0.4: Weak Bearish (Normal harvest, slight surplus).
                        -0.7 to -1.0: Strong Bearish (Record bumper crop, demand collapse).
                    3. Beta Decay Principle (Time-Weighting):
                        Information loses its market impact as time progresses and newer data emerges. You must calculate the effective_momentum using a decay factor beta = 0.05.
                        Formula: M_{effective} = √(|M_{intrinsic}|^2 * (1 - beta)^(N - n))
                        * M_{effective} has the same sign as M_{intrinsic}
                        N: Total number of paragraphs in the report.
                        n: Current paragraph index.
                        beta: 0.05 (The absorption rate of information).
                        Logic: The final paragraph (n=N) retains 100% of its weight. The first paragraph (n=1) is the most decayed.
                    4. Market State Operator Logic (Non-commutative & Phase Transition):
                        Information as an Operator: Treat each paragraph as a mathematical operator acting on the current "Market State" vector. The result of $Paragraph(n)$ depends entirely on the state left by $Paragraph(n-1)$.
                        Non-commutative Phase Shift: If a paragraph introduces a "Trend Reversal" (e.g., from Bullish to Bearish), apply a Phase Shift factor of 1.5x to the intrinsic_momentum. The order $A \to B$ creates a different market "spectrum" than $B \to A$.
                        Spectral Density (Information Intensity): Instead of simple decay, calculate the "intensity" of a paragraph based on its technical density (numbers, specific locations like 'Dak Lak' or 'Minas Gerais', and crop dates). High-density paragraphs "resist" $beta$ decay and retain 20% more weight over $N$ steps.
                        The "Trace" Rule: The cumulative_momentum at paragraph $n$ must reflect the "trace" (the sum of eigenvalues) of all preceding information. If the sequence of paragraphs shows a narrowing volatility, reduce the effective_momentum of late-session noise by an additional 10%.
                    5. Algebraic Structure Layer (Lie, Clifford, Cayley‑Dickson Enhancement):
                        Purpose: Use abstract algebraic structures to model more deeply how the market "digests" information. The rules below REFINE the calculations of Intrinsic Momentum, Beta Decay, Phase Shift and Cumulative Momentum without altering the original formulas.
                        5.1 Lie Bracket for Non‑commutative Interaction:
                            - Treat each consecutive pair of paragraphs (n‑1, n) as two operators. Compute a metaphorical "Lie bracket": L = |impact of (A then B) – impact of (B then A)|.
                            - If L > 0.3 → the information has strong order dependence (news A appearing first creates a significantly different effect than if it appeared later). In this case:
                                * Increase the Phase Shift by an additional 0.2x (i.e., 1.7x instead of 1.5x) if a Trend Reversal is detected.
                                * If L > 0.6 (extreme surprise), multiply the current paragraph's intrinsic_momentum by an amplification factor of 1.2 (sharp reversal) or 0.8 (sharp weakening) after applying the Phase Shift, while preserving the sign.
                        5.2 Clifford Semantic Geometry:
                            - Construct an abstract vector space with principal axes: price, weather, supply‑demand, geopolitics, logistics.
                            - Represent each paragraph as a multivector in a Clifford algebra. The geometric product between consecutive paragraphs tells whether they are "in phase" (positive result) or "out of phase" (negative result).
                            - Application: If the current paragraph is out of phase with the immediately preceding paragraph (e.g., clearly bullish followed by clearly bearish), then the effective_momentum of the current paragraph is strengthened by 15% (the market reacts more violently to contradictory signals). If they are in phase, reduce effective_momentum by 10% (consensus information causes less movement).
                            - Paragraphs containing many specific place names and numbers (e.g., Dak Lak, 85,000 VND) are considered "grade‑1 vectors" with high Spectral Density → they automatically trigger the existing rule of retaining 20% more weight against decay (as per section 4).
                    6. Cumulative Momentum & Trajectory:
                        cumulative_momentum: The running sum of effective_momentum from paragraph 1 to n.
                        Differential Rule: An increase in the cumulative value (e.g., -0.80 to -0.50) is BULLISH (+). A decrease (e.g., -0.50 to -0.80) is BEARISH (-).
                        When computing cumulative_momentum in the reordered timeline, apply the Lie adjustment (5.1) and Clifford adjustment (5.2) to each consecutive pair, and simultaneously track the "dimensional" layer via Cayley‑Dickson thinking to assign the appropriate decay factor (5.3).
                    
                    INPUT DATA (ANALYZE THIS)
                    1. Contextual Price Data
                    Yesterday's Price (Reference):
                """

                price_context_not_sort = """You are a professional financial analyst for the coffee commodity market. Your task is to analyze the daily report or article below.
                    You MUST follow the rules below and return a JSON CODE BLOCK, without any other text.

                    ANALYSIS RULES
                    1. Price Impact Sign (+ / - / neutral):
                        "price" Paragraphs: Compare Today vs. Yesterday. (+ if higher, - if lower).
                        "semantic" Paragraphs: + (Bullish - scarcity/high cost), - (Bearish - abundance/low cost).
                    2. Intrinsic Momentum Calculation:
                        Assign an intrinsic_momentum score between -1.0 and 1.0 based on the raw sentiment of the paragraph:
                        +0.7 to +1.0: Strong Bullish (Supply collapse, extreme weather).
                        +0.1 to +0.4: Weak Bullish (Slight delays, minor demand uptick).
                        0: Neutral/Structural.
                        -0.1 to -0.4: Weak Bearish (Normal harvest, slight surplus).
                        -0.7 to -1.0: Strong Bearish (Record bumper crop, demand collapse).
                    3. Beta Decay Principle (Time-Weighting):
                        Information loses its market impact as time progresses and newer data emerges. You must calculate the effective_momentum using a decay factor beta = 0.05.
                        Formula: M_{effective} = √(|M_{intrinsic}|^2 * (1 - beta)^(N - n))
                        * M_{effective} has the same sign as M_{intrinsic}
                        N: Total number of paragraphs in the report.
                        n: Current paragraph index.
                        beta: 0.05 (The absorption rate of information).
                        Logic: The final paragraph (n=N) retains 100% of its weight. The first paragraph (n=1) is the most decayed.
                    4. Market State Operator Logic (Non-commutative & Phase Transition):
                        Information as an Operator: Treat each paragraph as a mathematical operator acting on the current "Market State" vector. The result of $Paragraph(n)$ depends entirely on the state left by $Paragraph(n-1)$.
                        Non-commutative Phase Shift: If a paragraph introduces a "Trend Reversal" (e.g., from Bullish to Bearish), apply a Phase Shift factor of 1.5x to the intrinsic_momentum. The order $A \to B$ creates a different market "spectrum" than $B \to A$.
                        Spectral Density (Information Intensity): Instead of simple decay, calculate the "intensity" of a paragraph based on its technical density (numbers, specific locations like 'Dak Lak' or 'Minas Gerais', and crop dates). High-density paragraphs "resist" $beta$ decay and retain 20% more weight over $N$ steps.
                        The "Trace" Rule: The cumulative_momentum at paragraph $n$ must reflect the "trace" (the sum of eigenvalues) of all preceding information. If the sequence of paragraphs shows a narrowing volatility, reduce the effective_momentum of late-session noise by an additional 10%.
                    5. Algebraic Structure Layer (Lie, Clifford, Cayley‑Dickson Enhancement):
                        Purpose: Use abstract algebraic structures to model more deeply how the market "digests" information. The rules below REFINE the calculations of Intrinsic Momentum, Beta Decay, Phase Shift and Cumulative Momentum without altering the original formulas.
                        5.1 Lie Bracket for Non‑commutative Interaction:
                            - Treat each consecutive pair of paragraphs (n‑1, n) as two operators. Compute a metaphorical "Lie bracket": L = |impact of (A then B) – impact of (B then A)|.
                            - If L > 0.3 → the information has strong order dependence (news A appearing first creates a significantly different effect than if it appeared later). In this case:
                                * Increase the Phase Shift by an additional 0.2x (i.e., 1.7x instead of 1.5x) if a Trend Reversal is detected.
                                * If L > 0.6 (extreme surprise), multiply the current paragraph's intrinsic_momentum by an amplification factor of 1.2 (sharp reversal) or 0.8 (sharp weakening) after applying the Phase Shift, while preserving the sign.
                        5.2 Clifford Semantic Geometry:
                            - Construct an abstract vector space with principal axes: price, weather, supply‑demand, geopolitics, logistics.
                            - Represent each paragraph as a multivector in a Clifford algebra. The geometric product between consecutive paragraphs tells whether they are "in phase" (positive result) or "out of phase" (negative result).
                            - Application: If the current paragraph is out of phase with the immediately preceding paragraph (e.g., clearly bullish followed by clearly bearish), then the effective_momentum of the current paragraph is strengthened by 15% (the market reacts more violently to contradictory signals). If they are in phase, reduce effective_momentum by 10% (consensus information causes less movement).
                            - Paragraphs containing many specific place names and numbers (e.g., Dak Lak, 85,000 VND) are considered "grade‑1 vectors" with high Spectral Density → they automatically trigger the existing rule of retaining 20% more weight against decay (as per section 4).
                    6. Cumulative Momentum & Trajectory:
                        cumulative_momentum: The running sum of effective_momentum from paragraph 1 to n.
                        Differential Rule: An increase in the cumulative value (e.g., -0.80 to -0.50) is BULLISH (+). A decrease (e.g., -0.50 to -0.80) is BEARISH (-).
                        When computing cumulative_momentum in the reordered timeline, apply the Lie adjustment (5.1) and Clifford adjustment (5.2) to each consecutive pair, and simultaneously track the "dimensional" layer via Cayley‑Dickson thinking to assign the appropriate decay factor (5.3).
                    
                    INPUT DATA (ANALYZE THIS)
                    1. Contextual Price Data
                    Yesterday's Price (Reference):
                """

                price_context_chunk = """
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
                    INPUT DATA (ANALYZE THIS)
                    1. Contextual Price Data
                    Yesterday's Price (Reference):
                """
                # Add yesterday's prices if available
                if prev_prices:
                    price_context += f"""
                    Farm-Gate (low): {prev_prices.farm_gate_low or 'N/A'}
                    Midstream (low): {prev_prices.midstream_low or 'N/A'}
                    Differential (Bid): {prev_prices.differential_bid or 'N/A'}
                    Differential (Ask): {prev_prices.differential_ask or 'N/A'}
                    """

                    price_context_not_sort += f"""
                    Farm-Gate (low): {prev_prices.farm_gate_low or 'N/A'}
                    Midstream (low): {prev_prices.midstream_low or 'N/A'}
                    Differential (Bid): {prev_prices.differential_bid or 'N/A'}
                    Differential (Ask): {prev_prices.differential_ask or 'N/A'}
                    """

                    price_context_chunk += f"""
                    Farm-Gate (low): {prev_prices.farm_gate_low or 'N/A'}
                    Midstream (low): {prev_prices.midstream_low or 'N/A'}
                    Differential (Bid): {prev_prices.differential_bid or 'N/A'}
                    Differential (Ask): {prev_prices.differential_ask or 'N/A'}
                    """
                else:
                    price_context += """
                    No previous price data available.
                    """
                    price_context_not_sort += """
                    No previous price data available.
                    """
                    price_context_chunk += """
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
                    curr_prices["farm_gate_low"] or "N/A",
                    curr_prices["farm_gate_high"] or "N/A",
                    curr_prices["midstream_low"] or "N/A",
                    curr_prices["midstream_high"] or "N/A",
                    curr_prices["differential_bid"] or "N/A",
                    curr_prices["differential_ask"] or "N/A",
                    date_str,
                )

                price_context_not_sort += """
                    Today's Price (Analysis):
                    Farm-Gate (low): {}
                    Farm-Gate (high): {}
                    Midstream (low): {}
                    Midstream (high): {}
                    Differential (Bid): {}
                    Differential (Ask): {}
                    2. Report to Analyze ({}):
                    """.format(
                    curr_prices["farm_gate_low"] or "N/A",
                    curr_prices["farm_gate_high"] or "N/A",
                    curr_prices["midstream_low"] or "N/A",
                    curr_prices["midstream_high"] or "N/A",
                    curr_prices["differential_bid"] or "N/A",
                    curr_prices["differential_ask"] or "N/A",
                    date_str,
                )

                price_context_chunk += """
                    Today's Price (Analysis):
                    Farm-Gate (low): {}
                    Farm-Gate (high): {}
                    Midstream (low): {}
                    Midstream (high): {}
                    Differential (Bid): {}
                    Differential (Ask): {}
                    2. Report to Analyze ({}):
                    """.format(
                    curr_prices["farm_gate_low"] or "N/A",
                    curr_prices["farm_gate_high"] or "N/A",
                    curr_prices["midstream_low"] or "N/A",
                    curr_prices["midstream_high"] or "N/A",
                    curr_prices["differential_bid"] or "N/A",
                    curr_prices["differential_ask"] or "N/A",
                    date_str,
                )

                # Add each paragraph with its index
                content = price_context
                for idx, para in enumerate(paragraphs, 1):
                    content += f"\n--- [Paragraph {idx}] ---\n{para}"

                content_not_sort = price_context_not_sort
                for idx, para in enumerate(paragraphs, 1):
                    content_not_sort += f"\n--- [Paragraph {idx}] ---\n{para}"

                content_chunk = price_context_chunk
                content_chunk += text

                # Add the JSON structure
                content += """
                    CRITICAL CONSTRAINTS
                    TOTAL INTEGRITY: You must process EVERY paragraph provided.
                    NO MERGING: Do not skip or combine paragraphs.
                    JSON ONLY: No conversational filler.
                    REORDERING ONLY: Your task is to REORDER these {len(paragraphs)} entries based on when the market "consumes" them on the chart (Timeline), not to reduce them.
                    
                    RETURN THE JSON RESULT in the structure:
                    The "analysis_report" array MUST be sorted by the logical time of market consumption.
                    {
                        "analysis_report": [
                            {
                            "original_index": n,
                            "paragraph_index": n,
                            "consumption_phase": "Opening | Mid-day | Afternoon | Closing",
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

                content_not_sort += """
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
                            "consumption_phase": "Opening | Mid-day | Afternoon | Closing",
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

                content_chunk += """
                TASK:
                    - Break the report into micro-chunks (phrases or data points).
                    - Map each chunk to a semantic layer.
                    - Ensure inherited trend consistency but individual momentum weighting.
                    - Output only valid JSON.
                """
                # response = client.models.generate_content(
                #     model="gemini-2.5-flash",
                #     contents=content,
                # )
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Created successfully",
                        "result": {
                            # "ai_response": response.text,
                            "ai_response": "",
                            "prompt_used": content,
                            "prompt_not_sort": content_not_sort,
                            "prompt_chunk": content_chunk,
                        },
                    },
                    status=200,
                )
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, "market-agent/create-prompt.html")

class GetCalculateMomentumView(View):
    def post(request):
        if request.method == 'POST':
            try:
                json_input = request.POST.get('paragraph', '')
                if isinstance(json_input, str):
                    data = json.loads(json_input)
                else:
                    data = json_input
                
                type = request.POST.get('type', '1')

                iv = request.POST.get('iv', 1)
                price_close = request.POST.get('price_close', 0)

                gap = request.POST.get('gap', 0)

                iv_calculated = float(iv) / 100 / 20
                price_calculated = float(price_close) * iv_calculated

                report = data.get("analysis_report", [])
                sum_abs = 0
                if type == '1':
                    paragraphs = np.array([item["paragraph_index"] if "paragraph_index" in item else item["sentence_index"] for item in report])
                    effective_momentum = [item["decay_metrics"]["effective_momentum"] for item in report]
                else:
                    paragraphs = np.array([item["index"] for item in report])
                    effective_momentum = [item["momentum"] for item in report]
                
                print("effective_momentum:::", effective_momentum)
                print("effective_momentum length:::", len(effective_momentum))

                sign_changed_effective_momentum = [float(x) * (-1) for x in effective_momentum]

                paragraph_length = len(paragraphs)
                sum_abs = sum(abs(float(x)) for x in effective_momentum)
                print("sum_abs:::", sum_abs)
                calculated_momentum = [float(x) / sum_abs * price_calculated for x in effective_momentum]
                print("calculated_momentum:::", calculated_momentum)

                nearest_index, nearest_gap = min(
                    enumerate(calculated_momentum),
                    key=lambda item: abs(abs(item[1]) - float(gap))
                )

                nearest_gap_momentum = effective_momentum[nearest_index]
                return JsonResponse({
                    "status": "success",
                    "message": "Get calculated momentum successfully",
                    "result": {
                        "effective_momentum": effective_momentum,
                        "sign_changed_effective_momentum": sign_changed_effective_momentum,
                        "paragraph_length": paragraph_length,
                        "sum_abs": sum_abs,
                        "price_calculated": price_calculated,
                        "calculated_momentum": calculated_momentum,
                        "nearest_index": nearest_index + 1,
                        "nearest_gap": nearest_gap,
                        "nearest_gap_momentum": nearest_gap_momentum,
                    }
                }, status=200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, 'market-agent/get-calculated-momentum.html')