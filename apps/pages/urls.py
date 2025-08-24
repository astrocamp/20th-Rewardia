from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import path, include
from . import views
from apps.users.views import member_zone

app_name = "pages"
urlpatterns = [
    path('', views.download, name="download"),
    path('calculator/', views.calculator, name="calculator"),
    path('card_new/', views.card_new, name="card_new"),
    path('member/', member_zone, name='member_zone'),


] + debug_toolbar_urls()
