# views.py
import json
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone

class HomeView(ListView):
    template_name = "home.html"
    context_object_name = "home"

    # page = Page.objects.filter(code="HOME").first()
    
    def get_queryset(self):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home page"
        # context["page_content"] = self.page
        return context