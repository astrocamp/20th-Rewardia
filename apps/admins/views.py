from django.shortcuts import render, redirect
from apps.cards.models import CreditCard
from apps.cards.models import Bank
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponse


# Create your views here.


# 卡片頁面的函式
def cards(request):
    banks = Bank.objects.filter(is_active=True)
    card_networks = CreditCard.CardNetwork
    card_types = CreditCard.CardType
    cards = CreditCard.objects.order_by("-updated_at")
    return render(
        request,
        "admins/cards.html",
        {
            "banks": banks,
            "card_networks": card_networks,
            "card_types": card_types,
            "cards": cards,
        },
    )


@require_POST
def new_card(request):
    name = request.POST.get("card")
    bank = request.POST["bank"]
    card_network = request.POST["network"]
    card_type = request.POST["card_type"]
    foreign_transaction_fee = request.POST.get("foreign")
    is_active = request.POST.get("is_active") == "on"
    new_card = CreditCard.objects.create(
        name=f"{Bank.objects.get(id=bank).name} {name}",
        bank=Bank.objects.get(id=bank),
        card_network=card_network,
        card_type=card_type,
        foreign_transaction_fee=foreign_transaction_fee,
        is_active=is_active,
    )
    if new_card:
        messages.success(request, "新增卡片成功")
        return render(request, "admins/card_row.html", {"card": new_card})
    else:
        messages.success(request, "新增失敗")
        return redirect("admins:cards")


def edit_card(request, id):
    pass


@require_http_methods(["POST", "DELETE"])
def delete_card(request, id):
    card = CreditCard.objects.get(pk=id)
    card.delete()
    messages.success(request, "刪除成功")
    return HttpResponse("")


def rewards(request):
    return render(request, "admins/rewards.html")
