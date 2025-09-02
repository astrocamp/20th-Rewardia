from django.shortcuts import render, redirect
from .data.faq_content import FAQ_DATA
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q


def download(request):
    return render(request, "pages/download.html")


def calculator(request):
    # 暫時移除 is_active 限制，因為資料庫中的值是 NULL
    banks = (
        CreditCard.objects.all()
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
        # 根據銀行名稱找到該銀行的所有信用卡（暫時移除 is_active 限制）
        cards = CreditCard.objects.filter(bank=bank_name).order_by("name")

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
        # 從選定的信用卡找出所有不重複的消費類別（暫時移除 is_active 限制）
        categories = (
            RewardCategory.objects.filter(card_id=card_id)
            .values("category")
            .distinct()
            .order_by("category")
        )

        options_html = '<option value="" selected disabled>請選擇消費類別</option>'
        for category in categories:
            options_html += f'<option value="{category["category"]}">{category["category"]}</option>'

        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請選擇消費類別</option>')


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

        options_html = '<option value="" selected disabled>請選擇消費種類</option>'
        for scope in scopes:
            options_html += (
                f'<option value="{scope["scope"]}">{scope["scope"]}</option>'
            )

        return HttpResponse(options_html)

    return HttpResponse('<option value="" selected disabled>請選擇消費種類</option>')


def faq(request):
    context = {"faq_categories": FAQ_DATA["categories"]}
    return render(request, "pages/faq.html", context)


def register(request):
    return render(request, "users/register.html")


def login(request):
    return render(request, "users/login.html")


def calculate_reward(request):
    """計算信用卡回饋 - 使用真實資料"""
    if request.method == "POST":
        try:
            # 取得表單資料
            card_id = request.POST.get("card_select")
            category_name = request.POST.get("category_select")
            scope_name = request.POST.get("scope_select")
            amount = request.POST.get("amount_input")

            # 驗證資料
            if not all([card_id, category_name, scope_name, amount]):
                return HttpResponse("""
                    <div class="result-error">請填寫完整資訊</div>
                """)

            amount = float(amount)
            if amount <= 0:
                return HttpResponse("""
                    <div class="result-error">請輸入正確的消費金額</div>
                """)

            # 取得卡片資訊（暫時移除 is_active 限制）
            card = CreditCard.objects.get(id=card_id)

            # 資料庫找到對應的回饋規則（暫時移除 is_active 限制）
            try:
                reward_rule = RewardCategory.objects.get(
                    card_id=card_id, category=category_name, scope=scope_name
                )

                # 計算回饋金額
                min_rate = reward_rule.min_rate
                max_rate = reward_rule.max_rate

                # 四種情況的判斷邏輯
                if not min_rate and not max_rate:
                    # 都沒有資料
                    result = "資料不足無法計算"

                elif min_rate and not max_rate:
                    # 只有最低回饋率
                    reward_amount = amount * float(min_rate) / 100
                    result = (
                        f"最低{min_rate}% 回饋，回饋金額：{reward_amount:.0f} 元/點數"
                    )

                elif not min_rate and max_rate:
                    # 只有最高回饋率
                    reward_amount = amount * float(max_rate) / 100
                    result = (
                        f"最高{max_rate}% 回饋，回饋金額：{reward_amount:.0f} 元/點數"
                    )

                else:
                    # 兩個都有
                    if min_rate == max_rate:
                        reward_amount = amount * float(min_rate) / 100
                        result = (
                            f"{min_rate}% 回饋，回饋金額：{reward_amount:.0f} 元/點數"
                        )
                    else:
                        min_reward = amount * float(min_rate) / 100
                        max_reward = amount * float(max_rate) / 100
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
        except ValueError:
            return HttpResponse("""
                <div class="result-error">金額格式不正確</div>
            """)
        except Exception as e:
            return HttpResponse(f"""
                <div class="result-error">計算錯誤：{str(e)}</div>
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
