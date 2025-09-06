from django.shortcuts import render
from .data.faq_content import FAQ_DATA
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory
from django.http import HttpResponse


def download(request):
    return render(request, "pages/download.html")


def calculator(request):
    banks = (
        CreditCard.objects.filter(is_active=True)
        .values_list("bank", flat=True)
        .distinct()
        .order_by("bank")
    )

    context = {
        "banks": banks,
    }

    return render(request, "pages/calculator.html", context)


# HTMX 用的 API - 根據銀行取得卡片
def get_cards_by_bank(request):
    bank_name = request.GET.get("bank_select")

    if bank_name:
        cards = CreditCard.objects.filter(bank=bank_name, is_active=True).order_by(
            "name"
        )

        # 產生 HTML 選項
        options_html = '<option value="" selected disabled>請先選擇銀行，再選擇卡片</option>'
        for card in cards:
            options_html += f'<option value="{card.id}">{card.name}</option>'

        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請先選擇銀行，再選擇卡片</option>')


# HTMX 用的 API - 根據卡片取得消費類別
def get_categories_by_card(request):
    card_id = request.GET.get("card_select")

    if card_id:
        # 從選定的信用卡找出所有不重複的消費類別（暫時移除 is_active 限制）
        categories = (
            RewardCategory.objects.filter(card_id=card_id)
            .values("category")
            .distinct()
            .order_by("category")
        )

        options_html = '<option value="" selected disabled>請先選擇卡片</option>'
        for category in categories:
            options_html += f'<option value="{category["category"]}">{category["category"]}</option>'

        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請先選擇卡片</option>')


# HTMX 用的 API - 根據類別取得消費種類
def get_scopes_by_category(request):
    card_id = request.GET.get("card_select")
    category_name = request.GET.get("category_select")

    if card_id and category_name:
        # 從選定的信用卡和類別找出所有消費種類（暫時移除 is_active 限制）
        scopes = (
            RewardCategory.objects.filter(card_id=card_id, category=category_name)
            .values("scope")
            .distinct()
            .order_by("scope")
        )

        options_html = '<option value="" selected disabled>請先選擇消費類別</option>'
        for scope in scopes:
            options_html += (
                f'<option value="{scope["scope"]}">{scope["scope"]}</option>'
            )

        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請先選擇消費類別</option>')


def faq(request):
    context = {"faq_categories": FAQ_DATA["categories"]}
    return render(request, "pages/faq.html", context)


def register(request):
    return render(request, "users/register.html")


def login(request):
    return render(request, "users/login.html")


def calculate_reward(request):
    """計算信用卡回饋 - 使用 Django Form 驗證"""
    if request.method == "POST":
        from .forms import RewardCalculatorForm

        form = RewardCalculatorForm(request.POST)

        if form.is_valid():
            card_id = form.cleaned_data["card_select"]
            category_name = form.cleaned_data["category_select"]
            scope_name = form.cleaned_data["scope_select"]
            amount = form.cleaned_data["amount_input"]

            try:
                # ✅ 取得活躍的卡片資訊
                card = CreditCard.objects.get(id=card_id, is_active=True)

                # 資料庫找到對應的回饋規則（暫時移除 is_active 限制）
                try:
                    reward_rule = RewardCategory.objects.get(
                        card_id=card_id, category=category_name, scope=scope_name
                    )

                    min_rate = reward_rule.min_rate
                    max_rate = reward_rule.max_rate

                    if not min_rate and not max_rate:
                        # 都沒有資料
                        result = "資料不足無法計算"

                    elif min_rate and not max_rate:
                        # 只有最低回饋率
                        reward_amount = amount * min_rate / 100
                        result = f"最低{min_rate}% 回饋，回饋金額：{reward_amount:.0f} 元/點數"

                    elif not min_rate and max_rate:
                        # 只有最高回饋率
                        reward_amount = amount * max_rate / 100
                        result = f"最高{max_rate}% 回饋，回饋金額：{reward_amount:.0f} 元/點數"

                    else:
                        # 兩個都有
                        if min_rate == max_rate:
                            reward_amount = amount * min_rate / 100
                            result = f"{min_rate}% 回饋，回饋金額：{reward_amount:.0f} 元/點數"
                        else:
                            min_reward = amount * min_rate / 100
                            max_reward = amount * max_rate / 100
                            result = f"最低{min_rate}% ~ 最高{max_rate}% 回饋，回饋金額：{min_reward:.0f} ~ {max_reward:.0f} 元/點數"

                    return HttpResponse(f"""
                        <div class="result-success">{result}</div>
                    """)

                except RewardCategory.DoesNotExist:
                    return HttpResponse("""
                        <div class="result-warning">找不到對應的回饋資訊</div>
                    """)

            except CreditCard.DoesNotExist:
                return HttpResponse("""
                    <div class="result-error">找不到指定的信用卡</div>
                """)
            except Exception as e:
                return HttpResponse(f"""
                    <div class="result-error">計算錯誤：{str(e)}</div>
                """)
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)

            error_text = "、".join(error_messages)
            return HttpResponse(f"""
                <div class="result-error">{error_text}</div>
            """)

    return HttpResponse("""
        <div class="result-info">請使用 POST 方法</div>
    """)


# HTMX 用的 Messages API
def get_messages(request):
    """取得 Django Messages 並轉成 HTML"""
    from django.contrib.messages import get_messages

    messages_html = ""
    messages_list = get_messages(request)

    for message in messages_list:
        css_class = {
            "debug": "alert-secondary",
            "info": "alert-info",
            "success": "alert-success",
            "warning": "alert-warning",
            "error": "alert-danger",
        }.get(message.tags, "alert-info")

        messages_html += f"""
            <div class="alert {css_class} alert-dismissible fade show" role="alert">
                {message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        """

    return HttpResponse(messages_html)
