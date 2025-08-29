from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .forms import UserLoginForm
from .services import UserAuthenticationService


def login_view(request):
    """用戶登入視圖"""
    
    if request.user.is_authenticated:
        return redirect('users:member_zone')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        success, user, error_type = UserAuthenticationService.login_user(request, form)
        
        if success:
            UserAuthenticationService.handle_login_success(request, user)
            return redirect('users:member_zone')
        else:
            UserAuthenticationService.handle_login_failure(request, error_type, form)
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


@require_POST
def logout_view(request):
    """用戶登出視圖"""
    username = UserAuthenticationService.logout_user(request)
    
    if username:
        UserAuthenticationService.handle_logout_success(request, username)
    
        return redirect('pages:download')