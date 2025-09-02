from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from apps.cards.models import CreditCard
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponse


# Create your views here.


# 卡片頁面的函式
def cards(request):
    cards = CreditCard.objects.order_by("-updated_at")
    return render(
        request,
        "admins/cards.html",
        {
            "cards": cards,
        },
    )


def new_card(request):
    banks = CreditCard.Bank
    card_networks = CreditCard.CardNetwork
    card_types = CreditCard.CardType
    card_form_data = {
        "banks": banks,
        "card_networks": card_networks,
        "card_types": card_types,
    }

    if request.method == "POST":
        name = request.POST.get("card")
        bank = request.POST["bank"]
        card_network = request.POST["network"]
        card_type = request.POST["card_type"]
        is_active = request.POST.get("is_active") == "on"

        try:
            new_card = CreditCard.objects.create(
                name=f"{bank} {name}",
                bank=bank,
                card_network=card_network,
                card_type=card_type,
                is_active=is_active,
            )
            messages.success(request, "新增卡片成功")
            return render(request, "admins/card_row.html", {"card": new_card})
        except:
            messages.success(request, "新增失敗")
            return redirect("admins:cards")
    else:
        return render(request, "admins/new_card.html", card_form_data)


@require_http_methods(["GET"])
def edit_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    banks = CreditCard.Bank
    card_networks = CreditCard.CardNetwork
    card_types = CreditCard.CardType
    return render(
        request,
        "admins/edit_card_row.html",
        {
            "banks": banks,
            "card_networks": card_networks,
            "card_types": card_types,
            "card": card,
        },
    )


@require_http_methods(["POST"])
def update_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    card.name = request.POST.get("card_edit")
    card.bank = request.POST["bank_edit"]
    card.card_network = request.POST["network_edit"]
    card.card_type = request.POST["card_type_edit"]
    card.is_active = request.POST.get("is_active_edit") == "on"
    card.save()

    messages.success(request, "更新成功")
    url = reverse("admins:cards") + f"#card-{id}"
    return redirect(url)


@require_http_methods(["POST"])
def delete_card(request, id):
    card = get_object_or_404(CreditCard, pk=id)
    card.delete()
    messages.success(request, "刪除成功")
    return HttpResponse("")


def rewards(request):
    return render(request, "admins/rewards.html")
