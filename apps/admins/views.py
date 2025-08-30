from django.shortcuts import render
from apps.cards.models import CreditCard
from apps.cards.models import Bank


# Create your views here.
def cards(request):
    banks = Bank.objects.filter(is_active=True)
    card_networks = CreditCard.CardNetwork
    card_types = CreditCard.CardType

    if request.POST:
        name = request.POST.get("card")
        bank = request.POST.get("bank")
        card_network = request.POST.get("network")
        card_type = request.POST.get("card_type")
        foreign_transaction_fee = request.POST.get("foreign")
        is_active = request.POST.get("is_active")
        CreditCard.objects.create(
            name=name,
            bank=bank,
            network=card_network,
            card_type=card_type,
            foreign_transaction_fee=foreign_transaction_fee,
            is_active=is_active,
        )
    return render(
        request,
        "admins/cards.html",
        {
            "banks": banks,
            "card_networks": card_networks,
            "card_types": card_types,
        },
    )


def rewards(request):
    return render(request, "admins/rewards.html")
