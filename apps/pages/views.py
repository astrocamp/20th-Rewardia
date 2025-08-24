from django.shortcuts import render

def download(request):

    return render(request, "pages/download.html")

def calculator(request):

    return render(request, "pages/calculator.html")

def card_new(request):

    return render(request, "pages/card_new.html")

def faq(request):

    return render(request, "pages/faq.html")

def register(request):

    return render(request, "pages/register.html")

# Create your views here.
