from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('member/', views.member_zone, name='member_zone'),
]