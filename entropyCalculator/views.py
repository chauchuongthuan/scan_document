from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.contrib.auth.decorators import login_required
from .models import ViralContentAnalyzer
from django.shortcuts import render

class CalculateViralPotentialView(View):
    """
    API view to calculate viral potential for restaurant social media posts
    """
    @login_required(login_url="login_cms")
    def post(request):
        if request.method == 'POST':
            try:
                paragraph = request.POST.get('paragraph', '')
                
                if not paragraph:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No paragraph provided'
                    }, status=400)

                result = ViralContentAnalyzer.calculate_viral_potential(
                    paragraph,
                )
                return JsonResponse({
                    'status': 'success',
                    'message': 'Calculate viral potential successfully!',
                    'result': result
                })
            except Exception as e:
                print("Error2222222:", str(e))  # Debug log
                return JsonResponse({
                    'status': 'error',
                    'message': f'Calculate viral potential failed: {str(e)}'
                }, status=400) 
        return render(request, 'entropy/create.html')