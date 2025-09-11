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
]
