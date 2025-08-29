from django.shortcuts import render


# Create your views here.
def cards(request):
    return render(request, "admins/cards.html")


def rewards(request):
    return render(request, "admins/rewards.html")
