from django.shortcuts import render, redirect
from .data.faq_content import FAQ_DATA
from apps.cards.models import CreditCard
from django.http import HttpResponse


def download(request):
    return render(request, "pages/download.html")


def calculator(request):
    # banks = Bank.objects.filter(is_active=True).order_by("name")
    # merchants = Merchant.objects.filter(is_active=True).order_by("name")
    # payment_methods = OnlineTransaction.PaymentMethod.choices

    payment_methods = [
        ("CREDIT", "信用卡"),
        ("WALLET", "數位錢包"),
        ("MOBILE", "行動支付"),
    ]

    # 海外消費選項
    overseas_options = [
        ("YES", "是"),
        ("NO", "否"),
    ]

    context = {
        # "banks": banks,
        # "merchants": merchants,
        "payment_methods": payment_methods,
        "overseas_options": overseas_options,
    }

    return render(request, "pages/calculator.html", context)


# HTMX 用的 API - 根據銀行取得卡片
# def get_cards_by_bank(request):
# bank_id = request.GET.get("bank_select")

# if bank_id:
# cards = CreditCard.objects.filter(bank_id=bank_id, is_active=True).order_by(
# "name"
# )

# 產生 HTML 選項
#     options_html = '<option value="" selected disabled>請選擇卡片</option>'
#     for card in cards:
#         options_html += f'<option value="{card.id}">{card.name}</option>'

#     return HttpResponse(options_html)

# return HttpResponse('<option value="" selected disabled>請選擇卡片</option>')


def faq(request):
    context = {"faq_categories": FAQ_DATA["categories"]}
    return render(request, "pages/faq.html", context)


def register(request):
    return render(request, "users/register.html")


def login(request):
    return render(request, "users/login.html")
