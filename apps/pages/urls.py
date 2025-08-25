from django.urls import path
from . import views


app_name = "pages"
urlpatterns = [
    path('', views.download, name="download"),
    path('faq/', views.faq, name="faq"),
    path('calculator/', views.calculator, name="calculator"),
    path('card_new/', views.card_new, name="card_new"),
    path('register/', views.register, name="register"),


] + debug_toolbar_urls()

    

