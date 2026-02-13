from django.shortcuts import render
from django.http import JsonResponse
from .models import OHLCDataKC, OHLCDataRC
from datetime import datetime
from django.utils import timezone
import pytz
from django.contrib.auth.decorators import login_required

class ChartView:
    @login_required(login_url="login_cms")
    def view_chart_kc(request):
        # Hiển thị trang dashboard
        return render(request, 'chart/kc.html')

    @login_required(login_url="login_cms")
    def get_chart_json_kc(request):
        # 1. Lấy thời gian hiện tại theo múi giờ trong settings (Asia/Ho_Chi_Minh)
        now_local = timezone.localtime()
        # yesterday_local = now_local - timezone.timedelta(days=1)
        today_start = now_local.replace(hour=16, minute=0, second=0, microsecond=0)
        symbol = request.GET.get('symbol', 'KCU2026')

        data = OHLCDataKC.objects.filter(
            symbol=symbol, 
            timestamp__gte=today_start
        ).order_by('-timestamp')[:600]
        
        chart_data = []
        for d in reversed(data):
            chart_data.append({
                'time': int(timezone.localtime(d.timestamp).timestamp()),
                'open': d.open, 
                'high': d.high,
                'low': d.low, 
                'close': d.close
            })
        return JsonResponse(chart_data, safe=False)

    @login_required(login_url="login_cms")
    def view_chart_rc(request):
        # Hiển thị trang dashboard
        return render(request, 'chart/rc.html')

    @login_required(login_url="login_cms")
    def get_chart_json_rc(request):
        # 1. Lấy thời gian hiện tại theo múi giờ trong settings (Asia/Ho_Chi_Minh)
        now_local = timezone.localtime()
        # yesterday_local = now_local - timezone.timedelta(days=1)
        today_start = now_local.replace(hour=16, minute=0, second=0, microsecond=0)
        symbol = request.GET.get('symbol', 'RCU2026')
        
        data = OHLCDataRC.objects.filter(
            symbol=symbol, 
            timestamp__gte=today_start
        ).order_by('-timestamp')[:600]
        
        chart_data = []
        for d in reversed(data):
            chart_data.append({
                'time': int(timezone.localtime(d.timestamp).timestamp()),
                'open': d.open, 
                'high': d.high,
                'low': d.low, 
                'close': d.close
            })
            
        return JsonResponse(chart_data, safe=False)