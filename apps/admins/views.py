from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from apps.cards.models import CreditCard
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponse, JsonResponse
from apps.rewards.models import PendingReward, RewardCategory
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from apps.cards.storage import MediaStorage
import json


def _get_last_modified_str(card_instance):
    """格式化並返回最後異動時間的字串。"""
    last_modified_time = card_instance.updated_at or card_instance.created_at
    if last_modified_time:
        return last_modified_time.strftime('%Y/%m/%d %H:%M:%S')
    return None


# 卡片頁面
def cards(request):
    cards = CreditCard.objects.order_by("-updated_at")
    return render(
        request,
        "admins/cards.html",
        {
            "cards": cards,
        },
    )


def new_card(request):
    banks = CreditCard.Bank
    card_form_data = {
        "banks": banks,
    }

    if request.method == "POST":
        name = request.POST.get("card")
        bank = request.POST["bank"]
        is_active = request.POST.get("is_active") == "on"

        try:
            CreditCard.objects.create(
                name=name,
                bank=bank,
                is_active=is_active,
            )
            messages.success(request, "新增卡片成功")
            return redirect("admins:cards")
        except:
            messages.error(request, "新增失敗")
            return redirect("admins:cards")
    else:
        return render(request, "admins/new_card.html", card_form_data)


@require_http_methods(["GET"])
def edit_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    banks = CreditCard.Bank
    return render(
        request,
        "admins/edit_card_row.html",
        {
            "banks": banks,
            "card": card,
        },
    )


@require_http_methods(["POST"])
def update_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    card.name = request.POST.get("card_edit")
    card.bank = request.POST["bank_edit"]
    card.is_active = request.POST.get("is_active_edit") == "on"
    card.save()

    messages.success(request, "更新成功")
    url = reverse("admins:cards") + f"#card-{id}"
    return redirect(url)


@require_http_methods(["POST"])
def delete_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    card.delete()
    messages.success(request, "刪除成功")
    return HttpResponse("")


def rewards(request):
    """主要的rewards管理頁面"""
    PendingReward.detect_and_soft_delete_duplicates()

    status_filter = request.GET.get("status", PendingReward.Status.PENDING)

    if status_filter == "ALL":
        pending_rewards = PendingReward.objects.all()
    else:
        pending_rewards = PendingReward.objects.filter(status=status_filter)

    pending_rewards = pending_rewards.order_by("-created_at")

    stats = PendingReward.objects.aggregate(
        pending_count=Count("id", filter=Q(status=PendingReward.Status.PENDING)),
        reviewing_count=Count("id", filter=Q(status=PendingReward.Status.REVIEWING)),
        approved_count=Count("id", filter=Q(status=PendingReward.Status.APPROVED)),
        rejected_count=Count("id", filter=Q(status=PendingReward.Status.REJECTED)),
        total_count=Count("id"),
    )

    return render(
        request,
        "admins/rewards.html",
        {
            "pending_rewards": pending_rewards,
            "current_status": status_filter,
            "stats": stats,
        },
    )


@require_http_methods(["GET"])
def rewards_table(request):
    """HTMX：返回表格內容"""
    status_filter = request.GET.get("status", PendingReward.Status.PENDING)

    if status_filter == "ALL":
        pending_rewards = PendingReward.objects.all()
    else:
        pending_rewards = PendingReward.objects.filter(status=status_filter)

    pending_rewards = pending_rewards.order_by("-created_at")

    return render(
        request,
        "admins/rewards_table.html",
        {
            "pending_rewards": pending_rewards,
            "current_status": status_filter,
        },
    )


@require_http_methods(["POST"])
def approve_pending_reward(request, id):
    """通過審核"""
    pending_reward = get_object_or_404(PendingReward, pk=id)

    if pending_reward.status == PendingReward.Status.PENDING:
        try:
            reward_category = pending_reward.approve_and_create_reward_category()
            if reward_category:
                messages.success(request, f"通過審核：{pending_reward}")
            else:
                messages.error(request, "審核通過失敗")
        except Exception as e:
            messages.error(request, f"審核失敗：{str(e)}")
    else:
        messages.warning(request, "此項目已經處理過了")

    return render(
        request,
        "admins/reward_row.html",
        {
            "reward": pending_reward,
            "current_status": request.GET.get("status", PendingReward.Status.PENDING),
        },
    )


