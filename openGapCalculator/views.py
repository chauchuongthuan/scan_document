from django.http import JsonResponse
from django.shortcuts import render
import os
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.conf import settings
from rapidfuzz import fuzz, process
# Keyword Views
class RCOpenGapCalculatorView:  
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            try:
                excel_file = request.FILES['excel_file']
                # Read the CSV file directly from memory
                if excel_file.name.endswith('.xlsx'):
                    df = pd.read_excel(excel_file, header=0)
                else:
                    df = pd.read_csv(excel_file, header=0)
                
                # Convert string values to float, handling thousand separators
                value_c2 = float(str(df.iloc[0, 2]).replace(',', ''))
                value_b3 = float(str(df.iloc[1, 1]).replace(',', ''))

                result = value_c2 - value_b3
                response_data = {
                    'status': 'success',
                    'message': 'Xử lý thành công',
                    'result': {
                        'open_today_value': value_c2,
                        'close_yesterday_value': value_b3,
                        'open_gap': result
                    }
                }
                return JsonResponse(response_data)

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xử lý file: {str(e)}'
                }, status=400)
        
        return render(request, 'openGapCalculator/rc.html')
    
