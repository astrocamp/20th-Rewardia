from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
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
from django.db.models import Case, When, Value, DecimalField
from collections import defaultdict
try:
    from allauth.socialaccount.models import SocialAccount
except ImportError:
    SocialAccount = None
import json
import logging
import re
from apps.cards.models import CreditCard
from apps.cards.storage import MediaStorage
from apps.rewards.models import RewardCategory
from .models import UserCard
from .bin_service import get_bin_service


def get_card_image_url(card):
    """取得卡片圖片 URL 的共用函數"""
    if card.image:
        storage = MediaStorage()
        return storage.url(card.image.name)
    return None


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
    cards = CreditCard.objects.filter(is_active=True).only("id", "name", "bank", "image")

    # 處理卡片資料，包含圖片 URL
    processed_cards = []
    for card in cards:
        # 處理圖片 URL
        image_url = get_card_image_url(card)
        
        processed_cards.append({
            'id': card.id,
            'name': card.name,
            'bank': card.bank,
            'image_url': image_url
        })

    # 取得所有有卡片的銀行名稱 (去重複)
    bank_names = cards.values_list("bank", flat=True).distinct().order_by("bank")
    # 轉換成模板期望的格式
    banks = [{"name": bank_name} for bank_name in bank_names if bank_name]

    context = {
        "banks": banks,
        "cards": processed_cards,  # 使用處理後的卡片資料
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
        # 檢查用戶是否有 Google OAuth 關聯
        has_google_oauth = False
        if SocialAccount:
            has_google_oauth = SocialAccount.objects.filter(
                user=request.user, 
                provider='google'
            ).exists()
        else:
            # 如果 allauth 沒有安裝或導入失敗，預設為 False
            pass
        
        context['has_google_oauth'] = has_google_oauth
        # 獲取用戶的卡片資料，只顯示 is_active=True 的卡片
        user_cards = request.user.user_cards.select_related("card").filter(card__is_active=True)
        
        # 一次性獲取所有相關的回饋資料，避免 N+1 查詢問題
        card_ids = [user_card.card.id for user_card in user_cards]
        all_rewards = RewardCategory.objects.filter(
            card_id__in=card_ids,
            is_active=True
        ).annotate(
            max_effective_rate=Case(
                When(max_rate__isnull=False, then='max_rate'),
                When(min_rate__isnull=False, then='min_rate'),
                default=Value(0),
                output_field=DecimalField()
            )
        ).select_related('card')
        
        # 按卡片 ID 分組回饋資料
        rewards_by_card = defaultdict(list)
        for reward in all_rewards:
            rewards_by_card[reward.card.id].append(reward)
        
        # 處理每張卡片的詳細資訊
        processed_cards = []
        for user_card in user_cards:
            # 處理圖片 URL
            image_url = get_card_image_url(user_card.card)
            
            # 處理卡號
            masked_card_number = user_card.get_masked_card_number() if user_card.card_number_encrypted else "尚未登記卡號"
            
            # 處理最高回饋率 - 從預先查詢的資料中獲取
            card_rewards = rewards_by_card.get(user_card.card.id, [])
            
            # 按 category 分組，保留每個 category 的最高費率項目
            category_highest = {}
            for reward in card_rewards:
                category = reward.category
                if category not in category_highest or reward.max_effective_rate > category_highest[category].max_effective_rate:
                    category_highest[category] = reward
            
            # 按費率排序，取前三高
            top_rewards = sorted(category_highest.values(), key=lambda x: x.max_effective_rate, reverse=True)[:3]
            
            # 格式化前三高回饋率顯示
            top_rewards_display = []
            for reward in top_rewards:
                if reward.min_rate is not None and reward.max_rate is not None:
                    if reward.min_rate == reward.max_rate:
                        reward_text = f"{reward.category} {reward.min_rate:.2f}%"
                    else:
                        reward_text = f"{reward.category} {reward.min_rate:.2f}%~{reward.max_rate:.2f}%"
                elif reward.min_rate is not None:
                    reward_text = f"{reward.category} {reward.min_rate:.2f}%"
                elif reward.max_rate is not None:
                    reward_text = f"{reward.category} {reward.max_rate:.2f}%"
                else:
                    continue
                top_rewards_display.append(reward_text)
            
            processed_cards.append({
                'user_card': user_card,
                'image_url': image_url,
                'masked_card_number': masked_card_number,
                'top_rewards_display': top_rewards_display
            })
        
        context["processed_cards"] = processed_cards

    return render(request, "users/member_zone.html", context)




def get_cards_by_bank_htmx(request):
    bank_name = request.GET.get('bank_name', '')

    if not bank_name:
        return render(request, 'users/partials/card_options.html', {
            'cards': [],
            'message': '請選擇發卡銀行'
        })

    try:
        # 取得該銀行的所有啟用信用卡
        cards = (
            CreditCard.objects.filter(bank=bank_name, is_active=True)
            .only("id", "name")
            .order_by("name")
        )

        return render(request, 'users/partials/card_options.html', {
            'cards': cards,
            'bank_name': bank_name
        })

    except Exception as e:
        return render(request, 'users/partials/card_options.html', {
            'cards': [],
            'message': '載入卡片時發生錯誤'
        })


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
        card_number = request.POST.get("card_number", "").strip()
        

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

        # 驗證卡號（如果提供了）- 卡號不是必填
        clean_number = ""
        if card_number and card_number.strip():
            # 先移除空格，再檢查是否包含非數字字符
            card_number_no_spaces = card_number.replace(' ', '')
            if re.search(r'[^\d]', card_number_no_spaces):
                messages.error(request, "卡號格式異常：只能包含數字，不允許字母或特殊符號")
                context = prepare_card_form_context(
                    user_card=user_card,
                    is_edit_mode=is_edit_mode,
                    include_selected_bank=False,
                )
                return render(request, "users/card_form.html", context)
            
            clean_number = re.sub(r'\D', '', card_number)
            if len(clean_number) < 12 or len(clean_number) > 19:
                messages.error(request, "卡號長度必須在12-19位之間")
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
                
                # 如果有提供卡號，則加密並儲存
                if clean_number:
                    user_card.set_card_number(clean_number)
                
                user_card.save()
                messages.success(
                    request,
                    f"成功更新為 {selected_card.bank} {selected_card.name}！",
                )
                
                # 保持在編輯頁面，不跳轉
                context = prepare_card_form_context(
                    user_card=user_card, is_edit_mode=True, include_selected_bank=True
                )
                return render(request, "users/card_form.html", context)
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

                # 創建新卡片
                new_user_card = UserCard.objects.create(
                    user=request.user, card=selected_card, nickname="", is_primary=False
                )
                
                # 如果有提供卡號，則加密並儲存
                if clean_number:
                    new_user_card.set_card_number(clean_number)
                    new_user_card.save()
                
                messages.success(
                    request,
                    f"成功新增 {selected_card.bank} {selected_card.name}！",
                )

                # 新增卡片成功後轉址到會員專區
                return redirect('users:member_zone')

        except CreditCard.DoesNotExist:
            messages.error(request, "選擇的卡片不存在")
            # 使用輔助函式重新準備表單資料
            context = prepare_card_form_context(
                user_card=user_card,
                is_edit_mode=is_edit_mode,
                include_selected_bank=False,
            )
            return render(request, "users/card_form.html", context)


# 新增卡號功能
@login_required
def card_add_number(request, card_id):
    """為用戶卡片新增卡號（從無到有）"""
    user_card = get_object_or_404(UserCard, id=card_id, user=request.user)
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_number = data.get('card_number', '').strip()
            
            if not card_number:
                return JsonResponse({
                    'success': False,
                    'message': '卡號不能為空'
                })
            
            # 檢查是否已經有卡號
            # 嘗試解密驗證是否為有效的加密卡號
            try:
                decrypted = user_card.get_card_number()
                if decrypted and decrypted.strip():
                    return JsonResponse({
                        'success': False,
                        'message': '此卡片已有卡號，無法重複新增'
                    })
            except (ValueError, TypeError, UnicodeDecodeError, AttributeError) as e:
                # 預期的解密失敗（資料格式問題），允許新增
                logger = logging.getLogger(__name__)
                logger.debug(f"Card number decryption failed (expected): {e}")
                pass
            except Exception as e:
                # 未預期的錯誤，記錄並允許新增（避免阻塞用戶操作）
                logger = logging.getLogger(__name__)
                logger.warning(f"Unexpected error in card number decryption: {e}")
                pass
            
            # 移除所有非數字字符
            clean_number = re.sub(r'\D', '', card_number)
            
            if len(clean_number) < 12 or len(clean_number) > 19:
                return JsonResponse({
                    'success': False,
                    'message': '卡號長度必須在12-19位之間'
                })
            
            # 新增卡號
            user_card.set_card_number(clean_number)
            user_card.save()
            
            card_name = f"{user_card.card.bank} {user_card.card.name}"
            return JsonResponse({
                'success': True,
                'message': f"成功為 {card_name} 新增卡號！"
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '請求格式錯誤'
            })
        except (ValueError, TypeError, UnicodeDecodeError, AttributeError) as e:
            # 資料處理相關的預期錯誤
            logger = logging.getLogger(__name__)
            logger.error(f"Data processing error in card_add_number: {e}")
            return JsonResponse({
                'success': False,
                'message': '資料處理失敗，請檢查輸入格式'
            })
        except Exception as e:
            # 未預期的系統錯誤
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in card_add_number: {e}")
            return JsonResponse({
                'success': False,
                'message': '系統錯誤，請稍後再試'
            })
    
    return JsonResponse({
        'success': False,
        'message': '只允許 POST 請求'
    }, status=405)


# 刪除功能
@login_required
def card_delete(request, card_id):
    # 確保這張卡片屬於當前用戶
    user_card = get_object_or_404(UserCard, id=card_id, user=request.user)

    if request.method == "POST":
        # 處理刪除請求
        card_name = f"{user_card.card.bank} {user_card.card.name}"
        user_card.delete()
        return JsonResponse({
            'success': True,
            'message': f"成功刪除 {card_name}！"
        })

    # GET 請求：返回錯誤
    return JsonResponse({
        'success': False,
        'message': '只允許 POST 請求'
    }, status=405)


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


@api_view(["POST"])
def identify_bank_by_bin(request):
    """
    根據信用卡前6碼辨識發卡銀行
    
    接收格式: {"bin_code": "123456"}
    返回格式: {
        "success": true/false,
        "bank_name_chinese": "銀行中文名稱",
        "bank_name_english": "銀行英文名稱",
        "message": "訊息"
    }
    """
    try:
        # 解析請求資料 (使用 DRF 的 request.data)
        bin_code = request.data.get('bin_code', '').strip()
        
        if not bin_code:
            return JsonResponse({
                'success': False,
                'message': 'BIN 碼不能為空'
            }, status=400)
        
        # 驗證 BIN 碼格式
        if len(bin_code) != 6 or not bin_code.isdigit():
            return JsonResponse({
                'success': False,
                'message': 'BIN 碼必須是6位數字'
            }, status=400)
        
        # 使用 BIN 服務進行辨識
        result = get_bin_service().identify_bank_by_bin(bin_code)
        
        # 返回結果
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '無效的 JSON 資料'
        }, status=400)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"銀行辨識 API 錯誤: {e}")
        return JsonResponse({
            'success': False,
            'message': '銀行辨識服務暫時無法使用'
        }, status=500)
