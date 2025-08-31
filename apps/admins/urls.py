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
]
