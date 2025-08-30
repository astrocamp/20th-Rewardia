from django.urls import path
from . import views


app_name = "pages"
urlpatterns = [
    path("", views.download, name="download"),
    path("faq/", views.faq, name="faq"),
    path("calculator/", views.calculator, name="calculator"),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
]
