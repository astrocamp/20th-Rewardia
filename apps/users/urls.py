from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("member/", views.member_zone, name="member_zone"),
    path("register/", views.register, name="register"),
    path("cards/new/", views.card_form, name="card_new"),
    path("cards/<int:card_id>/edit/", views.card_form, name="card_edit"),
    path("card/<int:card_id>/add-number/", views.card_add_number, name="card_add_number"),
    path("cards/<int:card_id>/delete/", views.card_delete, name="card_delete"),
    path(
        "api/cards-by-bank/<int:bank_id>/",
        views.get_cards_by_bank,
        name="api_cards_by_bank",
    ),
    path("api/get_token", views.get_token, name="get_token"),
    path("change-password/", views.change_password, name="change_password"),
]
