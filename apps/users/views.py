from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .services import UserRegistrationService
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.banks.models import Bank
from apps.cards.models import CreditCard
from .models import UserCard

# Create your views here.


def member_zone(request):
    context = {}

    if request.user.is_authenticated:
        # 獲取用戶的卡片資料
        user_cards = request.user.user_cards.select_related('card', 'card__bank').all()
        context['user_cards'] = user_cards

        # 暫時移除收藏卡片功能，避免錯誤
        # favorite_cards = request.user.preferences.favorite_cards.select_related('bank').all()
        # context['favorite_cards'] = favorite_cards

    return render(request, 'users/member_zone.html', context)


def register(request):
    """使用者註冊"""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        success, user, error_type = UserRegistrationService.register_user(form)

        if success:
            UserRegistrationService.handle_registration_success(request, user)
            return redirect("pages:login")
        else:
            UserRegistrationService.handle_registration_failure(
                request, error_type, form
            )
    else:
        form = UserRegistrationForm()

    return render(request, "users/register.html", {"form": form})





@login_required
def card_create(request):
    if request.method == "GET":
        # 用戶想看申請表 - 準備銀行和卡片資料
def card_form(request, card_id=None):


    # 判斷是新增還是編輯模式
    if card_id:
        user_card = get_object_or_404(UserCard, id=card_id, user=request.user)
        is_edit_mode = True
    else:
        user_card = None
        is_edit_mode = False

    if request.method == 'GET':
        # 顯示表單頁面
        banks = Bank.objects.filter(is_active=True).only('id', 'name', 'code')

        # 決定要篩選哪個銀行的卡片
        selected_bank_id = None

        # 編輯模式：不篩選，載入所有卡片
        cards = CreditCard.objects.filter(is_active=True).select_related('bank').only('id', 'name', 'bank__id', 'bank__name')

        context = {
            "banks": banks,
            "cards": cards,
            'banks': banks,
            'cards': cards,
            'selected_bank_id': selected_bank_id,  # 傳給模板
            'user_card': user_card,
            'is_edit_mode': is_edit_mode,
        }

        # 編輯模式時，確保當前卡片在選項中
        if is_edit_mode and user_card:
            # 如果篩選後的卡片中沒有當前編輯的卡片，就加入
            if not cards.filter(id=user_card.card.id).exists():
                # 取消篩選，顯示所有卡片
                cards = CreditCard.objects.filter(is_active=True).select_related('bank').only('id', 'name', 'bank__id', 'bank__name')
                context['cards'] = cards
                context['selected_bank_id'] = None
        return render(request, 'pages/card_new.html', context)

    elif request.method == 'POST':
        # 取得表單資料
        bank_id = request.POST.get('bank_id')
        card_id_from_form = request.POST.get('card_id')

        # 檢查資料完整性
        if not bank_id or not card_id_from_form:
            messages.error(request, '請選擇銀行和卡片')
            # 重新準備表單資料
            banks = Bank.objects.filter(is_active=True)
            cards = CreditCard.objects.filter(is_active=True).select_related('bank')
            context = {
                'banks': banks,
                'cards': cards,
                'user_card': user_card,
                'is_edit_mode': is_edit_mode,
            }
            return render(request, 'pages/card_new.html', context)

        try:
            # 取得選擇的卡片
            selected_card = CreditCard.objects.get(id=card_id_from_form, is_active=True)

            # 檢查卡片是否真的屬於選的銀行
            if str(selected_card.bank.id) != bank_id:
                messages.error(request, '選擇的卡片與銀行不符！')
                # 重新準備表單資料
                banks = Bank.objects.filter(is_active=True)
                cards = CreditCard.objects.filter(is_active=True).select_related('bank')
                context = {
                    'banks': banks,
                    'cards': cards,
                    'user_card': user_card,
                    'is_edit_mode': is_edit_mode,
                }
                return render(request, 'pages/card_new.html', context)

            if is_edit_mode:
                # 編輯模式：檢查是否會與其他卡片重複
                existing_card = UserCard.objects.filter(
                    user=request.user,
                    card=selected_card
                ).exclude(id=user_card.id).first()  # 排除當前正在編輯的這張

                if existing_card:
                    messages.error(request, '您已經擁有這張卡片了！無法重複新增。')
                    # 重新準備表單資料
                    banks = Bank.objects.filter(is_active=True)
                    cards = CreditCard.objects.filter(is_active=True).select_related('bank')
                    context = {
                        'banks': banks,
                        'cards': cards,
                        'user_card': user_card,
                        'is_edit_mode': is_edit_mode,
                    }
                    return render(request, 'pages/card_new.html', context)

                # 更新現有卡片
                user_card.card = selected_card
                user_card.save()
                messages.success(request, f'成功更新為 {selected_card.bank.name} {selected_card.name}！')
            else:
                # 新增模式：檢查重複 + 創建新卡片
                if UserCard.objects.filter(user=request.user, card=selected_card).exists():
                    messages.error(request, '您已經擁有這張卡片了！')
                    # 重新準備表單資料，而不是 redirect
                    banks = Bank.objects.filter(is_active=True)
                    cards = CreditCard.objects.filter(is_active=True).select_related('bank')
                    context = {
                        'banks': banks,
                        'cards': cards,
                        'user_card': user_card,
                        'is_edit_mode': is_edit_mode,
                    }
                    return render(request, 'pages/card_new.html', context)

                UserCard.objects.create(
                    user=request.user,
                    card=selected_card,
                    nickname='',
                    is_primary=False
                )
                messages.success(request, f'成功新增 {selected_card.bank.name} {selected_card.name}！')

            return redirect('users:member_zone')

        except CreditCard.DoesNotExist:
            messages.error(request, '選擇的卡片不存在')
            # 重新準備表單資料
            banks = Bank.objects.filter(is_active=True)
            cards = CreditCard.objects.filter(is_active=True).select_related('bank')
            context = {
                'banks': banks,
                'cards': cards,
                'user_card': user_card,
                'is_edit_mode': is_edit_mode,
            }
            return render(request, 'pages/card_new.html', context)


@login_required
def card_delete(request, card_id):
    """刪除卡片功能"""

    # 確保這張卡片屬於當前用戶
    user_card = get_object_or_404(UserCard, id=card_id, user=request.user)

    if request.method == 'POST':
        # 處理刪除請求
        card_name = f"{user_card.card.bank.name} {user_card.card.name}"
        user_card.delete()
        messages.success(request, f'成功刪除 {card_name}！')
        return redirect('users:member_zone')

    # GET 請求：顯示確認刪除頁面
    context = {
        'user_card': user_card,
    }
    return render(request, 'users/card_delete_confirm.html', context)
