from django.contrib import messages
from django.http import QueryDict
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
import uuid

class PermissionRequired:
    permission_required = None 

    def dispatch(self, request, *args, **kwargs):
        # if request.user.is_superuser:
        #     return super().dispatch(request, *args, **kwargs)
        # if self.permission_required and not request.user.has_perm(self.permission_required):
        #     messages.error(request, 'Không tìm thấy quyền truy cập của bạn!')
        #     return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)