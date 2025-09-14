from django.urls import path
from . import views

app_name = "ext_api"


urlpatterns = [
    path(
        "rewards/",
        views.get_rewards,
        name="get_rewards",
    ),
    path(
        "rewards/category/<category>/",
        views.get_category_rewards,
        name="get_category_rewards",
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
        "<bank>/cards/",
        views.get_cards,
        name="get_cards",
    ),
    path(
        "users/new_card/",
        views.new_user_card,
        name="new_user_card",
    ),
    path(
        "users/delete_card/<int:id>",
        views.delete_user_card,
        name="delete_user_card",
    ),
]
