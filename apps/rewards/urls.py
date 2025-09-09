from django.urls import path
from . import views

app_name = "rewards"


urlpatterns = [
    path(
        "api/rewards/",
        views.get_rewards,
        name="get_rewards",
    ),
    path(
        "api/rewards/category/<category>",
        views.get_category_rewards,
        name="get_category_rewards",
    ),
    path(
        "api/rewards/scope/<scope>",
        views.get_merchant_rewards,
        name="get_merchant_rewards",
    ),
]
