from django.urls import path
from . import views

app_name = "admins"

urlpatterns = [
    path("cards/", views.cards, name="cards"),
    path("new_card/", views.new_card, name="new_card"),
    path("edit_card/<int:id>/", views.edit_card, name="edit_card"),
    path("update_card/<int:id>/", views.update_card, name="update_card"),
    path("delete_card/<int:id>/", views.delete_card, name="delete_card"),
    path("rewards/", views.rewards, name="rewards"),
    path("rewards/table/", views.rewards_table, name="rewards_table"),
    path(
        "rewards/<int:id>/approve/",
        views.approve_pending_reward,
        name="approve_pending_reward",
    ),
    path(
        "rewards/<int:id>/reject/",
        views.reject_pending_reward,
        name="reject_pending_reward",
    ),
    path(
        "rewards/<int:id>/delete/",
        views.delete_pending_reward,
        name="delete_pending_reward",
    ),
    path(
        "rewards/<int:id>/hard-delete/",
        views.hard_delete_pending_reward,
        name="hard_delete_pending_reward",
    ),
    path(
        "rewards/<int:id>/edit/", views.edit_pending_reward, name="edit_pending_reward"
    ),
    path(
        "rewards/<int:id>/update/",
        views.update_pending_reward,
        name="update_pending_reward",
    ),
    # 圖片上傳相關 URL
    path("image_upload/", views.image_upload, name="image_upload"),
    path("api/cards/", views.api_cards, name="api_cards"),
    path("api/upload-image/", views.api_upload_image, name="api_upload_image"),
    path("api/delete-image/", views.api_delete_image, name="api_delete_image"),
]
