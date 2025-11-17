from django.shortcuts import render
from google import genai
from django.http import JsonResponse
from django.views import View
import re
from datetime import datetime, timedelta
from .models import DailyMarketPrice
from .ft_api import search_ft
class FTSearchView(View):
    def post(request):
        if request.method == 'POST':
            try:
                keyword = request.POST.get('keyword', '')
                result = search_ft(keyword)
                return JsonResponse({
                    "status": "success",
                    "message": "Created successfully",
                    "result": result
                }, status=200)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return render(request, 'market-agent/ft-search.html')
