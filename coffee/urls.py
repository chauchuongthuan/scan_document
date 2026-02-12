"""
URL configuration for coffee project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from django_ckeditor_5 import views as ckeditor_views
from django.views.decorators.csrf import csrf_exempt
from auth.views import LoginView, logout_account
from django.views.generic.base import RedirectView
urlpatterns = [
    path('admin/', admin.site.urls),

    # path('ckeditor5/', include('django_ckeditor_5.urls')),
    # path('ckeditor5/image_upload/', csrf_exempt(ckeditor_views.upload_file), name='ckeditor_image_upload'),

    path('', RedirectView.as_view(url='/cms/login/')),

    path('documents/', include('documents.urls')),
    path('keywords/', include('keywords.urls')),
    path('entropy-calculator/', include('entropyCalculator.urls')),
    path('open-nc-file/', include('openNcFile.urls')),
    path('market-agent/', include('marketAgent.urls')),
    path('open-gap-calculator/', include('openGapCalculator.urls')),
    path('forecasting/', include('forecasting.urls')),
    path('quantum-engine/', include('quantumEngine.urls')),
    path('quantum-engine-v2/', include('quantumEngineV2.urls')),
    path('chart-ohlc/', include('chartOHLC.urls')),
    path('daily-ohlc/', include('dailyOHLC.urls')),
    path('revenue/', include('revenue.urls')),

    # AUTH CMS
    path('cms/login/', LoginView.as_view(), name='login_cms'),
    path('cms/logout/', logout_account, name='logout_cms'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
