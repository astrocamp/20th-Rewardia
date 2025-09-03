from django.shortcuts import render
from .data.faq_content import FAQ_DATA
from apps.cards.models import CreditCard
from apps.rewards.models import PendingReward, RewardCategory
from django.http import HttpResponse, JsonResponse # Added JsonResponse
from django.db.models import Prefetch
import json


def download(request):
    return render(request, "pages/download.html")


def main(request):
    return render(request, "pages/main.html")


def get_main_data(request):
    # 使用 prefetch_related 優化查詢，避免 N+1 問題
    cards = CreditCard.objects.filter(is_active=True).prefetch_related(
        'reward_categories',  # 預取已確認回饋
        'pending_rewards'     # 預取待審核回饋
    ).order_by('bank', 'name')

    # 一次性獲取所有需要的資料
    banks_set = set()
    pending_categories_set = set()
    all_cards_data = []
    
    for card in cards:
        banks_set.add(card.bank)
        rewards_data = []
        
        # 處理已確認的回饋類別
        for reward in card.reward_categories.all():
            limit_parts = []
            if reward.max_spending:
                limit_parts.append(f"上限 ${reward.max_spending:,.0f}")
            if reward.requires_activation:
                limit_parts.append("需登錄")
            if reward.is_rotating:
                limit_parts.append("季度輪替")
                
            rewards_data.append({
                'category': reward.get_category_display(),
                'rate': f"{reward.rate}%",
                'limit': " ".join(limit_parts),
                'category_code': reward.category,
                'source': 'confirmed'
            })
        
        # 處理待審核回饋
        for reward in card.pending_rewards.all():
            if reward.nlp_category:
                pending_categories_set.add(reward.nlp_category)
                
                rate_display = "N/A"
                if reward.max_rate is not None:
                    rate_display = f"{reward.max_rate}%"
                elif reward.min_rate is not None:
                    rate_display = f"{reward.min_rate}%"

                rewards_data.append({
                    'category': f"{reward.nlp_category} ({reward.nlp_scope})",
                    'rate': rate_display,
                    'limit': reward.extracted_sentence or '',
                    'category_code': reward.nlp_category,
                    'source': 'pending'
                })

        all_cards_data.append({
            'id': card.id,
            'name': card.name,
            'bank': card.bank,
            'card_type': card.get_card_type_display() if card.card_type else '',
            'card_network': card.get_card_network_display() if card.card_network else '',
            'foreign_fee': float(card.foreign_transaction_fee) if card.foreign_transaction_fee else 0,
            'image': f'https://via.placeholder.com/300x180.png?text={card.name.replace(" ", "+")}',
            'rewards': rewards_data[:6]
        })

    # 處理銀行資料（重用已收集的資料）
    banks = [{
        'code': bank.lower().replace(' ', '_'), 
        'name': bank
    } for bank in sorted(banks_set)]

    # 處理回饋類別選項（重用已收集的資料）
    reward_category_map = {}
    reward_categories_choices = []
    
    for category in sorted(pending_categories_set):
        category_code = category.upper().replace(' ', '_').replace('/', '_')
        reward_categories_choices.append((category_code, category))
        reward_category_map[category_code] = category

    return JsonResponse({
        'all_cards_data': all_cards_data,
        'banks': banks,
        'reward_categories_choices': reward_categories_choices,
        'reward_category_map': reward_category_map,
    }, safe=False)





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
