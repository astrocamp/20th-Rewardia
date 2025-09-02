from django.shortcuts import render, redirect
from .data.faq_content import FAQ_DATA
from apps.cards.models import CreditCard

# from apps.analytics.models import OnlineTransaction
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
# from .forms import RewardCalculatorForm


# 假資料 - 消費類別和種類
FAKE_CATEGORIES = {"ONLINE": "網購", "CVS": "超商", "GAS": "加油"}

FAKE_SCOPES = {
    "ONLINE": {
        "momo購物": {"min_rate": 5.0, "max_rate": 8.0},
        "蝦皮購物": {"min_rate": 3.0, "max_rate": 6.0},
    },
    "CVS": {"7-11": {"min_rate": 2.0}, "全家": {"min_rate": 1.5, "max_rate": 3.0}},
    "GAS": {"中油": {"min_rate": 4.0, "max_rate": 7.0}, "台塑": {"min_rate": 3.5}},
}


def download(request):
    return render(request, "pages/download.html")


def calculator(request):
    banks = CreditCard.objects.filter(is_active=True).order_by("name")

    # 消費類別假資料
    categories = [(code, name) for code, name in FAKE_CATEGORIES.items()]

    context = {
        "banks": banks,
        "categories": categories,
    }

    return render(request, "pages/calculator.html", context)


# HTMX 用的 API - 根據銀行取得卡片
def get_cards_by_bank(request):
    bank_id = request.GET.get("bank_select")

    if bank_id:
        cards = CreditCard.objects.filter(bank_id=bank_id, is_active=True).order_by(
            "name"
        )

        # 產生 HTML 選項
        options_html = '<option value="" selected disabled>請選擇卡片</option>'
        for card in cards:
            options_html += f'<option value="{card.id}">{card.name}</option>'

        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請選擇卡片</option>')


# HTMX 用的 API - 根據卡片取得消費類別
def get_categories_by_card(request):
    card_id = request.GET.get("card_select")

    if card_id:
        # 使用假資料
        options_html = '<option value="" selected disabled>請選擇消費類別</option>'
        for code, name in FAKE_CATEGORIES.items():
            options_html += f'<option value="{code}">{name}</option>'
        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請選擇消費類別</option>')


# HTMX 用的 API - 根據類別取得消費種類
def get_scopes_by_category(request):
    category_code = request.GET.get("category_select")

    if category_code and category_code in FAKE_SCOPES:
        options_html = '<option value="" selected disabled>請選擇消費種類</option>'
        for scope_name in FAKE_SCOPES[category_code].keys():
            options_html += f'<option value="{scope_name}">{scope_name}</option>'
        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請選擇消費種類</option>')


def faq(request):
    context = {"faq_categories": FAQ_DATA["categories"]}
    return render(request, "pages/faq.html", context)


def register(request):
    return render(request, "users/register.html")


def login(request):
    return render(request, "users/login.html")


# 使用假資料的計算回饋 API
def calculate_reward(request):
    """計算信用卡回饋 - 使用假資料"""
    if request.method == "POST":
        try:
            # 取得表單資料
            card_id = request.POST.get("card_select")
            category_code = request.POST.get("category_select")
            scope_name = request.POST.get("scope_select")
            amount = request.POST.get("amount_input")

            # 驗證資料
            if not all([card_id, category_code, scope_name, amount]):
                messages.error(request, "請填寫完整資訊！")
                # 同時回傳訊息 HTML
                return HttpResponse("""
                    <div class="result-error">請填寫完整資訊</div>
                    <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
                """)

            amount = float(amount)
            if amount <= 0:
                messages.error(request, "請輸入正確的消費金額！")
                return HttpResponse("""
                    <div class="result-error">請輸入正確的消費金額</div>
                    <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
                """)

            # 取得卡片資訊
            card = CreditCard.objects.get(id=card_id, is_active=True)

            # 使用假資料計算回饋
            if (
                category_code in FAKE_SCOPES
                and scope_name in FAKE_SCOPES[category_code]
            ):
                reward_data = FAKE_SCOPES[category_code][scope_name]
                min_rate = reward_data.get("min_rate")
                max_rate = reward_data.get("max_rate")

                min_reward = amount * min_rate / 100

                if max_rate:
                    max_reward = amount * max_rate / 100
                    result = f"{min_reward:.0f} ~ {max_reward:.0f} 元/點數"
                    messages.success(
                        request,
                        f"計算成功！{card.bank} {card.name} 在 {scope_name} 的回饋為 {result}",
                    )
                else:
                    result = f"{min_reward:.0f} 元/點數"
                    messages.success(
                        request,
                        f"計算成功！{card.bank} {card.name} 在 {scope_name} 的回饋為 {result}",
                    )

                # 回傳結果 + 訊息更新觸發器
                return HttpResponse(f"""
                    <div class="result-success">{result}</div>
                    <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
                """)
            else:
                messages.warning(
                    request,
                    f"找不到 {card.bank} {card.name} 在 {scope_name} 的回饋資訊",
                )
                return HttpResponse("""
                    <div class="result-warning">找不到對應的回饋資訊</div>
                    <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
                """)

        except CreditCard.DoesNotExist:
            messages.error(request, "找不到指定的信用卡，請重新選擇！")
            return HttpResponse("""
                <div class="result-error">找不到指定的信用卡</div>
                <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
            """)
        except ValueError:
            messages.error(request, "金額格式不正確，請輸入數字！")
            return HttpResponse("""
                <div class="result-error">金額格式不正確</div>
                <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
            """)
        except Exception as e:
            messages.error(request, f"計算發生錯誤: {str(e)}，請重試！")
            return HttpResponse(f"""
                <div class="result-error">計算錯誤: {str(e)}</div>
                <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
            """)

    messages.info(request, "請使用正確的請求方法")
    return HttpResponse("""
        <div class="result-info">請使用 POST 方法</div>
        <div hx-get="/get-messages/" hx-target="#messages-container" hx-trigger="load"></div>
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
