from django.urls import path
from . import views
from apps.users.views import member_zone


app_name = "pages"
urlpatterns = [
    path('', views.download, name="download"),
    path('faq/', views.faq, name="faq"),
    path('calculator/', views.calculator, name="calculator"),
    path('card_new/', views.card_new, name="card_new"),
    path('register/', views.register, name="register"),
    path('member/', member_zone, name='member_zone'),
]
