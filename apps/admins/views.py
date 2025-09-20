from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from apps.cards.models import CreditCard
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.http import HttpResponse, JsonResponse
from apps.rewards.models import PendingReward
from django.db.models import Q, Count
from apps.cards.storage import MediaStorage
from django.core.paginator import Paginator
import json
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from apps.card_crawler.models import CrawledRecord
from apps.card_crawler.tasks import crawl_roo_task
from apps.nlp_validation.models import AnalysisStatistics
from celery import current_app
from django_celery_results.models import TaskResult
from datetime import  timedelta
from django.utils import timezone


def _get_last_modified_str(card_instance):
    """格式化並返回最後異動時間的字串。"""
    last_modified_time = card_instance.updated_at or card_instance.created_at
    if last_modified_time:
        return last_modified_time.strftime("%Y/%m/%d %H:%M:%S")
    return None


def _get_paginated_rewards_for_bulk_action(request):
    """獲取當前頁面待處理項目的輔助函數"""
    status_filter = request.GET.get("status", PendingReward.Status.PENDING)
    page_number = request.GET.get("page", 1)
    queryset = PendingReward.objects.filter(status=status_filter).order_by(
        "-created_at"
    )
    paginator = Paginator(queryset, 50)
    page_obj = paginator.get_page(page_number)
    return page_obj.object_list, status_filter, page_number


def cards(request):
    sort_param = request.GET.get('sort', '')

    sort_mappings = {
        'is_active_desc': ('-is_active', '-updated_at'),
        'is_active_asc': ('is_active', '-updated_at'),
        'created_at_desc': ('-created_at',),
        'created_at_asc': ('created_at',),
        'updated_at_desc': ('-updated_at',),
        'updated_at_asc': ('updated_at',),
    }
    order_by_args = sort_mappings.get(sort_param, ('-updated_at',))
    cards = CreditCard.objects.order_by(*order_by_args)

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
        except Exception:
            messages.error(request, "新增失敗")
            return redirect("admins:cards")
    else:
        return render(request, "admins/new_card.html", card_form_data)


@require_GET
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


@require_POST
def update_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    card.name = request.POST.get("card_edit")
    card.bank = request.POST["bank_edit"]
    card.is_active = request.POST.get("is_active_edit") == "on"
    card.save()

    messages.success(request, "更新成功")
    url = reverse("admins:cards") + f"#card-{id}"
    return redirect(url)


@require_POST
def delete_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    card.delete()
    messages.success(request, "刪除成功")
    return HttpResponse("")


def rewards(request):
    """主要的rewards管理頁面"""
    page_number = request.GET.get("page", 1)
    if str(page_number) == "1":
        PendingReward.detect_and_soft_delete_duplicates()

    status_filter = request.GET.get("status", PendingReward.Status.PENDING)

    if status_filter == "ALL":
        pending_rewards = PendingReward.objects.select_related("card").all()
    else:
        pending_rewards = PendingReward.objects.select_related("card").filter(
            status=status_filter
        )

    pending_rewards = pending_rewards.order_by("-created_at")

    paginator = Paginator(pending_rewards, 50)  # 一頁50筆
    page_obj = paginator.get_page(page_number)

    stats = PendingReward.objects.aggregate(
        pending_count=Count(
            "id",
            filter=Q(status=PendingReward.Status.PENDING, soft_deleted_at__isnull=True),
        ),
        reviewing_count=Count("id", filter=Q(status=PendingReward.Status.REVIEWING)),
        approved_count=Count(
            "id",
            filter=Q(
                status=PendingReward.Status.APPROVED, soft_deleted_at__isnull=True
            ),
        ),
        rejected_count=Count(
            "id",
            filter=Q(
                status=PendingReward.Status.REJECTED, soft_deleted_at__isnull=True
            ),
        ),
        total_count=Count("id"),
    )

    return render(
        request,
        "admins/rewards.html",
        {
            "page_obj": page_obj,
            "current_status": status_filter,
            "stats": stats,
        },
    )


