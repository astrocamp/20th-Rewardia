from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "rewards"

# 因為使用了Django REST API的viewsets寫法，所以urls要改用他們的router寫法
router = DefaultRouter()
router.register(r"rewards", views.RewardViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
]
