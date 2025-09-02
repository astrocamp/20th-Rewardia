from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .services import UserRegistrationService
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.cards.models import CreditCard
from .models import UserCard


def register(request):
    """使用者註冊"""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        success, user, error_type = UserRegistrationService.register_user(form)

        if success:
            UserRegistrationService.handle_registration_success(request, user)
            return redirect("sessions:login")
        else:
            UserRegistrationService.handle_registration_failure(
                request, error_type, form
            )
    else:
        form = UserRegistrationForm()

    return render(request, "users/register.html", {"form": form})


def prepare_card_form_context(
    user_card=None, is_edit_mode=False, include_selected_bank=False
):
    # 基本的context資料
    # banks = Bank.objects.filter(is_active=True).only("id", "name", "code")
    cards = (
        CreditCard.objects.filter(is_active=True)
        .select_related("bank")
        .only("id", "name", "bank__id", "bank__name")
    )

    context = {
        # "banks": banks,
        "cards": cards,
        "user_card": user_card,
        "is_edit_mode": is_edit_mode,
    }

    if include_selected_bank:
        if is_edit_mode and user_card:
            context["selected_bank"] = user_card.card.bank
        else:
            context["selected_bank"] = None

    return context


@login_required
def member_zone(request):
    context = {}

    if request.user.is_authenticated:
        # 獲取用戶的卡片資料
        user_cards = request.user.user_cards.select_related("card", "card__bank").all()
        context["user_cards"] = user_cards

    return render(request, "users/member_zone.html", context)


# API 端點：根據銀行 ID 返回該銀行的所有信用卡（JSON 格式，給 Alpine.js 用）
# def get_cards_by_bank(request, bank_id):
# try:
# bank = Bank.objects.get(id=bank_id, is_active=True)

# 取得該銀行的所有啟用信用卡
# cards = (
#     # CreditCard.objects.filter(bank=bank, is_active=True)
#     .only("id", "name")
#     .order_by("name")
# )

# 轉換為 JSON 格式
# cards_data = [{"id": card.id, "name": card.name} for card in cards]

# return JsonResponse(
#     {
#         "success": True,
#         "bank_name": bank.name,
#         "cards": cards_data,
#         "message": f"載入 {bank.name} 的 {len(cards_data)} 張信用卡",
#     }
# )

# except Bank.DoesNotExist:
#     return JsonResponse(
#         {"success": False, "cards": [], "message": "找不到指定的銀行"}, status=404
#     )


@login_required
def card_form(request, card_id=None):
    # 判斷是新增還是編輯模式
    if card_id:
        user_card = get_object_or_404(UserCard, id=card_id, user=request.user)
        is_edit_mode = True
    else:
        user_card = None
        is_edit_mode = False

    if request.method == "GET":
        # 顯示表單頁面 - 使用輔助函式準備context
        context = prepare_card_form_context(
            user_card=user_card, is_edit_mode=is_edit_mode, include_selected_bank=True
        )
        return render(request, "users/card_form.html", context)

    elif request.method == "POST":
        # 取得表單資料
        bank_id = request.POST.get("bank_id")
        card_id_from_form = request.POST.get("card_id")

        # 檢查資料完整性
        if not bank_id or not card_id_from_form:
            messages.error(request, "請選擇銀行和卡片")
            # 使用輔助函式重新準備表單資料
            context = prepare_card_form_context(
                user_card=user_card,
                is_edit_mode=is_edit_mode,
                include_selected_bank=False,
            )
            return render(request, "users/card_form.html", context)

        try:
            selected_card = CreditCard.objects.get(id=card_id_from_form, is_active=True)

            # 檢查卡片是否真的屬於選的銀行
            if str(selected_card.bank.id) != bank_id:
                messages.error(request, "選擇的卡片與銀行不符！")
                # 使用輔助函式重新準備表單資料
                context = prepare_card_form_context(
                    user_card=user_card,
                    is_edit_mode=is_edit_mode,
                    include_selected_bank=False,
                )
                return render(request, "users/card_form.html", context)

            if is_edit_mode:
                # 編輯模式：檢查是否會與其他卡片重複
                existing_card = (
                    UserCard.objects.filter(user=request.user, card=selected_card)
                    .exclude(id=user_card.id)
                    .first()
                )  # 排除當前正在編輯的這張

                if existing_card:
                    messages.error(request, "您已經擁有這張卡片了！無法重複新增。")
                    # 使用輔助函式重新準備表單資料
                    context = prepare_card_form_context(
                        user_card=user_card,
                        is_edit_mode=is_edit_mode,
                        include_selected_bank=False,
                    )
                    return render(request, "users/card_form.html", context)

                # 更新現有卡片
                user_card.card = selected_card
                user_card.save()
                messages.success(
                    request,
                    f"成功更新為 {selected_card.bank.name} {selected_card.name}！",
                )
            else:
                # 新增模式：檢查重複 + 創建新卡片
                if UserCard.objects.filter(
                    user=request.user, card=selected_card
                ).exists():
                    messages.error(request, "您已經擁有這張卡片了！")
                    # 使用輔助函式重新準備表單資料
                    context = prepare_card_form_context(
                        user_card=user_card,
                        is_edit_mode=is_edit_mode,
                        include_selected_bank=False,
                    )
                    return render(request, "users/card_form.html", context)

                UserCard.objects.create(
                    user=request.user, card=selected_card, nickname="", is_primary=False
                )
                messages.success(
                    request,
                    f"成功新增 {selected_card.bank.name} {selected_card.name}！",
                )

            return redirect("users:member_zone")

        except CreditCard.DoesNotExist:
            messages.error(request, "選擇的卡片不存在")
            # 使用輔助函式重新準備表單資料
            context = prepare_card_form_context(
                user_card=user_card,
                is_edit_mode=is_edit_mode,
                include_selected_bank=False,
            )
            return render(request, "users/card_form.html", context)


# 刪除功能
@login_required
def card_delete(request, card_id):
    # 確保這張卡片屬於當前用戶
    user_card = get_object_or_404(UserCard, id=card_id, user=request.user)

    if request.method == "POST":
        # 處理刪除請求
        card_name = f"{user_card.card.bank.name} {user_card.card.name}"
        user_card.delete()
        messages.success(request, f"成功刪除 {card_name}！")
        return redirect("users:member_zone")

    # GET 請求：顯示確認刪除頁面
    context = {
        "user_card": user_card,
    }
    return render(request, "users/card_delete_confirm.html", context)