@require_GET
def rewards_table(request):
    """HTMX：返回表格內容"""
    status_filter = request.GET.get("status", PendingReward.Status.PENDING)

    if status_filter == "ALL":
        pending_rewards = PendingReward.objects.select_related("card").all()
    else:
        pending_rewards = PendingReward.objects.select_related("card").filter(
            status=status_filter
        )

    pending_rewards = pending_rewards.order_by("-created_at")

    return render(
        request,
        "admins/rewards_table.html",
        {
            "pending_rewards": pending_rewards,
            "current_status": status_filter,
        },
    )


@require_POST
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


@require_POST
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
            '<tr><td colspan="9" class="text-red-500">無法刪除此項目，只能刪除重複的項目</td></tr>'
        )


@require_GET
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


@require_POST
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
    cards = CreditCard.objects.filter(is_active=True).order_by("bank", "name")
    return render(request, "admins/image_upload.html", {"cards": cards})


# API: 獲取信用卡列表
def api_cards(request):
    """API: 獲取信用卡列表"""
    cards = CreditCard.objects.filter(is_active=True).order_by("bank", "name")
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

        cards_data.append(
            {
                "id": card.id,
                "name": card.name,
                "bank": card.bank,
                "image": image_url,
                "last_modified": last_modified,
            }
        )

    return JsonResponse({"cards": cards_data})


