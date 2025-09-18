from django.urls import path
from . import views

app_name = "ext_api"


urlpatterns = [
    path(
        "rewards/cards/<int:id>",
        views.get_card_rewards,
        name="get_card_rewards",
    ),
    path(
        "rewards/scope/<scope>/",
        views.get_merchant_rewards,
        name="get_merchant_rewards",
    ),
    path(
        "users/<int:id>/cards/",
        views.get_user_cards,
        name="get_user_cards",
    ),
    path(
        "banks/",
        views.get_banks,
        name="get_banks",
    ),
    path(
        "banks/<bank>/cards/",
        views.get_cards,
        name="get_cards",
    ),
    path(
        "find_rate/<str:bank_name>/<int:card_id>/<str:category_name>",
        views.get_category_rate,
        name="get_category_rate",
    ),
    path(
        "find_rate/<str:bank_name>/<int:card_id>/<str:category_name>/<str:scope_name>",
        views.get_merchant_rate,
        name="get_merchant_rate",
    ),
    path(
        "users/new_card/<int:id>",
        views.new_user_card,
        name="new_user_card",
    ),
    path(
        "users/delete_card/<int:id>/",
        views.delete_user_card,
        name="delete_user_card",
    ),
    path(
        "ocr/vision/",
        views.ocr_with_vision,
        name="ocr_with_vision",
    ),
]
