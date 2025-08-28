from django.shortcuts import render, redirect
from .forms import UserLoginForm
from .services import UserAuthenticationService


def login_view(request):
    """用戶登入視圖"""
    # 如果用戶已經登入，直接重定向到會員專區
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