# API: 上傳圖片
@require_POST
def api_upload_image(request):
    """API: 上傳圖片到 S3"""
    try:
        # 獲取上傳的檔案和卡片 ID
        image_file = request.FILES.get("image")
        card_id = request.POST.get("card_id")

        if not image_file:
            return JsonResponse({"success": False, "error": "沒有選擇圖片檔案"})

        if not card_id:
            return JsonResponse({"success": False, "error": "沒有指定卡片 ID"})

        # 獲取卡片物件
        card = get_object_or_404(CreditCard, id=card_id)

        # 驗證檔案類型, 符合才能上傳
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if image_file.content_type not in allowed_types:
            return JsonResponse({"success": False, "error": "不支援的檔案格式"})

        # 驗證檔案大小 (10MB)
        max_size = 10 * 1024 * 1024
        if image_file.size > max_size:
            return JsonResponse({"success": False, "error": "檔案大小不能超過 10MB"})

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

                content = ContentFile(image_content)

                # 提取檔案名稱，讓 MediaStorage 自動處理路徑
                # card.image.name 可能是 filename.png 或 path/filename.png
                filename = card.image.name.split("/")[-1]
                # MediaStorage location = 'media/credit_cards' 會自動處理完整路徑
                storage.save(filename, content)
            except Exception as e:
                return JsonResponse(
                    {"success": False, "error": f"S3 上傳失敗: {str(e)}"}
                )

        # 重新獲取卡片資料以取得最新的 updated_at 和 image
        card.refresh_from_db()

        # 處理最後異動時間
        last_modified = _get_last_modified_str(card)

        # 確保取得最新的圖片 URL
        image_url = None
        if card.image:
            image_url = storage.url(card.image.name)

        return JsonResponse(
            {
                "success": True,
                "image_url": image_url,
                "last_modified": last_modified,
                "message": "圖片上傳成功",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# API: 刪除圖片
@require_POST
def api_delete_image(request):
    """API: 刪除 S3 圖片"""
    try:
        card_id = request.POST.get("card_id")

        if not card_id:
            return JsonResponse({"success": False, "error": "沒有指定卡片 ID"})

        # 獲取卡片物件
        card = get_object_or_404(CreditCard, id=card_id)

        if not card.image:
            return JsonResponse({"success": False, "error": "該卡片沒有圖片"})

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

        return JsonResponse(
            {"success": True, "last_modified": last_modified, "message": "圖片刪除成功"}
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@require_POST
def bulk_approve_rewards(request):
    """批量通過審核"""
    current_page_rewards, status_filter, page_number = (
        _get_paginated_rewards_for_bulk_action(request)
    )
    success_count = 0

    for reward in current_page_rewards:
        try:
            result = reward.approve_and_create_reward_category()
            if result:
                success_count += 1
            else:
                # 遇到錯誤立即停止並警告
                messages.error(
                    request,
                    f"批量審核失敗！在處理第 {success_count + 1} 個項目「{reward.card.name} - {reward.nlp_category}」時發生錯誤。已成功處理 {success_count} 個項目，剩餘項目未處理。",
                )
                break
        except Exception as e:
            messages.error(
                request,
                f"批量審核中斷！在處理「{reward.card.name} - {reward.nlp_category}」時發生錯誤：{str(e)}。已成功處理 {success_count} 個項目，請檢查後重試。",
            )
            break
    else:
        messages.success(request, f"批量審核完成！成功通過 {success_count} 個項目。")

    return redirect(
        f"{reverse('admins:rewards')}?status={status_filter}&page={page_number}"
    )


@require_POST
def bulk_reject_rewards(request):
    """批量駁回審核"""
    current_page_rewards, status_filter, page_number = (
        _get_paginated_rewards_for_bulk_action(request)
    )
    success_count = 0

    for reward in current_page_rewards:
        try:
            reward.reject()
            success_count += 1
        except Exception as e:
            messages.error(
                request,
                f"批量駁回中斷！在處理「{reward.card.name} - {reward.nlp_category}」時發生錯誤：{str(e)}。已成功處理 {success_count} 個項目，請檢查後重試。",
            )
            break
    else:
        messages.success(request, f"批量駁回完成！成功駁回 {success_count} 個項目。")

    return redirect(
        f"{reverse('admins:rewards')}?status={status_filter}&page={page_number}"
    )

# 排程管理相關 Views
def scheduler(request):
    """排程管理主頁面"""
    return render(request, "admins/scheduler.html")


def api_scheduler_status(request):
    """獲取當前排程狀態"""
    try:
        task = PeriodicTask.objects.filter(
            task="apps.card_crawler.tasks.crawl_roo_task"
        ).first()

        # 檢查 Celery 服務狀態
        celery_worker_active = False
        celery_beat_active = False

        try:
            # 檢查 Celery Worker 是否活躍
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            if stats:
                celery_worker_active = True

            # 檢查最近1分鐘內是否有 beat 心跳
            recent_beat_time = timezone.now() - timedelta(minutes=1)
            recent_heartbeat = TaskResult.objects.filter(
                date_created__gte=recent_beat_time
            ).exists()
            if recent_heartbeat or stats:
                celery_beat_active = True

        except Exception as celery_error:
            print(f"Celery 檢查錯誤: {celery_error}")

        # 檢查是否有正在執行的任務
        is_running = False
        current_task_info = None

        # 檢查最近5分鐘內的任務狀態
        recent_time = timezone.now() - timedelta(minutes=5)
        running_tasks = TaskResult.objects.filter(
            task_name="apps.card_crawler.tasks.crawl_roo_task",
            status="STARTED",
            date_created__gte=recent_time
        ).first()

        if running_tasks:
            is_running = True
            current_task_info = {
                'task_id': running_tasks.task_id,
                'started_at': running_tasks.date_created.strftime('%H:%M:%S')
            }

        if task and task.crontab:
            return JsonResponse({
                'success': True,
                'schedule': {
                    'hour': task.crontab.hour,
                    'minute': task.crontab.minute,
                    'enabled': task.enabled,
                    'last_run_at': task.last_run_at.strftime('%Y-%m-%d %H:%M:%S') if task.last_run_at else None,
                    'is_running': is_running,
                    'current_task': current_task_info,
                    'celery_worker_active': celery_worker_active,
                    'celery_beat_active': celery_beat_active
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'schedule': {
                    'hour': 8,
                    'minute': 0,
                    'enabled': False,
                    'last_run_at': None,
                    'is_running': is_running,
                    'current_task': current_task_info,
                    'celery_worker_active': celery_worker_active,
                    'celery_beat_active': celery_beat_active
                }
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def api_update_schedule(request):
    """更新排程時間"""
    try:
        data = json.loads(request.body)
        hour = int(data.get('hour', 8))
        minute = int(data.get('minute', 0))

        # 獲取或創建 CrontabSchedule
        crontab, created = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # 獲取或創建 PeriodicTask
        task, created = PeriodicTask.objects.get_or_create(
            name='daily-crawl-and-nlp',
            defaults={
                'task': 'apps.card_crawler.tasks.crawl_roo_task',
                'crontab': crontab,
                'enabled': True,
            }
        )

        if not created:
            task.crontab = crontab
            task.save()

        return JsonResponse({
            'success': True,
            'message': f'排程時間已更新為 {hour:02d}:{minute:02d}'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def api_toggle_schedule(request):
    """啟用/停用排程"""
    try:
        task = PeriodicTask.objects.filter(
            task="apps.card_crawler.tasks.crawl_roo_task"
        ).first()

        if task:
            task.enabled = not task.enabled
            task.save()

            status = "啟用" if task.enabled else "停用"
            return JsonResponse({
                'success': True,
                'enabled': task.enabled,
                'message': f'排程已{status}'
            })
        else:
            return JsonResponse({'success': False, 'error': '找不到排程任務'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def api_run_now(request):
    """立即執行爬蟲任務"""
    try:
        # 使用 Celery 立即執行任務
        result = crawl_roo_task.delay()

        return JsonResponse({
            'success': True,
            'task_id': result.id,
            'message': '爬蟲任務已開始執行'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def api_crawled_records(request):
    """獲取爬蟲執行記錄"""
    try:
        records = CrawledRecord.objects.order_by('-created_at')[:20]

        data = []
        for record in records:
            # 判斷是否有錯誤
            has_errors = bool(record.errors)
            error_message = None

            if has_errors:
                # 爬蟲記錄：使用字典裡面的實際內容數量
                error_count = 0
                if isinstance(record.errors, dict):
                    # 計算字典中實際的錯誤項目數量
                    error_count = len([v for v in record.errors.values() if v])
                elif isinstance(record.errors, list):
                    error_count = len(record.errors)

                if error_count > 0:
                    error_message = f"{error_count} 個錯誤"
                else:
                    # 如果計算出來是 0，表示沒有實際錯誤
                    has_errors = False

            data.append({
                'id': record.id,
                'created_at': record.created_at.strftime('%m/%d %H:%M'),
                'total_cards': record.total_cards,
                'total_time': f"{record.total_time:.1f}",
                'average_time': f"{record.average_time:.3f}",
                'errors': error_message,
                'has_errors': has_errors
            })

        return JsonResponse({
            'success': True,
            'records': data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def api_analysis_records(request):
    """獲取 NLP 分析記錄"""
    try:
        records = AnalysisStatistics.objects.order_by('-created_at')[:20]

        data = []
        for record in records:
            # 判斷是否有錯誤
            has_errors = bool(record.errors)
            error_message = None

            if has_errors:
                # NLP分析記錄：使用 error_count 欄位判斷
                error_count = 0
                if isinstance(record.errors, dict) and 'error_count' in record.errors:
                    error_count = record.errors['error_count']
                elif isinstance(record.errors, list):
                    error_count = len(record.errors)
                elif isinstance(record.errors, dict):
                    error_count = len(record.errors)

                if error_count > 0:
                    error_message = f"{error_count} 個錯誤"
                else:
                    # 如果計算出來是 0，表示沒有實際錯誤
                    has_errors = False

            data.append({
                'id': record.id,
                'created_at': record.created_at.strftime('%m/%d %H:%M'),
                'analyzed_count': record.analyzed_count,
                'total_time': f"{record.total_time:.1f}",
                'average_time': f"{record.average_time:.3f}",
                'errors': error_message,
                'has_errors': has_errors
            })

        return JsonResponse({
            'success': True,
            'records': data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

