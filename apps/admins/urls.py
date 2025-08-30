from django.urls import path
from . import views

app_name = "admins"

urlpatterns = [
    path("cards/", views.cards, name="cards"),
    path("new_card/", views.new_card, name="new_card"),
    path("delete_card/<int:id>/", views.delete_card, name="delete_card"),
    path("rewards/", views.rewards, name="rewards"),
]
