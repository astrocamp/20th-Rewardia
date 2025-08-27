from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
import json
from .forms import UserRegistrationForm

# Create your views here.

def member_zone(request):
    """
    會員專區統一頁面
    - 未登入：顯示登入提示
    - 已登入：顯示會員資料和卡片
    """
    context = {}
    
    if request.user.is_authenticated:
        # 獲取用戶的卡片資料
        user_cards = request.user.user_cards.select_related('card', 'card__bank').all()
        context['user_cards'] = user_cards
    
    return render(request, 'users/member_zone.html', context)


def register(request):
    """使用者註冊"""
    if request.method == 'POST':
        # 判斷是否為 AJAX 請求
        if request.headers.get('content-type') == 'application/json':
            return handle_ajax_registration(request)
        else:
            # 一般表單提交
            form = UserRegistrationForm(request.POST)
            if form.is_valid():
                # 創建新用戶
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                
                messages.success(request, '註冊成功！請登入您的帳號。')
                return redirect('pages:login')  # 重定向到登入頁面
            else:
                # 表單驗證失敗
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


@csrf_exempt
def handle_ajax_registration(request):
    """處理 AJAX 註冊請求"""
    try:
        data = json.loads(request.body)
        form = UserRegistrationForm(data)
        
        if form.is_valid():
            # 創建新用戶
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            
            return JsonResponse({
                'success': True,
                'message': '註冊成功！正在跳轉至登入頁面...',
                'redirect_url': '/login/'  # 登入頁面 URL
            })
        else:
            # 收集所有錯誤訊息
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors[0]  # 取第一個錯誤訊息
            
            return JsonResponse({
                'success': False,
                'errors': errors
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '請求格式錯誤'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'系統錯誤: {str(e)}'
        })
