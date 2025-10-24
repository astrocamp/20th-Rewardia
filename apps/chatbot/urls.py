from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chat_api, name='chat_api'),
]
