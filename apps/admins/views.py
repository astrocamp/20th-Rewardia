from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from apps.cards.models import CreditCard

# from apps.cards.models import Bank
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponse

from apps.rewards.models import PendingReward, RewardCategory
from django.db.models import Q
from django.core.paginator import Paginator


# Create your views here.


# 卡片頁面的函式
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
    # banks = Bank.objects.filter(is_active=True)
    card_networks = CreditCard.CardNetwork
    card_types = CreditCard.CardType
    card_form_data = {
        # "banks": banks,
        "card_networks": card_networks,
        "card_types": card_types,
    }

    if request.method == "POST":
        name = request.POST.get("card")

        bank_id = request.POST["bank"]
        # bank = get_object_or_404(Bank, id=bank_id)

        card_network = request.POST["network"]
        card_type = request.POST["card_type"]
        is_active = request.POST.get("is_active") == "on"

        try:
            new_card = CreditCard.objects.create(
                # name=f"{bank.name} {name}",
                # bank=bank,
                card_network=card_network,
                card_type=card_type,
                is_active=is_active,
            )
            messages.success(request, "新增卡片成功")
            return render(request, "admins/card_row.html", {"card": new_card})
        except:
            messages.success(request, "新增失敗")
            return redirect("admins:cards")
    else:
        return render(request, "admins/new_card.html", card_form_data)


@require_http_methods(["GET"])
def edit_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    # banks = Bank.objects.filter(is_active=True)
    card_networks = CreditCard.CardNetwork
    card_types = CreditCard.CardType
    return render(
        request,
        "admins/edit_card_row.html",
        {
            # "banks": banks,
            "card_networks": card_networks,
            "card_types": card_types,
            "card": card,
        },
    )


@require_http_methods(["POST"])
def update_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    card.name = request.POST.get("card_edit")

    # 因為是foreign key，所以要從Bank那裡的資料庫取得資料
    bank_id = request.POST["bank_edit"]
    # card.bank = get_object_or_404(Bank, id=bank_id)

    card.card_network = request.POST["network_edit"]
    card.card_type = request.POST["card_type_edit"]

    card.is_active = request.POST.get("is_active_edit") == "on"
    card.save()
    print(reverse("admins:cards"))
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
    return render(request, "admins/rewards.html")


def rewards(request):
    """主要的rewards管理頁面 - 替換原本的空函數"""
    status_filter = request.GET.get("status", "PENDING")
    page = request.GET.get("page", 1)

    # 根據狀態過濾
    if status_filter == "ALL":
        pending_rewards = PendingReward.objects.all()
    else:
        pending_rewards = PendingReward.objects.filter(status=status_filter)

    # 排序：最新的在前面
    pending_rewards = pending_rewards.order_by("-created_at")

    # 分頁處理
    paginator = Paginator(pending_rewards, 20)  # 每頁20筆
    page_obj = paginator.get_page(page)

    # 統計數量
    stats = {
        "pending_count": PendingReward.objects.filter(status="PENDING").count(),
        "approved_count": PendingReward.objects.filter(status="APPROVED").count(),
        "rejected_count": PendingReward.objects.filter(status="REJECTED").count(),
        "total_count": PendingReward.objects.count(),
    }

    return render(
        request,
        "admins/rewards.html",
        {
            "pending_rewards": page_obj,
            "current_status": status_filter,
            "stats": stats,
        },
    )


@require_http_methods(["GET"])
def rewards_table(request):
    """HTMX專用：返回表格內容"""
    status_filter = request.GET.get("status", "PENDING")

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

    # 返回更新後的行
    return render(
        request,
        "admins/reward_row.html",
        {
            "reward": pending_reward,
            "current_status": request.GET.get("status", "PENDING"),
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

    # 返回更新後的行
    return render(
        request,
        "admins/reward_row.html",
        {
            "reward": pending_reward,
            "current_status": request.GET.get("status", "PENDING"),
        },
    )


@require_http_methods(["DELETE"])
def delete_pending_reward(request, id):
    """刪除待審核項目"""
    pending_reward = get_object_or_404(PendingReward, pk=id)

    try:
        pending_reward.delete()
        messages.success(request, "刪除成功")
        return HttpResponse("")  # 空響應，表示該行要被移除
    except Exception as e:
        messages.error(request, f"刪除失敗：{str(e)}")
        return HttpResponse(
            f'<tr><td colspan="8" class="text-red-500">刪除失敗：{str(e)}</td></tr>'
        )


@require_http_methods(["POST"])
def batch_approve_rewards(request):
    """批量通過審核"""
    reward_ids = request.POST.getlist("reward_ids")

    if not reward_ids:
        messages.warning(request, "請選擇要處理的項目")
        return redirect("admins:rewards")

    success_count = 0
    error_count = 0

    for reward_id in reward_ids:
        try:
            pending_reward = PendingReward.objects.get(pk=reward_id, status="PENDING")
            pending_reward.approve_and_create_reward_category()
            success_count += 1
        except PendingReward.DoesNotExist:
            error_count += 1
        except Exception:
            error_count += 1

    if success_count > 0:
        messages.success(request, f"成功通過 {success_count} 項審核")
    if error_count > 0:
        messages.error(request, f"{error_count} 項處理失敗")

    return redirect("admins:rewards")


@require_http_methods(["POST"])
def batch_reject_rewards(request):
    """批量駁回審核"""
    reward_ids = request.POST.getlist("reward_ids")

    if not reward_ids:
        messages.warning(request, "請選擇要處理的項目")
        return redirect("admins:rewards")

    success_count = 0
    error_count = 0

    for reward_id in reward_ids:
        try:
            pending_reward = PendingReward.objects.get(pk=reward_id, status="PENDING")
            pending_reward.reject()
            success_count += 1
        except PendingReward.DoesNotExist:
            error_count += 1
        except Exception:
            error_count += 1

    if success_count > 0:
        messages.success(request, f"成功駁回 {success_count} 項審核")
    if error_count > 0:
        messages.error(request, f"{error_count} 項處理失敗")

    return redirect("admins:rewards")


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
        # 更新可編輯欄位
        pending_reward.category = request.POST.get("category", pending_reward.category)
        pending_reward.scope = request.POST.get("scope", pending_reward.scope)

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

    # 返回更新後的行
    return render(
        request,
        "admins/reward_row.html",
        {
            "reward": pending_reward,
            "current_status": request.GET.get("status", "PENDING"),
        },
    )