@require_http_methods(["POST"])
def reject_pending_reward(request, id):
    """駁回審核"""
    pending_reward = get_object_or_404(PendingReward, pk=id)

    if pending_reward.status == PendingReward.Status.PENDING:
        try:
            pending_reward.reject()
            messages.success(request, f"駁回審核：{pending_reward}")
        except Exception as e:
            messages.error(request, f"駁回失敗：{str(e)}")
    else:
        messages.warning(request, "此項目已經處理過了")

    return render(
        request,
        "admins/reward_row.html",
        {
            "reward": pending_reward,
            "current_status": request.GET.get("status", PendingReward.Status.PENDING),
        },
    )


@require_http_methods(["DELETE"])
def delete_pending_reward(request, id):
    """刪除待審核項目"""
    pending_reward = get_object_or_404(PendingReward, pk=id)

    try:
        pending_reward.delete()
        messages.success(request, "刪除成功")
        return HttpResponse("")
    except Exception as e:
        messages.error(request, f"刪除失敗：{str(e)}")
        return HttpResponse(
            f'<tr><td colspan="8" class="text-red-500">刪除失敗：{str(e)}</td></tr>'
        )


@require_http_methods(["DELETE"])
def hard_delete_pending_reward(request, id):
    """硬刪除軟刪除的項目"""
    pending_reward = get_object_or_404(PendingReward, pk=id)

    # 只允許硬刪除軟刪除且在審核中狀態的資料
    if (
        pending_reward.status == PendingReward.Status.REVIEWING
        and pending_reward.soft_deleted_at
    ):
        try:
            pending_reward.delete()
            messages.success(request, "硬刪除成功")
            return HttpResponse("")
        except Exception as e:
            messages.error(request, f"硬刪除失敗：{str(e)}")
            return HttpResponse(
                f'<tr><td colspan="9" class="text-red-500">硬刪除失敗：{str(e)}</td></tr>'
            )
    else:
        messages.error(request, "無法刪除此項目，只能刪除重複的項目")
        return HttpResponse(
            f'<tr><td colspan="9" class="text-red-500">無法刪除此項目，只能刪除重複的項目</td></tr>'
        )


@require_http_methods(["GET"])
def edit_pending_reward(request, id):
    """編輯待審核項目 - 返回編輯表單"""
    pending_reward = get_object_or_404(PendingReward, pk=id)

    return render(
        request,
        "admins/edit_reward_row.html",
        {
            "reward": pending_reward,
        },
    )


@require_http_methods(["POST"])
def update_pending_reward(request, id):
    """更新待審核項目"""
    pending_reward = get_object_or_404(PendingReward, pk=id)

    try:
        pending_reward.nlp_category = request.POST.get(
            "nlp_category", pending_reward.nlp_category
        )
        pending_reward.nlp_scope = request.POST.get(
            "nlp_scope", pending_reward.nlp_scope
        )

        min_rate = request.POST.get("min_rate")
        if min_rate:
            pending_reward.min_rate = float(min_rate)

        max_rate = request.POST.get("max_rate")
        if max_rate:
            pending_reward.max_rate = float(max_rate)

        pending_reward.reward_type = request.POST.get(
            "reward_type", pending_reward.reward_type
        )
        pending_reward.save()

        messages.success(request, "更新成功")

    except Exception as e:
        messages.error(request, f"更新失敗：{str(e)}")

    return render(
        request,
        "admins/reward_row.html",
        {
            "reward": pending_reward,
            "current_status": request.GET.get("status", PendingReward.Status.PENDING),
        },
    )



# 以下是圖片上傳相關
def image_upload(request):
    """圖片上傳管理頁面"""
    cards = CreditCard.objects.filter(is_active=True).order_by('bank', 'name')
    return render(request, 'admins/image_upload.html', {'cards': cards})


