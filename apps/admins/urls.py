from django.urls import path
from . import views

app_name = "admins"

urlpatterns = [
    path("cards/", views.cards, name="cards"),
]
