from django.urls import path
from . import views
from django.shortcuts import redirect

def superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/sessions/login/')
        if not request.user.is_superuser:
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper

app_name = "admins"

urlpatterns = [
    path("cards/", superuser_required(views.cards), name="cards"),
    path("new_card/", superuser_required(views.new_card), name="new_card"),
    path("edit_card/<int:id>/", superuser_required(views.edit_card), name="edit_card"),
    path("update_card/<int:id>/", superuser_required(views.update_card), name="update_card"),
    path("delete_card/<int:id>/", superuser_required(views.delete_card), name="delete_card"),
    path("rewards/", superuser_required(views.rewards), name="rewards"),
    path("rewards/table/", superuser_required(views.rewards_table), name="rewards_table"),
    path(
        "rewards/<int:id>/approve/",
        superuser_required(views.approve_pending_reward),
        name="approve_pending_reward",
    ),
    path(
        "rewards/<int:id>/reject/",
        superuser_required(views.reject_pending_reward),
        name="reject_pending_reward",
    ),
    path(
        "rewards/<int:id>/delete/",
        superuser_required(views.delete_pending_reward),
        name="delete_pending_reward",
    ),
    path(
        "rewards/<int:id>/hard-delete/",
        superuser_required(views.hard_delete_pending_reward),
        name="hard_delete_pending_reward",
    ),
    path(
        "rewards/<int:id>/edit/", superuser_required(views.edit_pending_reward), name="edit_pending_reward"
    ),
    path(
        "rewards/<int:id>/update/",
        superuser_required(views.update_pending_reward),
        name="update_pending_reward",
    ),
    # 圖片上傳相關 URL
    path("image_upload/", superuser_required(views.image_upload), name="image_upload"),
    path("api/cards/", superuser_required(views.api_cards), name="api_cards"),
    path("api/upload-image/", superuser_required(views.api_upload_image), name="api_upload_image"),
    path("api/delete-image/", superuser_required(views.api_delete_image), name="api_delete_image"),
    # 批量操作
    path(
        "rewards/bulk-approve/",
        superuser_required(views.bulk_approve_rewards),
        name="bulk_approve_rewards",
    ),
    path(
        "rewards/bulk-reject/",
        superuser_required(views.bulk_reject_rewards),
        name="bulk_reject_rewards",
    ),
    # 排程管理相關 URL
    path("scheduler/", superuser_required(views.scheduler), name="scheduler"),
    path("scheduler/api/status/", superuser_required(views.api_scheduler_status), name="api_scheduler_status"),
    path("scheduler/api/update/", superuser_required(views.api_update_schedule), name="api_update_schedule"),
    path("scheduler/api/toggle/", superuser_required(views.api_toggle_schedule), name="api_toggle_schedule"),
    path("scheduler/api/run-now/", superuser_required(views.api_run_now), name="api_run_now"),
    path("scheduler/api/crawled-records/", superuser_required(views.api_crawled_records), name="api_crawled_records"),
    path("scheduler/api/analysis-records/", superuser_required(views.api_analysis_records), name="api_analysis_records"),
]
