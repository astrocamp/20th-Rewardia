from django.shortcuts import render
from .data.faq_content import FAQ_DATA

def download(request):
  return render(request, "pages/download.html")

def calculator(request):
  return render(request, "pages/calculator.html")

def faq(request):
  context = {
    'faq_categories': FAQ_DATA['categories']
  }
  return render(request, "pages/faq.html", context)

def register(request):
  return render(request, "users/register.html")

def login(request):
  return render(request, "users/login.html")

def card_new(request):
  return render(request, "pages/card_new.html")

