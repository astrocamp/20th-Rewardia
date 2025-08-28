from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .services import UserRegistrationService

def member_zone(request):
    """
    會員專區統一頁面
    - 未登入：顯示登入提示
    - 已登入：顯示會員資料和卡片
    """
    context = {}
    
    if request.user.is_authenticated:
        user_cards = request.user.user_cards.select_related('card', 'card__bank').all()
        context['user_cards'] = user_cards
    
    return render(request, 'users/member_zone.html', context)


def register(request):
    """使用者註冊"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        success, user, error_type = UserRegistrationService.register_user(form)
        
        if success:
            UserRegistrationService.handle_registration_success(request, user)
            return redirect('pages:login')
        else:
            UserRegistrationService.handle_registration_failure(request, error_type, form)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})
