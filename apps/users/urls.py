from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("member/", views.member_zone, name="member_zone"),
    path("register/", views.register, name="register"),
    path("cards/new/", views.card_form, name="card_new"),
    path("cards/<int:card_id>/edit/", views.card_form, name="card_edit"),
    path("cards/<int:card_id>/delete/", views.card_delete, name="card_delete"),
]
