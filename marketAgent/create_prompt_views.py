from django.shortcuts import render
from google import genai
from django.http import JsonResponse
from django.views import View
import re
from datetime import datetime, timedelta
from .models import DailyMarketPrice
from .market_agent_utils import (
    safe_float,
    convert_json_string_to_object
)
client = genai.Client(api_key="AIzaSyA46hJwJsxpkB-a78FG2j9ryeB4OZ4RbjE")

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
        if request.method == 'POST':
            try:
                text = request.POST.get('paragraph', '')
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
                
                if not text or len(text.strip()) < 5:
                    return JsonResponse({"status": "error", "message": "No valid text input."}, status=400)
                if not date_str:
                    return JsonResponse({"status": "error", "message": "Missing 'date' field (YYYY-MM-DD)."}, status=400)
                
                paragraphs = [p.strip() for p in re.split(r'\n{1,}', text) if len(p.strip()) > 0]
                
                # Prepare price data for the prompt
                price_context = """
                    You are a professional financial analyst for the coffee commodity market. Your task is to analyze the daily report below.
                    You MUST follow the rules below and return a JSON CODE BLOCK, without any other text.

                    ANALYSIS RULES
                    1. Price Impact Sign (+ / - / neutral)
                    "price" Paragraphs (Farm-Gate, Midstream, Differential): The sign MUST be based on the numerical comparison (Today vs. Yesterday).
                    +: Today's price is higher.
                    -: Today's price is lower.
                    Differential Rule: An increase (e.g., -80 to -50) is BULLISH (+). A decrease (e.g., -50 to -80) is BEARISH (-).
                    "semantic" Paragraphs (News, Politics): The sign is based on the implied impact.
                    + (Bullish): Implies scarcity, high costs (e.g., "drought", "frost", "supply concerns", "tariffs").
                    - (Bearish): Implies abundance, low costs (e.g., "bumper crop", "favorable weather", "tariff lifting", "unlocking supply").
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

                # Add each paragraph with its index
                content = price_context
                for idx, para in enumerate(paragraphs, 1):
                    content += f"\n--- [Paragraph {idx}] ---\n{para}"

                # Add the JSON structure
                content += """
                    RETURN THE JSON RESULT in the structure:
                    [
                    {
                        "paragraph_index": 1,
                        "paragraph_type": "price",
                        "paragraph_sign": "+",
                        "default_text": "Default text of paragraph",
                        "sign_explanation": "Explain why it is + or -"
                    }
                    ]
                """
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=content,
                )
                return JsonResponse({
                    "status": "success",
                    "message": "Created successfully",
                    "result": {
                        "ai_response": response.text,
                        # "ai_response": "",
                        "prompt_used": content
                    }
                }, status=200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, 'market-agent/create-prompt.html')
