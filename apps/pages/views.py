from django.shortcuts import render
from .data.faq_content import FAQ_DATA
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory
from django.http import HttpResponse, JsonResponse # Added JsonResponse
from django.db.models import Prefetch
from django.utils.html import escape
import json


def download(request):
    return render(request, "pages/download.html")

def main(request):
    return render(request, "pages/main.html")

def faq(request):
    context = {"faq_categories": FAQ_DATA["categories"]}
    return render(request, "pages/faq.html", context)


def get_main_data(request):
    cards = CreditCard.objects.filter(is_active=True).prefetch_related(
        'reward_categories'  # 預取回饋分類
    ).order_by('bank', 'name')

    # 一次性獲取所有需要的資料
    banks_set = set()
    reward_categories_set = set()
    merchants_set = set()
    all_cards_data = []
    
    for card in cards:
        banks_set.add(card.bank)
        rewards_data = []
        
        # 處理回饋分類
        for reward in card.reward_categories.filter(is_active=True):
            reward_categories_set.add(reward.category)
            merchants_set.add(reward.scope)
            
            # 處理回饋率顯示
            min_rate, max_rate = reward.min_rate, reward.max_rate
            if min_rate is None and max_rate is None:
                rate_display = "N/A"
            elif min_rate == max_rate or max_rate is None:
                rate_display = f"{min_rate}%"
            elif min_rate is None:
                rate_display = f"{max_rate}%"
            else:
                rate_display = f"{min_rate}%-{max_rate}%"
                
            rewards_data.append({
                'category': reward.category,
                'scope': reward.scope,
                'rate': rate_display,
                'reward_type': reward.reward_type,
                'category_code': reward.category,
                'source': 'confirmed'
            })

        # 處理圖片欄位
        if card.image:
            # 如果有上傳的圖片，使用 MediaStorage 生成正確的 URL
            from apps.cards.storage import MediaStorage
            storage = MediaStorage()
            image_url = storage.url(card.image.name)
        else:
            # 如果沒有圖片，使用本地 placeholder 或不同的 placeholder 服務
            # 使用 picsum.photos 作為替代的 placeholder 服務
            image_url = f'https://picsum.photos/300/180?random={card.id}'
        
        all_cards_data.append({
            'id': card.id,
            'name': card.name,
            'bank': card.bank,
            'image': image_url,
            'rewards': rewards_data
        })

    # 處理銀行資料
    banks = [{
        'code': bank.lower().replace(' ', '_'), 
        'name': bank
    } for bank in sorted(banks_set)]

    # 處理回饋類別選項
    reward_category_map = {}
    reward_categories_choices = []
    
    for category in sorted(reward_categories_set):
        category_code = category.upper().replace(' ', '_').replace('/', '_')
        reward_categories_choices.append((category_code, category))
        reward_category_map[category_code] = category

    # 處理店家選項
    merchants = [{'code': merchant.lower().replace(' ', '_'), 'name': merchant} for merchant in sorted(merchants_set)]

    return JsonResponse({
        'all_cards_data': all_cards_data,
        'banks': banks,
        'merchants': merchants,
        'reward_categories_choices': reward_categories_choices,
        'reward_category_map': reward_category_map,
    }, safe=False)


# API - 根據優惠類別獲取對應的店家列表
def get_merchants_by_category(request):
    """根據優惠類別獲取對應的店家列表"""
    category_code = request.GET.get("category_code")
    
    if category_code:
        # 直接查詢所有回饋類別來建立映射
        reward_categories = RewardCategory.objects.filter(is_active=True).values_list('category', flat=True).distinct()
        
        # 建立類別代碼到類別名稱的映射
        reward_category_map = {}
        for category in reward_categories:
            category_code_mapped = category.upper().replace(' ', '_').replace('/', '_')
            reward_category_map[category_code_mapped] = category
        
        # 獲取實際的類別名稱
        category_name = reward_category_map.get(category_code)
        
        if category_name:
            # 查詢該類別下的所有店家
            merchants = RewardCategory.objects.filter(
                category=category_name,
                is_active=True
            ).values_list('scope', flat=True).distinct().order_by('scope')
            
            merchants_list = [{'code': merchant.lower().replace(' ', '_'), 'name': merchant} for merchant in merchants]
            
            return JsonResponse({
                'merchants': merchants_list
            })
    
    return JsonResponse({'merchants': []})

# 共用的選項生成函數
def _generate_options_html(default_text, items, value_field, text_field):
    """生成 HTML 選項的共用函數"""
    options_html = f'<option value="" selected disabled>{escape(default_text)}</option>'
    for item in items:
        if isinstance(item, dict):
            value = escape(item[value_field])
            text = escape(item[text_field])
        else:
            value = escape(getattr(item, value_field))
            text = escape(getattr(item, text_field))
        options_html += f'<option value="{value}">{text}</option>'
    return options_html



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
        cards = CreditCard.objects.filter(bank=bank_name, is_active=True).order_by("name")
        return HttpResponse(_generate_options_html(
            "請先選擇銀行，再選擇卡片", 
            cards, 
            "id", 
            "name"
        ))

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

        return HttpResponse(_generate_options_html(
            "請先選擇卡片", 
            categories, 
            "category", 
            "category"
        ))

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

        return HttpResponse(_generate_options_html(
            "請先選擇消費類別", 
            scopes, 
            "scope", 
            "scope"
        ))

    return HttpResponse('<option value="" selected disabled>請先選擇消費類別</option>')




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
