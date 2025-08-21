from django.shortcuts import render

def download(request):

    return render(request, "pages/download.html")

def calculator(request):

    return render(request, "pages/calculator.html")
