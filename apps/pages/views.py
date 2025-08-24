from django.shortcuts import render

def download(request):

    return render(request, "pages/download.html")

def calculator(request):

    return render(request, "pages/calculator.html")

def card_new(request):

    return render(request, "pages/card_new.html")


def member_zone(request):

    return render(request, "pages/member_zone.html")
