from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .services import UserRegistrationService
from django.contrib import messages
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from django.contrib.auth import authenticate, login
from django.contrib.auth.backends import ModelBackend
import json

# from apps.banks.models import Bank
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

    return render(request, "users/register.html", {"form": form, "hide_chatbot": True})


def prepare_card_form_context(
    user_card=None, is_edit_mode=False, include_selected_bank=False
):
    # 取得所有活躍的卡片
    cards = CreditCard.objects.filter(is_active=True).only("id", "name", "bank")

    # 取得所有有卡片的銀行名稱 (去重複)
    bank_names = cards.values_list("bank", flat=True).distinct().order_by("bank")
    # 轉換成模板期望的格式
    banks = [{"name": bank_name} for bank_name in bank_names if bank_name]

    context = {
        "banks": banks,
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


def member_zone(request):
    context = {}

    if request.user.is_authenticated:
        # 獲取用戶的卡片資料
        user_cards = request.user.user_cards.select_related("card").all()
        context["user_cards"] = user_cards

    return render(request, "users/member_zone.html", context)


# API 端點：根據銀行名稱返回該銀行的所有信用卡（JSON 格式，給 Alpine.js 用）
def get_cards_by_bank(request, bank_name):
    try:
        # 取得該銀行的所有啟用信用卡
        cards = (
            CreditCard.objects.filter(bank=bank_name)
            .only("id", "name")
            .order_by("name")
        )

        # 轉換為 JSON 格式
        cards_data = [{"id": card.id, "name": card.name} for card in cards]

        return JsonResponse(
            {
                "success": True,
                "bank_name": bank_name,
                "cards": cards_data,
                "message": f"載入 {bank_name} 的 {len(cards_data)} 張信用卡",
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "cards": [], "message": "找不到指定的銀行"}, status=404
        )


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
        bank_name = request.POST.get("bank_name")
        card_id_from_form = request.POST.get("card_id")

        # 檢查資料完整性
        if not bank_name or not card_id_from_form:
            messages.error(request, "請選擇銀行和卡片")
            # 使用輔助函式重新準備表單資料
            context = prepare_card_form_context(
                user_card=user_card,
                is_edit_mode=is_edit_mode,
                include_selected_bank=False,
            )
            return render(request, "users/card_form.html", context)

        try:
            selected_card = CreditCard.objects.get(id=card_id_from_form)

            # 檢查卡片是否真的屬於選的銀行
            if selected_card.bank != bank_name:
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
                    f"成功更新為 {selected_card.bank} {selected_card.name}！",
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
                    f"成功新增 {selected_card.bank} {selected_card.name}！",
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
        card_name = f"{user_card.card.bank} {user_card.card.name}"
        user_card.delete()
        messages.success(request, f"成功刪除 {card_name}！")
        return redirect("users:member_zone")

    # GET 請求：顯示確認刪除頁面
    context = {
        "user_card": user_card,
    }
    return render(request, "users/card_delete_confirm.html", context)


# 允許插件獲得token的函數
@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_token(request):
    try:
        token = Token.objects.get(user=request.user)
        return Response(
            {
                "token": token.key,
                "user_id": request.user.id,
                "username": request.user.username,
                "message": "Token retrieved successfully",
            }
        )
    except Token.DoesNotExist:
        return Response(
            {"error": "Failed to retrieve token"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# 修改密碼 API 端點
@login_required
def change_password(request):
    """修改密碼 API 端點"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只允許 POST 請求'}, status=405)
    
    try:
        data = json.loads(request.body)
        old_password = data.get('old_password', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        errors = {}
        
        # 驗證舊密碼
        if not old_password:
            errors['old_password'] = '舊密碼為必填項目'
        elif not authenticate(username=request.user.username, password=old_password):
            errors['old_password'] = '舊密碼不正確'
        
        # 驗證新密碼
        if not new_password:
            errors['new_password'] = '新密碼為必填項目'
        elif len(new_password) < 8 or len(new_password) > 20:
            errors['new_password'] = '密碼長度必須在 8-20 個字元之間'
        elif not new_password.isalnum():
            errors['new_password'] = '密碼只能包含英文字母和數字，不能有空格或特殊字元'
        elif not any(c.isupper() for c in new_password):
            errors['new_password'] = '密碼必須包含至少一個英文大寫字母'
        elif not any(c.islower() for c in new_password):
            errors['new_password'] = '密碼必須包含至少一個英文小寫字母'
        elif not any(c.isdigit() for c in new_password):
            errors['new_password'] = '密碼必須包含至少一個數字'
        elif new_password == old_password:
            errors['new_password'] = '新密碼不能與舊密碼相同'
        
        # 驗證確認密碼
        if not confirm_password:
            errors['confirm_password'] = '確認密碼為必填項目'
        elif confirm_password != new_password:
            errors['confirm_password'] = '兩次輸入的密碼不一致，請重新確認'
        
        # 如果有錯誤，返回錯誤訊息
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        # 更新密碼
        request.user.set_password(new_password)
        request.user.save()
        
        # 重新登入使用者（因為 set_password 會讓會話失效）
        login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
        
        # 使用 Django Messages 框架
        messages.success(request, '密碼修改成功！')
        
        return JsonResponse({'success': True, 'redirect': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '無效的 JSON 資料'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'修改密碼失敗：{str(e)}'}, status=500)
