from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "pages"
urlpatterns = [
    path('', views.download, name="download"),
] + debug_toolbar_urls()
