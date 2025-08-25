from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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