# API: 獲取信用卡列表
def api_cards(request):
    """API: 獲取信用卡列表"""
    cards = CreditCard.objects.filter(is_active=True).order_by('bank', 'name')
    cards_data = []
    
    for card in cards:
        # 生成正確的圖片 URL
        image_url = None
        if card.image:
            storage = MediaStorage()
            # 使用 MediaStorage.url() 來生成正確的 URL，它會自動添加 media/ 前綴
            image_url = storage.url(card.image.name)
        
        # 處理最後異動時間
        last_modified = _get_last_modified_str(card)
        
        cards_data.append({
            'id': card.id,
            'name': card.name,
            'bank': card.bank,
            'image': image_url,
            'last_modified': last_modified
        })
    
    return JsonResponse({'cards': cards_data})


# API: 上傳圖片
@require_POST
def api_upload_image(request):
    """API: 上傳圖片到 S3"""
    try:
        # 獲取上傳的檔案和卡片 ID
        image_file = request.FILES.get('image')
        card_id = request.POST.get('card_id')
        
        if not image_file:
            return JsonResponse({'success': False, 'error': '沒有選擇圖片檔案'})
        
        if not card_id:
            return JsonResponse({'success': False, 'error': '沒有指定卡片 ID'})
        
        # 獲取卡片物件
        card = get_object_or_404(CreditCard, id=card_id)
        
        # 驗證檔案類型, 符合才能上傳
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return JsonResponse({'success': False, 'error': '不支援的檔案格式'})
        
        # 驗證檔案大小 (10MB)
        max_size = 10 * 1024 * 1024
        if image_file.size > max_size:
            return JsonResponse({'success': False, 'error': '檔案大小不能超過 10MB'})
        
        # 儲存圖片到模型
        card.image = image_file
        card.save()
        
        # 確保圖片已上傳到 S3
        storage = MediaStorage()
        
        # 檢查圖片是否在 S3 中存在
        if not storage.exists(card.image.name):
            # 如果不存在，手動上傳
            try:
                card.image.seek(0)
                image_content = card.image.read()
                from django.core.files.base import ContentFile
                content = ContentFile(image_content)
                
                # 提取檔案名稱，讓 MediaStorage 自動處理路徑
                # card.image.name 可能是 filename.png 或 path/filename.png
                filename = card.image.name.split('/')[-1]
                # MediaStorage location = 'media/credit_cards' 會自動處理完整路徑
                storage.save(filename, content)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'S3 上傳失敗: {str(e)}'})
        
        # 重新獲取卡片資料以取得最新的 updated_at 和 image
        card.refresh_from_db()
        
        # 處理最後異動時間
        last_modified = _get_last_modified_str(card)
        
        # 確保取得最新的圖片 URL
        image_url = None
        if card.image:
            image_url = storage.url(card.image.name)
        
        return JsonResponse({
            'success': True, 
            'image_url': image_url,
            'last_modified': last_modified,
            'message': '圖片上傳成功'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# API: 刪除圖片
@require_POST
def api_delete_image(request):
    """API: 刪除 S3 圖片"""
    try:
        card_id = request.POST.get('card_id')
        
        if not card_id:
            return JsonResponse({'success': False, 'error': '沒有指定卡片 ID'})
        
        # 獲取卡片物件
        card = get_object_or_404(CreditCard, id=card_id)
        
        if not card.image:
            return JsonResponse({'success': False, 'error': '該卡片沒有圖片'})
        
        # 刪除 S3 中的圖片
        try:
            storage = MediaStorage()
            if storage.exists(card.image.name):
                storage.delete(card.image.name)
        except Exception as e:
            pass  # 靜默處理 S3 刪除錯誤，不影響資料庫清理
        
        # 清空資料庫中的圖片欄位
        card.image = None
        card.save()
        
        # 重新獲取卡片資料以取得最新的 updated_at
        card.refresh_from_db()
        
        # 處理最後異動時間
        last_modified = _get_last_modified_str(card)
        
        return JsonResponse({
            'success': True, 
            'last_modified': last_modified,
            'message': '圖片刪除成功'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

