from django.shortcuts import render
from apps.cards.models import CreditCard


# Create your views here.
def cards(request):
    if request.POST:
        form = CreditCard.objects
        pass
    return render(request, "admins/cards.html")


def rewards(request):
    return render(request, "admins/rewards.html")
