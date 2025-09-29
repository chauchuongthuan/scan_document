import os
from django.contrib.auth import authenticate, login
from django.shortcuts import render

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# url = os.getenv("R2_URL", "")

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

# @csrf_exempt
# def ckeditor_upload_view(request):
#     print("Received request to ckeditor_upload_view")
#     print(f"Request method: {request.method}")
#     print(f"Request FILES: {request.FILES}")

#     if request.method == "POST" and request.FILES.get("upload"):
#         print("Processing file upload")
#         file = request.FILES["upload"]
#         file_name = default_storage.save(os.path.join("uploads", file.name), file)
#         url = default_storage.url(file_name)
#         print(f"File uploaded successfully. URL: {url}")
#         return JsonResponse({"url": url})

#     print("Upload failed")
#     return JsonResponse({"error": "Upload failed"}, status=400)


# Create your views here.
def index(request):

    return render(request, "layouts/default.html")

# def pages(request):
#     return render(request, 'components/pages/list.html')