from django.shortcuts import render
from .data.faq_content import FAQ_DATA

def home(request):
  return render(request, "pages/home.html")

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
  return render(request, "pages/register.html")

def login(request):
  return render(request, "pages/login.html")
