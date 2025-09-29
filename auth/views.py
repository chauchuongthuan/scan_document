from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views import View

# # Create your views here.

class LoginView(View):
    template_name = 'admin/layouts/login.html'

    def get(self, request):
        return render(request, self.template_name)

    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        if all([username, password]):
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # if user.is_superuser:
                if user.is_active:
                    login(request, user)
                    return redirect('document-list')
                else:
                    messages.error(request, 'You do not have permissions')
            else:
                messages.error(request, 'Invalid username or password')
        return redirect('login_cms')
    
@login_required
def logout_account(request):
    logout(request)
    return redirect('login_cms')