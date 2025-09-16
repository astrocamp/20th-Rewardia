# Chatbot 資料庫查詢服務
import logging
import functools
from django.db.models import Q, Value, DecimalField
from django.db.models.functions import Coalesce
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory
from apps.users.models import UserCard, User
from apps.chatbot.knowledge_base import REWARDIA_KNOWLEDGE_BASE, SYSTEM_PROMPT
from apps.chatbot.config import (
    BANK_MAPPING, COMMON_KEYWORDS, PERSONAL_QUERY_KEYWORDS, REWARD_TYPE_KEYWORDS, 
    NAVIGATION_KEYWORDS, COMPARISON_KEYWORDS, PERSONAL_RECOMMENDATION_KEYWORDS, 
    CARD_COMPARISON_RECOMMENDATION_KEYWORDS, RESPONSE_MESSAGES, PAGE_MAPPING,
    INTENT_KEYWORDS, FORMAT_CONFIG, DATABASE_CONFIG
)

# 設定日誌記錄器
logger = logging.getLogger(__name__)


def handle_database_errors(default_return=None, log_error=True):
    """
    統一的資料庫錯誤處理裝飾器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                return default_return if default_return is not None else []
        return wrapper
    return decorator


class ChatbotDataService:
    """AI 助理資料庫查詢服務"""
    
    # 快取變數
    _cached_categories = None
    
    @staticmethod
    def _get_reward_queryset_with_sorting():
        """取得帶有排序邏輯的 RewardCategory QuerySet"""
        return RewardCategory.objects.filter(is_active=True).annotate(
            sort_rate=Coalesce('max_rate', 'min_rate', Value(0, output_field=DecimalField()))
        ).order_by('-sort_rate')
    
    @staticmethod
    def format_reward_rate(min_rate=None, max_rate=None, reward_dict=None):
        """統一的回饋率格式化方法"""
        if reward_dict:
            min_rate = reward_dict.get('min_rate', '') or ''
            max_rate = reward_dict.get('max_rate', '') or ''
        
        rate = f"{min_rate or ''}-{max_rate or ''}".strip('-')
        return f"{rate}{FORMAT_CONFIG['rate_suffix']}" if rate else FORMAT_CONFIG['unknown_rate']
    
    @staticmethod
    def _format_reward_rate(min_rate, max_rate):
        """向後相容的格式化方法"""
        return ChatbotDataService.format_reward_rate(min_rate, max_rate)
    
    @staticmethod
    def _format_reward_rate_from_dict(reward_dict):
        """向後相容的格式化方法"""
        return ChatbotDataService.format_reward_rate(reward_dict=reward_dict)
    
    @staticmethod
    def _build_reward_list_response(rewards, title, prefix=""):
        """建構回饋列表回應的共用方法"""
        if not rewards:
            return ""
        
        response = f"{prefix}{title}\n"
        for reward in rewards:
            rate_display = ChatbotDataService._format_reward_rate_from_dict(reward)
            response += f"- {reward['bank']} {reward['card_name']}: {rate_display} {reward['reward_type']}\n"
        return response
    
    @staticmethod
    @handle_database_errors(default_return=[])
    def get_cards_by_bank(bank_name):
        """根據銀行名稱查詢信用卡"""
        # 使用統一的銀行映射配置
        bank_config = BANK_MAPPING.get(bank_name, {'keywords': [bank_name]})
        search_terms = bank_config['keywords']
        
        query = Q()
        for term in search_terms:
            query |= Q(bank__icontains=term)
        
        cards = CreditCard.objects.filter(
            query,
            is_active=True
        ).values('name', 'bank')
        return list(cards)
    
    @staticmethod
    @handle_database_errors(default_return=[])
    def get_cards_by_category(category, limit=5):
        """根據消費類別查詢最佳回饋信用卡（使用 reward_categories 表格）"""
        # 查詢該類別回饋率最高的卡片（搜尋 category、scope 和 reward_type 欄位）
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(category__iexact=category) | Q(scope__iexact=category) | Q(reward_type__iexact=category) |
            Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category)
        ).select_related('card')[:limit]
        
        result = []
        for reward in rewards:
            # 使用 max_rate 作為主要回饋率，如果沒有則使用 min_rate
            rate = float(reward.max_rate) if reward.max_rate else float(reward.min_rate) if reward.min_rate else 0
            result.append({
                'card_name': reward.card.name,
                'bank': reward.card.bank,
                'rate': rate,
                'reward_type': reward.reward_type,
                'scope': reward.scope,
                'min_rate': float(reward.min_rate) if reward.min_rate else None,
                'max_rate': float(reward.max_rate) if reward.max_rate else None
            })
        return result
    
    @staticmethod
    @handle_database_errors(default_return=[])
    def get_all_active_cards():
        """取得所有啟用的信用卡"""
        cards = CreditCard.objects.filter(is_active=True).values('name', 'bank')
        return list(cards)
    
    @staticmethod
    @handle_database_errors(default_return=[])
    def get_user_cards(user_id):
        """取得用戶的信用卡（需要登入）"""
        if not user_id:
            return []
        
        user = User.objects.get(pk=user_id)
        user_cards = UserCard.objects.filter(
            user=user,
            is_active=True
        ).select_related('card').values(
            'card__name',
            'card__bank',
            'nickname',
            'is_primary'
        )
        return list(user_cards)
    
    @staticmethod
    @handle_database_errors(default_return=[])
    def get_card_rewards_by_category(card_name, category):
        """取得特定卡片在特定類別的回饋"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(category__iexact=category) | Q(scope__iexact=category) | Q(reward_type__iexact=category) |
            Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category),
            card__name=card_name
        ).select_related('card')
        
        result = []
        for reward in rewards:
            result.append({
                'bank': reward.card.bank,
                'card_name': reward.card.name,
                'category': reward.category,
                'scope': reward.scope,
                'min_rate': reward.min_rate,
                'max_rate': reward.max_rate,
                'reward_type': reward.reward_type
            })
        return result
    
    @staticmethod
    @handle_database_errors(default_return=[])
    def get_card_all_rewards(card_name):
        """取得特定卡片的所有回饋"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            card__name=card_name
        ).select_related('card')
        
        result = []
        for reward in rewards:
            result.append({
                'bank': reward.card.bank,
                'card_name': reward.card.name,
                'category': reward.category,
                'scope': reward.scope,
                'min_rate': reward.min_rate,
                'max_rate': reward.max_rate,
                'reward_type': reward.reward_type
            })
        return result
    
    
    @staticmethod
    def get_reward_categories():
        """取得所有消費類別（從 reward_categories 表格）"""
        if ChatbotDataService._cached_categories is None:
            try:
                # 從 reward_categories 表格獲取消費類別、範圍和回饋類型
                from django.db.models import Value, CharField
                from django.db.models.functions import Concat
                
                categories = RewardCategory.objects.filter(
                    is_active=True
                ).annotate(
                    combined_category=Concat(
                        'category', Value(' '), 'scope', Value(' '), 'reward_type',
                        output_field=CharField()
                    )
                ).values_list('combined_category', flat=True).distinct()
                ChatbotDataService._cached_categories = list(categories)
            except Exception as e:
                logger.error(f"Error in get_reward_categories: {str(e)}", exc_info=True)
                ChatbotDataService._cached_categories = []
        return ChatbotDataService._cached_categories
    
    @staticmethod
    @handle_database_errors(default_return=[])
    def get_supported_banks():
        """取得支援的銀行列表（從實際資料庫資料去重）"""
        # 從實際資料庫獲取銀行列表並去重
        banks = CreditCard.objects.filter(is_active=True).values_list('bank', flat=True).distinct()
        # 過濾掉排除列表中的值和空值
        banks = [bank for bank in banks if bank and bank not in FORMAT_CONFIG['filter_exclude']]
        
        # 除錯：記錄原始銀行資料
        logger.info(f"原始銀行資料: {list(banks)}")
        
        # 簡化版本：直接回傳所有銀行，不進行映射
        # 這樣可以確保所有資料庫中的銀行都會被顯示
        result = sorted(list(set(banks)))  # 去重並排序
        
        logger.info(f"最終銀行列表: {result}")
        return result


class ChatbotResponseBuilder:
    """AI 助理回應建構器"""

    # 動態產生一份包含所有銀行關鍵字的列表
    _bank_related_keywords = ['信用卡', '卡', '銀行', '信託'] + [
        keyword 
        for bank_config in BANK_MAPPING.values() 
        for keyword in bank_config['keywords']
    ]

    @staticmethod
    def _create_base_intent(user_message):
        """建立基礎意圖結構"""
        return {
            "banks": [],
            "categories": [],
            "is_comparison": "比較" in user_message,
            "is_listing_banks": ("銀行" in user_message and ("列出" in user_message or "哪些" in user_message or "條列式" in user_message)),
            "has_reward_keyword": "回饋" in user_message,
            "has_card_keyword": "信用卡" in user_message or "卡" in user_message,
            "raw_message": user_message,
            "is_context_question": False,
            "is_card_benefit_question": False,
            "context_banks": [],
            # 導航相關意圖
            "is_navigation": False,
            "navigation_type": None,
            "navigation_target": None,
            # 比較相關意圖
            "comparison_type": None,
            "comparison_cards": [],
            "is_highest_query": False,
            "is_bank_limited": False,
            # 個人化推薦意圖
            "is_personal_recommendation": False,
            "recommendation_type": None,
            "recommendation_category": None,
            "recommendation_bank": None,
            # 卡片比較推薦意圖
            "is_card_comparison_recommendation": False,
            "card_comparison_type": None,
            "user_card_name": None,
            "comparison_category": None,
            "comparison_bank": None
        }

    @staticmethod
    def analyze_user_intent(user_message, conversation_history=None):
        """分析使用者意圖，回傳結構化意圖物件"""
        # 建立基礎意圖結構
        intent = ChatbotResponseBuilder._create_base_intent(user_message)
        
        # 分析上下文和卡片優惠問題
        ChatbotResponseBuilder._analyze_context_and_benefit_intent(intent, user_message, conversation_history)

        # 分析銀行資訊
        ChatbotResponseBuilder._analyze_bank_intent(intent, user_message) 
        
        # 分析消費類別
        ChatbotResponseBuilder._analyze_category_intent(intent, user_message)
        
        # 分析導航意圖
        ChatbotResponseBuilder._analyze_navigation_intent(intent, user_message)
        
        # 分析比較意圖
        ChatbotResponseBuilder._analyze_comparison_intent(intent, user_message)
        
        # 分析個人化推薦意圖
        ChatbotResponseBuilder._analyze_personal_recommendation_intent(intent, user_message)
        
        # 分析卡片比較推薦意圖
        ChatbotResponseBuilder._analyze_card_comparison_recommendation_intent(intent, user_message)
            
        return intent

    @staticmethod
    def _analyze_context_and_benefit_intent(intent, user_message, conversation_history=None):
        """分析上下文相關問題和卡片優惠問題"""
        context_indicators = INTENT_KEYWORDS['context_indicators']
        card_benefit_indicators = INTENT_KEYWORDS['card_benefit_indicators']
        
        if any(indicator in user_message for indicator in context_indicators):
            intent["is_context_question"] = True
        elif any(indicator in user_message for indicator in card_benefit_indicators):
            intent["is_card_benefit_question"] = True
            
            # 從對話歷史中提取銀行資訊
            if conversation_history:
                for msg in conversation_history[-DATABASE_CONFIG['conversation_history_limit']:]:  # 檢查最近對話
                    if msg.get('type') == 'ai':
                        ai_content = msg.get('content', '')
                        # 檢查AI回應中是否提到銀行
                        for standard_name, config in BANK_MAPPING.items():
                            for keyword in config['keywords']:
                                if keyword in ai_content:
                                    if standard_name not in intent["context_banks"]:
                                        intent["context_banks"].append(standard_name)
                                    break

    @staticmethod
    def _analyze_bank_intent(intent, user_message):
        """分析銀行資訊"""
        for standard_name, config in BANK_MAPPING.items():
            for keyword in config['keywords']:
                if keyword in user_message:
                    if standard_name not in intent["banks"]:
                        intent["banks"].append(standard_name)
                    break 
        
    @staticmethod
    def _analyze_category_intent(intent, user_message):
        """分析消費類別資訊"""
        # 找出訊息中提及的消費類別
        # 注意：這裡會執行一次DB查詢，若有效能考量可考慮快取
        for category in ChatbotDataService.get_reward_categories():
            if category in user_message:
                if category not in intent["categories"]:
                    intent["categories"].append(category)
        
        # 如果沒有找到完全匹配的類別，嘗試部分匹配
        if not intent["categories"]:
            for category in ChatbotDataService.get_reward_categories():
                # 將組合字串分割成單詞進行匹配
                category_words = category.split()
                for word in category_words:
                    # 檢查完整詞彙匹配
                    if word in user_message and len(word) > FORMAT_CONFIG['min_word_length']:  # 避免單字符匹配
                        if word not in intent["categories"]:
                            intent["categories"].append(word)
                        break
                    # 檢查部分詞彙匹配（如「美食」匹配「美食饗宴」）
                    elif len(word) > FORMAT_CONFIG['min_partial_word_length'] and any(part in user_message for part in [word[:2], word[:3], word[:4]] if len(part) > FORMAT_CONFIG['min_word_length']):
                        if word not in intent["categories"]:
                            intent["categories"].append(word)
                        break
        
        # 額外檢查：如果用戶訊息包含常見關鍵字，嘗試匹配資料庫中的相關類別
        # 基於資料庫實際類別和用戶常用詞彙擴展關鍵字列表（適用於所有查詢）
        for keyword in COMMON_KEYWORDS:
            if keyword in user_message:
                for category in ChatbotDataService.get_reward_categories():
                    if keyword in category and keyword not in intent["categories"]:
                        intent["categories"].append(keyword)
                        break
            
    @staticmethod
    def _analyze_navigation_intent(intent, user_message):
        """分析導航意圖"""
        for nav_type, keywords in NAVIGATION_KEYWORDS.items():
            if nav_type == 'general_pages':
                # 處理一般頁面導航
                for page_type, page_keywords in keywords.items():
                    if any(keyword in user_message for keyword in page_keywords):
                        intent["is_navigation"] = True
                        intent["navigation_type"] = "general_page"
                        intent["navigation_target"] = page_type
                        break
                if intent["is_navigation"]:
                    break
            elif nav_type == 'auth_pages':
                # 處理登入註冊頁面導航
                for page_type, page_keywords in keywords.items():
                    if any(keyword in user_message for keyword in page_keywords):
                        intent["is_navigation"] = True
                        intent["navigation_type"] = "auth_page"
                        intent["navigation_target"] = page_type
                        break
                if intent["is_navigation"]:
                    break
            else:
                # 處理其他導航類型（會員專區、新增卡片、登出）
                if any(keyword in user_message for keyword in keywords):
                    intent["is_navigation"] = True
                    intent["navigation_type"] = nav_type
                    intent["navigation_target"] = nav_type
                    break

    @staticmethod
    def _handle_navigation_intent(intent, user_id=None, current_page=''):
        """處理導航意圖"""
        nav_type = intent.get("navigation_type")
        nav_target = intent.get("navigation_target")
        
        # 會員專區相關導航
        if nav_type == "member_area":
            if user_id:
                # 已登入：檢查是否已在會員專區
                # 這裡需要檢查當前頁面，暫時假設不在會員專區
                return f"NAVIGATE:member_area:{RESPONSE_MESSAGES['navigation']['member_area']}"
            else:
                # 未登入
                return RESPONSE_MESSAGES['navigation']['login_required']
        
        # 一般頁面導航
        elif nav_type == "general_page":
            # 檢查是否已在目標頁面（暫時假設不在）
            page_name = PAGE_MAPPING['general_pages'].get(nav_target, nav_target)
            message = RESPONSE_MESSAGES['navigation']['general_pages'].get(nav_target, f"好的，我帶你去{page_name}")
            return f"NAVIGATE:{nav_target}:{message}"
        
        # 新增卡片導航
        elif nav_type == "add_card":
            if user_id:
                # 已登入：檢查是否在新增卡片頁面
                if current_page and ('cards/new' in current_page or 'add_card' in current_page):
                    return RESPONSE_MESSAGES['navigation']['already_here']
                else:
                    return f"NAVIGATE:add_card:{RESPONSE_MESSAGES['navigation']['add_card']}"
            else:
                # 未登入
                return RESPONSE_MESSAGES['navigation']['login_required']
        
        # 登入註冊頁面導航
        elif nav_type == "auth_page":
            page_name = PAGE_MAPPING['auth_pages'].get(nav_target, nav_target)
            message = RESPONSE_MESSAGES['navigation']['auth_pages'].get(nav_target, f"好的，我帶你去{page_name}")
            return f"NAVIGATE:{nav_target}:{message}"
        
        # 登出
        elif nav_type == "logout":
            if user_id:
                return f"NAVIGATE:logout:{RESPONSE_MESSAGES['navigation']['logout']}"
            else:
                return RESPONSE_MESSAGES['navigation']['not_logged_in']
        
        return RESPONSE_MESSAGES['navigation']['default']

    @staticmethod
    def _analyze_comparison_intent(intent, user_message):
        """分析比較意圖的詳細信息"""
        # 檢查是否為比較查詢
        comparison_indicators = COMPARISON_KEYWORDS['comparison_indicators']
        highest_indicators = COMPARISON_KEYWORDS['highest_indicators']
        bank_limited_indicators = COMPARISON_KEYWORDS['bank_limited_indicators']
        
        # 檢查是否包含比較指示詞
        has_comparison = any(indicator in user_message for indicator in comparison_indicators)
        has_highest = any(indicator in user_message for indicator in highest_indicators)
        has_bank_limited = any(indicator in user_message for indicator in bank_limited_indicators)
        
        if has_comparison or has_highest:
            intent["is_comparison"] = True
            intent["is_highest_query"] = has_highest
            intent["is_bank_limited"] = has_bank_limited
            
            # 分析比較類型
            if any(sep in user_message for sep in INTENT_KEYWORDS['comparison_separators']):
                # 特定卡片比較：A卡與B卡
                intent["comparison_type"] = "specific_cards"
                # 提取卡片名稱
                import re
                
                # 簡化版本：直接分割並清理
                # 先移除比較前綴
                prefixes_pattern = '|'.join(INTENT_KEYWORDS['comparison_prefixes'])
                clean_message = re.sub(f'^({prefixes_pattern})', '', user_message)
                
                # 使用分隔符分割
                separators = INTENT_KEYWORDS['comparison_separators']
                cards = []
                
                for sep in separators:
                    if sep in clean_message:
                        parts = clean_message.split(sep)
                        if len(parts) >= 2:
                            for part in parts[:2]:  # 只取前兩個部分
                                # 清理卡片名稱
                                card_name = part.strip()
                                # 移除"關於"、"在回饋"後的內容
                                card_name = re.sub(r'[關於在回饋].*$', '', card_name)
                                # 移除銀行名稱前綴（如"玉山的"）
                                card_name = re.sub(r'^[^卡]*的', '', card_name)
                                # 確保以卡結尾
                                if not any(card_name.endswith(suffix) for suffix in INTENT_KEYWORDS['card_suffixes']):
                                    if '信用卡' in card_name:
                                        card_name = card_name.replace('信用卡', '信用卡')
                                    else:
                                        card_name += INTENT_KEYWORDS['card_suffixes'][0]  # 使用 "卡"
                                
                                if card_name and len(card_name) > 1:
                                    cards.append(card_name)
                            
                            if len(cards) >= 2:
                                intent["comparison_cards"] = cards
                                break
                        break
            elif has_highest:
                # 最高回饋查詢
                intent["comparison_type"] = "highest_reward"
            else:
                # 一般比較查詢
                intent["comparison_type"] = "general_comparison"

    @staticmethod
    def _handle_comparison_intent(intent, user_id=None):
        """處理比較意圖"""
        comparison_type = intent.get("comparison_type")
        categories = intent.get("categories", [])
        banks = intent.get("banks", [])
        is_highest = intent.get("is_highest_query", False)
        is_bank_limited = intent.get("is_bank_limited", False)
        
        if not categories:
            return RESPONSE_MESSAGES['comparison']['no_category_specified']
        
        # 優先選擇更相關的類別
        category = None
        
        for priority in INTENT_KEYWORDS['priority_categories']:
            if priority in categories:
                category = priority
                break
        
        # 如果沒有找到優先類別，使用第一個
        if not category:
            category = categories[0]
        
        if comparison_type == "specific_cards":
            # 特定卡片比較
            comparison_cards = intent.get("comparison_cards", [])
            if len(comparison_cards) < 2:
                return RESPONSE_MESSAGES['comparison']['no_cards_specified']
            
            return ChatbotResponseBuilder._compare_specific_cards(comparison_cards, category)
            
        elif comparison_type == "highest_reward":
            # 最高回饋查詢
            if is_bank_limited and banks:
                # 限定銀行
                return ChatbotResponseBuilder._get_highest_reward_in_bank(banks[0], category)
            else:
                # 不限銀行
                return ChatbotResponseBuilder._get_highest_reward_unlimited(category)
                
        else:
            # 一般比較查詢
            if is_bank_limited and banks:
                # 限定銀行
                return ChatbotResponseBuilder._compare_cards_in_bank(banks[0], category, is_highest)
            else:
                # 不限銀行
                return ChatbotResponseBuilder._compare_cards_unlimited(category, is_highest)

    @staticmethod
    def _compare_specific_cards(card_names, category):
        """比較特定卡片"""
        # 查詢兩張卡片的回饋資料
        all_cards = ChatbotDataService.get_all_active_cards()
        card_data = []
        
        for card_name in card_names:
            # 尋找匹配的卡片
            matched_card = None
            for card in all_cards:
                if card_name in card['name'] or card['name'] in card_name:
                    matched_card = card
                    break
            
            if matched_card:
                # 查詢該卡片的回饋資料
                rewards = ChatbotDataService.get_card_all_rewards(matched_card['name'])
                category_rewards = [r for r in rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
                card_data.append({
                    'name': matched_card['name'],
                    'bank': matched_card['bank'],
                    'rewards': category_rewards
                })
        
        if len(card_data) < 2:
            return RESPONSE_MESSAGES['comparison']['no_cards_found']
        
        # 比較回饋率
        response = RESPONSE_MESSAGES['comparison']['comparison_title'].format(category=category)
        for card in card_data:
            if card['rewards']:
                best_reward = max(card['rewards'], key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
                rate_display = ChatbotDataService._format_reward_rate_from_dict(best_reward)
                response += f"- {card['bank']} {card['name']}: {rate_display} {best_reward['reward_type']}\n"
            else:
                response += RESPONSE_MESSAGES['comparison']['no_reward'].format(
                    bank=card['bank'], name=card['name'], category=category
                )
        
        return response

    @staticmethod
    def _get_highest_reward_in_bank(bank, category):
        """取得特定銀行在指定類別的最高回饋"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(card__bank__icontains=bank) &
            (Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category))
        )
        
        if rewards.exists():
            best_reward = rewards.first()
            rate_display = ChatbotDataService._format_reward_rate(best_reward.min_rate, best_reward.max_rate)
            return RESPONSE_MESSAGES['comparison']['highest_in_bank'].format(
                bank=bank, category=category, name=best_reward.card.name, 
                rate=rate_display, type=best_reward.reward_type
            )
        else:
            return RESPONSE_MESSAGES['comparison']['bank_no_data'].format(bank=bank, category=category)

    @staticmethod
    def _get_highest_reward_unlimited(category):
        """取得不限銀行的最高回饋"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category)
        )
        
        if rewards.exists():
            best_reward = rewards.first()
            rate_display = ChatbotDataService._format_reward_rate(best_reward.min_rate, best_reward.max_rate)
            return RESPONSE_MESSAGES['comparison']['highest_unlimited'].format(
                category=category, bank=best_reward.card.bank, name=best_reward.card.name, 
                rate=rate_display, type=best_reward.reward_type
            )
        else:
            return RESPONSE_MESSAGES['comparison']['no_data_found'].format(category=category)

    @staticmethod
    def _compare_cards_in_bank(bank, category, is_highest_only=False):
        """比較特定銀行內的卡片"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(card__bank__icontains=bank) &
            (Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category))
        )
        
        if rewards.exists():
            if is_highest_only:
                # 只返回最高回饋的卡片，如果有相同數值則並列
                best_reward = rewards.first()
                best_rate = float(best_reward.max_rate or best_reward.min_rate or 0)
                
                # 找出所有相同最高回饋率的卡片
                same_rate_rewards = rewards.filter(
                    Q(max_rate=best_reward.max_rate, min_rate=best_reward.min_rate) |
                    Q(max_rate=best_reward.max_rate) |
                    Q(min_rate=best_reward.min_rate)
                )
                
                if same_rate_rewards.count() == 1:
                    rate_display = ChatbotDataService._format_reward_rate(best_reward.min_rate, best_reward.max_rate)
                    return RESPONSE_MESSAGES['comparison']['highest_in_bank'].format(
                        bank=bank, category=category, name=best_reward.card.name, 
                        rate=rate_display, type=best_reward.reward_type
                    )
                else:
                    response = RESPONSE_MESSAGES['comparison']['highest_tied'].format(bank=bank, category=category)
                    for reward in same_rate_rewards:
                        rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                        response += f"- {reward.card.name}: {rate_display} {reward.reward_type}\n"
                    return response
            else:
                # 返回前5名
                response = RESPONSE_MESSAGES['comparison']['cards_in_bank'].format(bank=bank, category=category)
                for reward in rewards[:5]:
                    rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                    response += f"- {reward.card.name}: {rate_display} {reward.reward_type}\n"
                return response
        else:
            return RESPONSE_MESSAGES['comparison']['bank_no_data'].format(bank=bank, category=category)

    @staticmethod
    def _compare_cards_unlimited(category, is_highest_only=False):
        """比較不限銀行的卡片"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category)
        )
        
        if rewards.exists():
            if is_highest_only:
                # 只返回最高回饋的卡片，如果有相同數值則並列
                best_reward = rewards.first()
                best_rate = float(best_reward.max_rate or best_reward.min_rate or 0)
                
                # 找出所有相同最高回饋率的卡片
                same_rate_rewards = rewards.filter(
                    Q(max_rate=best_reward.max_rate, min_rate=best_reward.min_rate) |
                    Q(max_rate=best_reward.max_rate) |
                    Q(min_rate=best_reward.min_rate)
                )
                
                if same_rate_rewards.count() == 1:
                    rate_display = ChatbotDataService._format_reward_rate(best_reward.min_rate, best_reward.max_rate)
                    return RESPONSE_MESSAGES['comparison']['highest_unlimited'].format(
                        category=category, bank=best_reward.card.bank, name=best_reward.card.name, 
                        rate=rate_display, type=best_reward.reward_type
                    )
                else:
                    response = RESPONSE_MESSAGES['comparison']['highest_tied_unlimited'].format(category=category)
                    for reward in same_rate_rewards:
                        rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                        response += f"- {reward.card.bank} {reward.card.name}: {rate_display} {reward.reward_type}\n"
                    return response
            else:
                # 返回前5名
                response = RESPONSE_MESSAGES['comparison']['cards_unlimited'].format(category=category)
                for reward in rewards[:5]:
                    rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                    response += f"- {reward.card.bank} {reward.card.name}: {rate_display} {reward.reward_type}\n"
                return response
        else:
            return RESPONSE_MESSAGES['comparison']['no_data_found'].format(category=category)

    @staticmethod
    def _analyze_personal_recommendation_intent(intent, user_message):
        """分析個人化推薦意圖"""
        personal_indicators = PERSONAL_RECOMMENDATION_KEYWORDS['personal_indicators']
        recommendation_indicators = PERSONAL_RECOMMENDATION_KEYWORDS['recommendation_indicators']
        specific_merchants = PERSONAL_RECOMMENDATION_KEYWORDS['specific_merchants']
        
        # 檢查是否包含個人化指示詞和推薦指示詞
        has_personal = any(indicator in user_message for indicator in personal_indicators)
        has_recommendation = any(indicator in user_message for indicator in recommendation_indicators)
        
        if has_personal and has_recommendation:
            intent["is_personal_recommendation"] = True
            
            # 檢查是否限定銀行
            bank_limited = any(keyword in user_message for keyword in INTENT_KEYWORDS['bank_limited_keywords'])
            if bank_limited:
                intent["recommendation_type"] = "bank_limited"
                # 提取銀行名稱
                for bank, config in BANK_MAPPING.items():
                    for keyword in config['keywords']:
                        if keyword in user_message:
                            intent["recommendation_bank"] = bank
                            break
                    if intent["recommendation_bank"]:
                        break
            else:
                intent["recommendation_type"] = "unlimited"
            
            # 提取推薦類別
            # 先檢查特定商家
            for merchant in specific_merchants:
                if merchant in user_message:
                    intent["recommendation_category"] = merchant
                    break
            
            # 如果沒有特定商家，檢查一般類別
            if not intent["recommendation_category"]:
                for category in ChatbotDataService.get_reward_categories():
                    if category in user_message:
                        intent["recommendation_category"] = category
                        break
                
                # 如果還是沒有找到，檢查常見關鍵字
                if not intent["recommendation_category"]:
                    for keyword in COMMON_KEYWORDS:
                        if keyword in user_message:
                            intent["recommendation_category"] = keyword
                            break

    @staticmethod
    def _handle_personal_recommendation_intent(intent, user_id=None):
        """處理個人化推薦意圖"""
        recommendation_type = intent.get("recommendation_type")
        category = intent.get("recommendation_category")
        bank = intent.get("recommendation_bank")
        
        if not category:
            return RESPONSE_MESSAGES['personal']['no_category_specified']
        
        if recommendation_type == "bank_limited" and bank:
            # 限定銀行推薦
            return ChatbotResponseBuilder._get_personal_recommendation_in_bank(bank, category)
        else:
            # 不限銀行推薦
            return ChatbotResponseBuilder._get_personal_recommendation_unlimited(category)

    @staticmethod
    def _get_personal_recommendation_in_bank(bank, category):
        """取得特定銀行的個人化推薦"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(card__bank__icontains=bank) &
            (Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category))
        )
        
        if rewards.exists():
            best_reward = rewards.first()
            rate_display = ChatbotDataService._format_reward_rate(best_reward.min_rate, best_reward.max_rate)
            return RESPONSE_MESSAGES['recommendation']['personal_recommendation_bank'].format(
                category=category, bank=bank, name=best_reward.card.name, 
                rate=rate_display, type=best_reward.reward_type
            )
        else:
            return RESPONSE_MESSAGES['recommendation']['bank_no_recommendation'].format(bank=bank, category=category)

    @staticmethod
    def _get_personal_recommendation_unlimited(category):
        """取得不限銀行的個人化推薦"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category)
        )
        
        if rewards.exists():
            best_reward = rewards.first()
            rate_display = ChatbotDataService._format_reward_rate(best_reward.min_rate, best_reward.max_rate)
            return RESPONSE_MESSAGES['recommendation']['personal_recommendation_unlimited'].format(
                category=category, bank=best_reward.card.bank, name=best_reward.card.name, 
                rate=rate_display, type=best_reward.reward_type
            )
        else:
            return RESPONSE_MESSAGES['recommendation']['no_recommendation'].format(category=category)

    @staticmethod
    def _analyze_card_comparison_recommendation_intent(intent, user_message):
        """分析卡片比較推薦意圖"""
        comparison_indicators = CARD_COMPARISON_RECOMMENDATION_KEYWORDS['comparison_indicators']
        reward_indicators = CARD_COMPARISON_RECOMMENDATION_KEYWORDS['reward_indicators']
        other_card_indicators = CARD_COMPARISON_RECOMMENDATION_KEYWORDS['other_card_indicators']
        bank_limited_indicators = CARD_COMPARISON_RECOMMENDATION_KEYWORDS['bank_limited_indicators']
        
        # 檢查是否包含比較指示詞、優惠指示詞和其他卡片指示詞
        has_comparison = any(indicator in user_message for indicator in comparison_indicators)
        has_reward = any(indicator in user_message for indicator in reward_indicators)
        has_other_card = any(indicator in user_message for indicator in other_card_indicators)
        
        if has_comparison and has_reward and has_other_card:
            intent["is_card_comparison_recommendation"] = True
            
            # 檢查是否限定銀行
            bank_limited = any(keyword in user_message for keyword in bank_limited_indicators)
            if bank_limited:
                intent["card_comparison_type"] = "bank_limited"
                # 提取銀行名稱
                for bank, config in BANK_MAPPING.items():
                    for keyword in config['keywords']:
                        if keyword in user_message:
                            intent["comparison_bank"] = bank
                            break
                    if intent["comparison_bank"]:
                        break
            else:
                intent["card_comparison_type"] = "unlimited"
            
            # 提取用戶卡片名稱
            all_cards = ChatbotDataService.get_all_active_cards()
            for card in all_cards:
                card_name = card['name']
                if card_name in user_message:
                    intent["user_card_name"] = card_name
                    break
                # 檢查卡片名稱的關鍵部分
                card_key_part = card_name.replace(card['bank'], '').strip()
                if card_key_part and card_key_part in user_message:
                    intent["user_card_name"] = card_name
                    break
            
            # 提取比較類別
            for category in ChatbotDataService.get_reward_categories():
                if category in user_message:
                    intent["comparison_category"] = category
                    break
            
            # 如果沒有找到，檢查常見關鍵字
            if not intent["comparison_category"]:
                for keyword in COMMON_KEYWORDS:
                    if keyword in user_message:
                        intent["comparison_category"] = keyword
                        break

    @staticmethod
    def _handle_card_comparison_recommendation_intent(intent, user_id=None):
        """處理卡片比較推薦意圖"""
        comparison_type = intent.get("card_comparison_type")
        user_card_name = intent.get("user_card_name")
        category = intent.get("comparison_category")
        bank = intent.get("comparison_bank")
        
        if not user_card_name:
            return RESPONSE_MESSAGES['personal']['no_card_specified']
        
        if not category:
            return RESPONSE_MESSAGES['personal']['no_category_specified']
        
        if comparison_type == "bank_limited" and bank:
            # 限定銀行推薦
            return ChatbotResponseBuilder._get_better_cards_in_bank(user_card_name, category, bank)
        else:
            # 不限銀行推薦
            return ChatbotResponseBuilder._get_better_cards_unlimited(user_card_name, category)

    @staticmethod
    def _get_better_cards_in_bank(user_card_name, category, bank):
        """取得特定銀行中比用戶卡片更好的卡片"""
        # 先查詢用戶卡片的回饋率
        user_card_rewards = ChatbotDataService.get_card_all_rewards(user_card_name)
        user_category_rewards = [r for r in user_card_rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
        
        if not user_category_rewards:
            return RESPONSE_MESSAGES['recommendation']['no_comparison_data'].format(card_name=user_card_name, category=category)
        
        # 取得用戶卡片在該類別的最高回饋率
        user_best_reward = max(user_category_rewards, key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
        user_rate = float(user_best_reward.get('max_rate', 0) or user_best_reward.get('min_rate', 0) or 0)
        
        # 查詢該銀行其他卡片的回饋
        all_cards = ChatbotDataService.get_all_active_cards()
        bank_cards = [card for card in all_cards if bank in card['bank'] and card['name'] != user_card_name]
        
        better_cards = []
        for card in bank_cards:
            card_rewards = ChatbotDataService.get_card_all_rewards(card['name'])
            category_rewards = [r for r in card_rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
            
            if category_rewards:
                best_reward = max(category_rewards, key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
                card_rate = float(best_reward.get('max_rate', 0) or best_reward.get('min_rate', 0) or 0)
                
                if card_rate > user_rate:
                    better_cards.append({
                        'name': card['name'],
                        'rate': card_rate,
                        'reward': best_reward
                    })
        
        if better_cards:
            # 按回饋率排序
            better_cards.sort(key=lambda x: x['rate'], reverse=True)
            best_card = better_cards[0]
            rate_display = ChatbotDataService._format_reward_rate_from_dict(best_card['reward'])
            
            return RESPONSE_MESSAGES['recommendation']['better_card_in_bank'].format(
                bank=bank, card_name=user_card_name, category=category, 
                name=best_card['name'], rate=rate_display, type=best_card['reward']['reward_type']
            )
        else:
            return RESPONSE_MESSAGES['recommendation']['no_better_card_in_bank'].format(
                bank=bank, card_name=user_card_name, category=category
            )

    @staticmethod
    def _get_better_cards_unlimited(user_card_name, category):
        """取得不限銀行中比用戶卡片更好的卡片"""
        # 先查詢用戶卡片的回饋率
        user_card_rewards = ChatbotDataService.get_card_all_rewards(user_card_name)
        user_category_rewards = [r for r in user_card_rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
        
        if not user_category_rewards:
            return RESPONSE_MESSAGES['recommendation']['no_comparison_data'].format(card_name=user_card_name, category=category)
        
        # 取得用戶卡片在該類別的最高回饋率
        user_best_reward = max(user_category_rewards, key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
        user_rate = float(user_best_reward.get('max_rate', 0) or user_best_reward.get('min_rate', 0) or 0)
        
        # 查詢所有其他卡片的回饋
        all_cards = ChatbotDataService.get_all_active_cards()
        other_cards = [card for card in all_cards if card['name'] != user_card_name]
        
        better_cards = []
        for card in other_cards:
            card_rewards = ChatbotDataService.get_card_all_rewards(card['name'])
            category_rewards = [r for r in card_rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
            
            if category_rewards:
                best_reward = max(category_rewards, key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
                card_rate = float(best_reward.get('max_rate', 0) or best_reward.get('min_rate', 0) or 0)
                
                if card_rate > user_rate:
                    better_cards.append({
                        'name': card['name'],
                        'bank': card['bank'],
                        'rate': card_rate,
                        'reward': best_reward
                    })
        
        if better_cards:
            # 按回饋率排序
            better_cards.sort(key=lambda x: x['rate'], reverse=True)
            best_card = better_cards[0]
            rate_display = ChatbotDataService._format_reward_rate_from_dict(best_card['reward'])
            
            return RESPONSE_MESSAGES['recommendation']['found_better_cards'].format(
                card_name=user_card_name, category=category, bank=best_card['bank'], 
                better_card_name=best_card['name'], rate=rate_display, reward_type=best_card['reward']['reward_type']
            )
        else:
            return RESPONSE_MESSAGES['recommendation']['no_better_cards'].format(
                card_name=user_card_name, category=category
            )

    @staticmethod
    def validate_response(response, user_message, user_id=None):
        """驗證 AI 回應是否包含虛假的卡片名稱"""
        try:
            # 改為使用動態產生的列表
            if any(keyword in user_message for keyword in ChatbotResponseBuilder._bank_related_keywords):
                # 獲取所有真實的卡片名稱
                all_cards = ChatbotDataService.get_all_active_cards()
                real_card_names = {card['name'] for card in all_cards}
                
                # 檢查回應中是否包含虛假的卡片名稱
                lines = response.split('\n')
                validated_lines = []
                
                for line in lines:
                    # 如果是條列式項目（以 - 開頭）
                    if line.strip().startswith('-'):
                        card_name = line.strip()[1:].strip()
                        # 檢查是否是真實的卡片名稱（支援部分匹配）
                        is_real_card = any(
                            real_name in card_name or card_name in real_name
                            for real_name in real_card_names
                        )
                        if is_real_card:
                            validated_lines.append(line)
                        else:
                            # 如果是虛假的卡片名稱，跳過這一行
                            continue
                    else:
                        validated_lines.append(line)
                
                return '\n'.join(validated_lines)
            
            return response
        except Exception as e:
            return response

    
    @staticmethod
    def build_context_prompt_with_history(intent, user_id=None, conversation_history=None):
        """根據意圖和對話歷史建立上下文提示詞"""
        # 建立基本上下文
        context = ChatbotResponseBuilder.build_context_prompt(intent, user_id)
        
        # 添加對話歷史和上下文分析
        if conversation_history and len(conversation_history) > 0:
            context += RESPONSE_MESSAGES['context']['conversation_history']
            context += RESPONSE_MESSAGES['context']['history_description']
            
            for msg in conversation_history[-6:]:  # 只取最近6條
                if msg.get('type') == 'user':
                    context += f"{RESPONSE_MESSAGES['context']['user_prefix']}{msg.get('content', '')}\n"
                elif msg.get('type') == 'ai':
                    context += f"{RESPONSE_MESSAGES['context']['ai_prefix']}{msg.get('content', '')}\n"
            
            # 分析對話上下文
            context += RESPONSE_MESSAGES['context']['context_analysis']
            context += RESPONSE_MESSAGES['context']['analysis_points']
            context += RESPONSE_MESSAGES['context']['analysis_1']
            context += RESPONSE_MESSAGES['context']['analysis_2']
            context += RESPONSE_MESSAGES['context']['analysis_3']
            context += RESPONSE_MESSAGES['context']['analysis_4']
            context += RESPONSE_MESSAGES['context']['analysis_5']
            context += RESPONSE_MESSAGES['context']['analysis_conclusion']
        
        return context

    @staticmethod
    def build_context_prompt(intent, user_id=None):
        """根據分析後的意圖建構上下文提示詞"""
        
        context = SYSTEM_PROMPT
        
        # 添加用戶資訊
        if user_id:
            user_cards = ChatbotDataService.get_user_cards(user_id)
            if user_cards:
                context += RESPONSE_MESSAGES['user_info']['header']
                for card in user_cards:
                    context += f"- {card['card__bank']} {card['card__name']}"
                    if card['nickname']:
                        context += f"{RESPONSE_MESSAGES['user_info']['nickname_prefix']}{card['nickname']}{RESPONSE_MESSAGES['user_info']['nickname_suffix']}"
                    if card['is_primary']:
                        context += RESPONSE_MESSAGES['user_info']['primary_marker']
                    context += "\n"
        
        # 添加通用資料庫資訊 (可考慮快取)
        context += RESPONSE_MESSAGES['database_info']['header']
        context += RESPONSE_MESSAGES['database_info']['description']
        
        banks = ChatbotDataService.get_supported_banks()
        context += RESPONSE_MESSAGES['database_info']['supported_banks']
        for bank in banks[:DATABASE_CONFIG['max_banks_display']]: context += f"- {bank}\n"
        if len(banks) > DATABASE_CONFIG['max_banks_display']: 
            context += RESPONSE_MESSAGES['database_info']['more_banks'].format(count=len(banks))
        
        categories = ChatbotDataService.get_reward_categories()
        context += RESPONSE_MESSAGES['database_info']['categories']
        for category in categories[:DATABASE_CONFIG['max_categories_display']]: context += f"- {category}\n"
        if len(categories) > DATABASE_CONFIG['max_categories_display']: 
            context += RESPONSE_MESSAGES['database_info']['more_categories'].format(count=len(categories))
        
        total_cards = len(ChatbotDataService.get_all_active_cards())
        context += RESPONSE_MESSAGES['database_info']['total_cards'].format(count=total_cards)
        
        # 處理特定卡片優惠問題
        if intent.get("is_card_benefit_question", False):
            context += RESPONSE_MESSAGES['card_benefit']['header']
            context += RESPONSE_MESSAGES['card_benefit']['description']
            
            # 提取卡片名稱
            user_message = intent.get("raw_message", "")
            card_name = None
            bank_name = None
            
            # 從用戶訊息中提取銀行名稱
            for bank, config in BANK_MAPPING.items():
                for keyword in config['keywords']:
                    if keyword in user_message:
                        bank_name = bank
                        break
                if bank_name:
                    break
            
            # 動態提取卡片名稱：從資料庫中所有卡片名稱進行匹配
            all_cards = ChatbotDataService.get_all_active_cards()
            for card in all_cards:
                card_full_name = card['name']
                # 檢查完整卡片名稱是否在用戶訊息中
                if card_full_name in user_message:
                    card_name = card_full_name
                    break
                # 檢查卡片名稱的關鍵部分（去除銀行名稱前綴）
                card_key_part = card_full_name.replace(card['bank'], '').strip()
                if card_key_part and card_key_part in user_message:
                    card_name = card_full_name
                    break
            
            # 如果沒有找到完整匹配，嘗試部分匹配
            if not card_name and bank_name:
                for card in all_cards:
                    if bank_name in card['bank']:
                        # 檢查卡片名稱是否包含用戶訊息中的關鍵字
                        card_words = card['name'].split()
                        for word in card_words:
                            if len(word) > 2 and word in user_message:
                                card_name = card['name']
                                break
                        if card_name:
                            break
            
            if card_name:
                context += f"{RESPONSE_MESSAGES['card_benefit']['query_prefix']}{card_name}{RESPONSE_MESSAGES['card_benefit']['query_suffix']}"
                # 查詢該卡片的回饋資料
                rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                    card__name=card_name
                )
                if rewards.exists():
                    for reward in rewards:
                        rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                        context += f"- {reward.category}/{reward.scope}: {rate_display} {reward.reward_type}\n"
                else:
                    context += RESPONSE_MESSAGES['card_benefit']['no_data'].format(name=card_name)
            else:
                context += RESPONSE_MESSAGES['card_benefit']['unrecognized']

        # 處理上下文相關問題
        if intent.get("is_context_question", False) and intent.get("context_banks"):
            context += RESPONSE_MESSAGES['context_question']['header']
            context += RESPONSE_MESSAGES['context_question']['description'].format(banks=', '.join(intent['context_banks']))
            
            # 如果問的是特定類別的回饋
            if intent["categories"]:
                for bank in intent["context_banks"]:
                    for category in intent["categories"]:
                        context += f"{RESPONSE_MESSAGES['context_question']['bank_category_prefix']}{bank} 在 {category}{RESPONSE_MESSAGES['context_question']['bank_category_suffix']}"
                        # 查詢該銀行在該類別的回饋
                        rewards = ChatbotDataService.get_cards_by_category(category)
                        bank_rewards = [r for r in rewards if bank in r.get('bank', '')]
                        if bank_rewards:
                            for reward in bank_rewards:
                                rate = f"{reward.get('min_rate', '') or ''}-{reward.get('max_rate', '') or ''}".strip('-')
                                rate_display = f"{rate}{FORMAT_CONFIG['rate_suffix']}" if rate else FORMAT_CONFIG['unknown_rate']
                                context += f"- {reward['card_name']}: {rate_display} {reward['reward_type']}\n"
                        else:
                            context += RESPONSE_MESSAGES['context_question']['no_bank_data'].format(bank=bank, category=category)
            else:
                # 如果沒有指定類別，提供該銀行的所有回饋資料
                for bank in intent["context_banks"]:
                    context += f"\n### {bank} 的回饋資料：\n"  # 這個可以保持原樣，因為是動態的銀行名稱
                    rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                        card__bank__icontains=bank
                    )
                    if rewards.exists():
                        for reward in rewards[:10]:
                            rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                            context += f"- {reward.card.name}: {reward.category} {rate_display} {reward.reward_type}\n"
                    else:
                        context += f"- 資料庫中沒有 {bank} 的回饋資料\n"  # 這個可以保持原樣，因為是動態的銀行名稱

        # 根據意圖添加特定上下文
        if intent["banks"] and intent["has_card_keyword"]:
            for bank in intent["banks"]:
                # 如果同時問了類別，提供該銀行在該類別的回饋
                if intent["categories"]:
                    context += RESPONSE_MESSAGES['bank_cards']['header'].format(bank=bank)
                    for category in intent["categories"]:
                        rewards = ChatbotDataService.get_cards_by_category(category)
                        bank_rewards = [r for r in rewards if bank in r['bank']]
                        if bank_rewards:
                            context += RESPONSE_MESSAGES['bank_cards']['category_rewards'].format(category=category)
                            for reward in bank_rewards:
                                rate = f"{reward.get('min_rate', '') or ''}-{reward.get('max_rate', '') or ''}".strip('-')
                                rate_display = f"{rate}{FORMAT_CONFIG['rate_suffix']}" if rate else FORMAT_CONFIG['unknown_rate']
                                context += f"- {reward['card_name']}: {rate_display} {reward['reward_type']}\n"
                        else:
                            context += RESPONSE_MESSAGES['bank_cards']['no_category_rewards'].format(category=category)
                else:
                    # 否則，提供該銀行的卡片列表
                    cards = ChatbotDataService.get_cards_by_bank(bank)
                    if cards:
                        context += RESPONSE_MESSAGES['bank_cards']['header'].format(bank=bank)
                        for card in cards[:5]: context += f"- {card['name']}\n"
                
                # 如果意圖包含回饋或比較，也提供回饋資料
                if intent["has_reward_keyword"] or intent["is_comparison"]:
                    rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                        card__bank__icontains=bank
                    )
                    if rewards.exists():
                        context += RESPONSE_MESSAGES['bank_rewards']['header'].format(bank=bank)
                        for reward in rewards[:5]:
                            rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                            context += f"- {reward.card.name}: {reward.category} {rate_display} {reward.reward_type}\n"
        
        # 添加知識庫資訊
        context += RESPONSE_MESSAGES['platform_info']['header']
        context += RESPONSE_MESSAGES['platform_info']['main_features'].format(
            features=', '.join(REWARDIA_KNOWLEDGE_BASE['website_info']['main_features'])
        )
        
        return context

    @staticmethod
    def enhance_response_with_data(response, intent, user_id=None, current_page=''):
        """根據意圖增強 AI 回應"""
        
        user_message = intent.get("raw_message", "")

        # 處理導航意圖（優先處理）
        if intent.get("is_navigation", False):
            return ChatbotResponseBuilder._handle_navigation_intent(intent, user_id, current_page)

        # 處理比較意圖（優先處理）
        if intent.get("is_comparison", False):
            return ChatbotResponseBuilder._handle_comparison_intent(intent, user_id)

        # 處理個人化推薦意圖（優先處理）
        if intent.get("is_personal_recommendation", False):
            return ChatbotResponseBuilder._handle_personal_recommendation_intent(intent, user_id)

        # 處理卡片比較推薦意圖（優先處理）
        if intent.get("is_card_comparison_recommendation", False):
            return ChatbotResponseBuilder._handle_card_comparison_recommendation_intent(intent, user_id)

        # 未登入防護：偵測個人查詢關鍵字但沒有 user_id 時，直接回覆尚未登入
        if (not user_id) and any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS):
            return "你尚未登入"
        
        # 處理特定卡片優惠問題（優先處理）
        if intent.get("is_card_benefit_question", False):
            # 動態提取卡片名稱
            all_cards = ChatbotDataService.get_all_active_cards()
            card_name = None
            
            # 從資料庫中所有卡片名稱進行匹配
            for card in all_cards:
                card_full_name = card['name']
                # 檢查完整卡片名稱是否在用戶訊息中
                if card_full_name in user_message:
                    card_name = card_full_name
                    break
                # 檢查卡片名稱的關鍵部分（去除銀行名稱前綴）
                card_key_part = card_full_name.replace(card['bank'], '').strip()
                if card_key_part and card_key_part in user_message:
                    card_name = card_full_name
                    break
            
            # 如果沒有找到完整匹配，嘗試部分匹配
            if not card_name:
                for bank, config in BANK_MAPPING.items():
                    for keyword in config['keywords']:
                        if keyword in user_message:
                            # 在該銀行的卡片中尋找匹配
                            for card in all_cards:
                                if bank in card['bank']:
                                    card_words = card['name'].split()
                                    for word in card_words:
                                        if len(word) > 2 and word in user_message:
                                            card_name = card['name']
                                            break
                                    if card_name:
                                        break
                            if card_name:
                                break
                    if card_name:
                        break
            
            if card_name:
                # 查詢該卡片的回饋資料
                rewards = ChatbotDataService.get_card_all_rewards(card_name)
                if rewards:
                    response = RESPONSE_MESSAGES['card_rewards']['header'].format(name=card_name)
                    for reward in rewards:
                        rate_display = ChatbotDataService._format_reward_rate_from_dict(reward)
                        response += f"- {reward['category']}/{reward['scope']}: {rate_display} {reward['reward_type']}\n"
                    return response
                else:
                    return RESPONSE_MESSAGES['card_rewards']['no_rewards'].format(name=card_name)
            else:
                return RESPONSE_MESSAGES['card_rewards']['unrecognized_card']
        
        # 已登入使用者的個人化查詢優先處理
        if user_id:
            # 1. 查詢使用者個人卡片的回饋類型
            if any(keyword in user_message for keyword in REWARD_TYPE_KEYWORDS) and any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS):
                user_cards = ChatbotDataService.get_user_cards(user_id)
                if user_cards:
                    # 收集所有使用者卡片的回饋類型
                    all_rewards = []
                    for user_card in user_cards:
                        card_rewards = ChatbotDataService.get_card_all_rewards(user_card['card__name'])
                        if card_rewards:
                            all_rewards.extend(card_rewards)
                    
                    if all_rewards:
                        # 按回饋類型分組
                        reward_types = {}
                        for reward in all_rewards:
                            reward_type = reward['reward_type']
                            if reward_type not in reward_types:
                                reward_types[reward_type] = []
                            reward_types[reward_type].append(reward)
                        
                        response = RESPONSE_MESSAGES['reward_types']['header']
                        for reward_type, rewards in reward_types.items():
                            response += RESPONSE_MESSAGES['reward_types']['type_prefix'].format(type=reward_type)
                            for reward in rewards[:3]:  # 每種類型最多顯示3個
                                rate_display = ChatbotDataService._format_reward_rate_from_dict(reward)
                                response += f"- {reward['bank']} {reward['card_name']}: {rate_display} ({reward['category']})\n"
                            if len(rewards) > 3:
                                response += RESPONSE_MESSAGES['reward_types']['more_rewards'].format(count=len(rewards), type=reward_type)
                        return response
                    else:
                        return RESPONSE_MESSAGES['personal']['no_rewards']
                else:
                    return RESPONSE_MESSAGES['personal']['no_cards_set']
            
            # 2. 查詢使用者個人卡片的特定類別回饋（優先處理）
            if intent["categories"] and any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS + ["哪些有", "哪些是"]):
                user_cards = ChatbotDataService.get_user_cards(user_id)
                if user_cards:
                    # 找出使用者卡片中符合查詢類別的卡片
                    matching_cards = []
                    for category in intent["categories"]:
                        # 查詢使用者卡片在該類別的回饋
                        for user_card in user_cards:
                            card_rewards = ChatbotDataService.get_card_rewards_by_category(
                                user_card['card__name'], category
                            )
                            if card_rewards:
                                matching_cards.extend(card_rewards)
                    
                    if matching_cards:
                        title = RESPONSE_MESSAGES['user_category_rewards']['header'].format(category=intent['categories'][0])
                        response = ChatbotDataService._build_reward_list_response(matching_cards, title)
                        return response
                    else:
                        return RESPONSE_MESSAGES['no_user_category_rewards'].format(category=intent['categories'][0])
            
            # 3. 查詢使用者個人卡片（僅當沒有類別查詢時）
            if any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS) and not intent["categories"]:
                user_cards = ChatbotDataService.get_user_cards(user_id)
                if user_cards:
                    response = RESPONSE_MESSAGES['user_cards']['header']
                    for card in user_cards:
                        response += f"- {card['card__bank']} {card['card__name']}"
                        if card['nickname']:
                            response += f"{RESPONSE_MESSAGES['user_info']['nickname_prefix']}{card['nickname']}{RESPONSE_MESSAGES['user_info']['nickname_suffix']}"
                        if card['is_primary']:
                            response += RESPONSE_MESSAGES['user_info']['primary_marker']
                        response += "\n"
                    return response
                else:
                    return RESPONSE_MESSAGES['personal']['no_cards_set']
        
        # 如果意圖是列出銀行，但回應中沒有，則補充
        if intent["is_listing_banks"] and "銀行" not in response:
            banks = ChatbotDataService.get_supported_banks()
            response = RESPONSE_MESSAGES['supported_banks']['header']
            for bank in banks[:DATABASE_CONFIG['max_banks_display']]: response += f"- {bank}\n"
            if len(banks) > DATABASE_CONFIG['max_banks_display']: 
                response += RESPONSE_MESSAGES['database_info']['more_banks'].format(count=len(banks))
            return response # 直接回傳，因為這是主要意圖

        # 如果意圖是查詢特定銀行的卡片，但回應中沒有條列式內容，則補充
        if intent["banks"] and not intent["has_reward_keyword"] and not intent["is_comparison"]:
            # 檢查回應是否已經包含條列式內容
            if not any(line.strip().startswith('-') for line in response.split('\n')):
                for bank in intent["banks"]:
                    cards = ChatbotDataService.get_cards_by_bank(bank)
                    if cards:
                        response += RESPONSE_MESSAGES['bank_cards']['header'].format(bank=bank)
                        for card in cards[:5]: response += f"- {card['name']}\n"
        
        # 如果意圖是查詢特定類別的回饋，但沒有指定銀行，則補充或修正回應
        if intent["categories"] and not intent["banks"]:
            # 檢查是否有錯誤的「沒有資料」回答
            error_indicators = ["沒有", "找不到", "無相關", "無資料", "資料庫中沒有"]
            has_error_response = any(indicator in response for indicator in error_indicators)
            
            # 計算回應中的卡片數量
            card_lines = [line for line in response.split('\n') if line.strip().startswith('-')]
            card_count = len(card_lines)
            
            # 取得用戶原始訊息
            user_message = intent.get("raw_message", "")
            
            # 如果沒有條列式內容、有錯誤回答、或卡片數量不足，則補充正確資料
            # 對於「所有銀行」問題，期望更多卡片；對於一般問題，至少3張
            expected_min_cards = 8 if any(keyword in user_message for keyword in ["所有", "全部", "全部銀行", "所有銀行"]) else 3
            if not any(line.strip().startswith('-') for line in response.split('\n')) or has_error_response or card_count < expected_min_cards:
                for category in intent["categories"]:
                    # 檢查是否詢問「最高」或「最好」的回饋
                    is_highest_only = any(keyword in user_message for keyword in ["最高", "最好", "最佳", "最優", "最大", "最棒"])
                    
                    # 根據問題類型決定返回的卡片數量
                    limit = 1 if is_highest_only else 5
                    rewards = ChatbotDataService.get_cards_by_category(category, limit)
                    
                    if rewards:
                        # 如果有錯誤回答或卡片數量不足，先清除原始內容
                        if has_error_response or card_count < expected_min_cards:
                            response = ""
                        
                        if is_highest_only:
                            response += f"\n\n{category} 回饋最高的信用卡：\n"  # 保持原樣，因為是動態類別名稱
                        else:
                            # 根據問題類型選擇更合適的標題
                            if any(keyword in user_message for keyword in ["有哪些", "哪些", "什麼", "什麼卡", "所有", "全部", "有", "的卡", "卡片", "信用卡"]):
                                response += f"\n\n{category}的信用卡：\n"  # 保持原樣，因為是動態類別名稱
                            else:
                                response += f"\n\n{category} 消費的最佳回饋卡片：\n"  # 保持原樣，因為是動態類別名稱
                        
                        for reward in rewards:
                            rate_display = ChatbotDataService._format_reward_rate_from_dict(reward)
                            response += f"- {reward['bank']} {reward['card_name']}: {rate_display} {reward['reward_type']}\n"

        return response
