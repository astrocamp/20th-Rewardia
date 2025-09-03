from django.urls import path
from . import views


app_name = "pages"
urlpatterns = [
    path("download/", views.download, name="download"),
    path("", views.main, name="main"),
    path("faq/", views.faq, name="faq"),
    path("calculator/", views.calculator, name="calculator"),
<<<<<<< HEAD
    path("login/", views.login, name="login"),
=======
>>>>>>> d924205 (fixed: 移除main.js中多餘或功能衝突或重複功能的程式碼)
    path("get-cards-by-bank/", views.get_cards_by_bank, name="get_cards_by_bank"),
    path(
        "get-categories-by-card/",
        views.get_categories_by_card,
        name="get_categories_by_card",
    ),
    path(
        "get-scopes-by-category/",
        views.get_scopes_by_category,
        name="get_scopes_by_category",
    ),
    path("get-messages/", views.get_messages, name="get_messages"),
    path("calculate-reward/", views.calculate_reward, name="calculate_reward"),
    path("api/main-data/", views.get_main_data, name="get_main_data"),
]
