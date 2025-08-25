from django.shortcuts import render

def home(request):
  return render(request, "pages/home.html")

def download(request):
  return render(request, "pages/download.html")

def calculator(request):
  return render(request, "pages/calculator.html")

def faq(request):
  return render(request, "pages/faq.html")

def register(request):
  return render(request, "pages/register.html")

def login(request):
  return render(request, "pages/login.html")
