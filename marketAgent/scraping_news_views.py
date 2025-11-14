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

class ScrapingNewsView(View):
    def post(request):
        if request.method == 'POST':
            try:
                date_str = request.POST.get('date', '')
                
                # Prepare price data for the prompt
                context = """
                    
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
                        "prompt_used": context
                    }
                }, status=200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, 'market-agent/create-prompt.html')
