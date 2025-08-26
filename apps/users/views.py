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
        user_cards = request.user.user_cards.select_related("card", "card__bank").all()
        context["user_cards"] = user_cards

        # 新增這行：獲取收藏的卡片
        favorite_cards = request.user.preferences.favorite_cards.select_related(
            "bank"
        ).all()
        context["favorite_cards"] = favorite_cards

    return render(request, "users/member_zone.html", context)


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
        banks = Bank.objects.filter(is_active=True)
        cards = CreditCard.objects.filter(is_active=True).select_related("bank")

        context = {
            "banks": banks,
            "cards": cards,
        }
        return render(request, "pages/card_new.html", context)

    elif request.method == "POST":
        # 取得表單資料
        bank_id = request.POST.get("bank_id")
        card_id = request.POST.get("card_id")

        # 檢查資料完整性
        if not bank_id or not card_id:
            messages.error(request, "請選擇銀行和卡片")
            return redirect("pages:card_new")

        try:
            # 取得選擇的卡片
            selected_card = CreditCard.objects.get(id=card_id, is_active=True)

            # 檢查卡片是否真的屬於選的銀行
            if str(selected_card.bank.id) != bank_id:
                messages.error(request, "選擇的卡片與銀行不符！")
                return redirect("pages:card_new")

            # 檢查是否已經擁有這張卡片
            if UserCard.objects.filter(user=request.user, card=selected_card).exists():
                messages.error(request, "您已經擁有這張卡片了！")
                return redirect("pages:card_new")

            # 新增卡片到用戶帳戶
            UserCard.objects.create(user=request.user, card=selected_card)

            messages.success(
                request, f"成功新增 {selected_card.bank.name} {selected_card.name}！"
            )
            return redirect("users:member_zone")

        except CreditCard.DoesNotExist:
            messages.error(request, "選擇的卡片不存在")
            return redirect("pages:card_new")
