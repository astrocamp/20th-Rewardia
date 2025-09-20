# Chatbot 比較邏輯服務
from django.db.models import Q
from apps.chatbot.config import (
    INTENT_KEYWORDS, RESPONSE_MESSAGES
)
from .data_service import ChatbotDataService


class ComparisonService:
    """比較邏輯服務"""

    @staticmethod
    def handle_comparison_intent(intent, user_id=None):
        """處理比較意圖"""
        comparison_type = intent.get("comparison_type")
        categories = intent.get("categories", [])
        banks = intent.get("banks", [])
        is_highest = intent.get("is_highest_query", False)
        is_bank_limited = intent.get("is_bank_limited", False)
        
        # 如果沒有明確的類別，嘗試從上下文獲取
        if not categories and intent.get("context_categories"):
            categories = intent["context_categories"]
        
        # 如果還是沒有類別，但有用戶卡片，提供用戶卡片的比較
        if not categories and user_id:
            user_cards = ChatbotDataService.get_user_cards(user_id)
            if user_cards:
                # 從用戶卡片中提取可能的類別
                context_categories = intent.get("context_categories", [])
                if context_categories:
                    categories = context_categories
                else:
                    return RESPONSE_MESSAGES['comparison']['no_category_specified']
        
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
            
            return ComparisonService.compare_specific_cards(comparison_cards, category)
            
        elif comparison_type == "highest_reward":
            # 最高回饋查詢
            if is_bank_limited and banks:
                # 限定銀行
                return ComparisonService.get_highest_reward_in_bank(banks[0], category)
            else:
                # 不限銀行
                return ComparisonService.get_highest_reward_unlimited(category)
                
        elif comparison_type == "better_than_card":
            # 比某張卡片更高的查詢
            return ComparisonService.get_better_cards_than_user_card(intent, user_id, category)
                
        else:
            # 一般比較查詢
            if is_bank_limited and banks:
                # 限定銀行
                return ComparisonService.compare_cards_in_bank(banks[0], category, is_highest)
            else:
                # 不限銀行
                return ComparisonService.compare_cards_unlimited(category, is_highest)

    @staticmethod
    def compare_specific_cards(card_names, category):
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
    def get_highest_reward_in_bank(bank, category):
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
    def get_highest_reward_unlimited(category):
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
    def compare_cards_in_bank(bank, category, is_highest_only=False):
        """比較特定銀行內的卡片"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(card__bank__icontains=bank) &
            (Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category))
        )
        
        if rewards.exists():
            if is_highest_only:
                # 只返回最高回饋的卡片，如果有相同數值則並列
                best_reward = rewards.first()
                # 找出所有相同最高回饋率的卡片
                same_rate_rewards = rewards.filter(sort_rate=best_reward.sort_rate)
                
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
    def compare_cards_unlimited(category, is_highest_only=False):
        """比較不限銀行的卡片"""
        rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category)
        )
        
        if rewards.exists():
            if is_highest_only:
                # 只返回最高回饋的卡片，如果有相同數值則並列
                best_reward = rewards.first()
                # 找出所有相同最高回饋率的卡片
                same_rate_rewards = rewards.filter(sort_rate=best_reward.sort_rate)
                
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

    @staticmethod
    def get_better_cards_than_user_card(intent, user_id, category):
        """找出比用戶卡片回饋更高的所有卡片"""
        
        # 從對話歷史中提取用戶的最高回饋卡片
        context_user_cards = intent.get("context_user_cards", [])
        if not context_user_cards:
            return "很抱歉，無法識別您要比較的卡片。"
        
        # 找到用戶卡片中該類別的最高回饋
        user_highest_rate = 0
        user_card_name = ""
        
        for card_info in context_user_cards:
            card_rewards = ChatbotDataService.get_card_all_rewards(card_info)
            category_rewards = [r for r in card_rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
            
            if category_rewards:
                best_reward = max(category_rewards, key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
                rate_value = float(best_reward.get('max_rate', 0) or best_reward.get('min_rate', 0) or 0)
                
                if rate_value > user_highest_rate:
                    user_highest_rate = rate_value
                    user_card_name = card_info
        
        if user_highest_rate == 0:
            return f"很抱歉，您的卡片中沒有 {category} 回饋資料。"
        
        # 查詢所有卡片中比用戶最高回饋更高的卡片
        all_rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
            Q(category__icontains=category) | Q(scope__icontains=category) | Q(reward_type__icontains=category)
        ).select_related('card')
        
        better_cards = []
        for reward in all_rewards:
            # 計算該回饋的數值（使用 max_rate 或 min_rate）
            reward_rate = float(reward.max_rate or reward.min_rate or 0)
            
            # 如果回饋率比用戶的最高回饋更高
            if reward_rate > user_highest_rate:
                # 檢查是否為用戶的卡片（避免重複）
                card_name = f"{reward.card.bank} {reward.card.name}"
                if card_name not in context_user_cards:
                    better_cards.append({
                        'card': reward.card,
                        'reward': reward,
                        'rate': reward_rate
                    })
        
        if better_cards:
            # 按回饋率排序
            better_cards.sort(key=lambda x: x['rate'], reverse=True)
            
            response = f"比您的 {user_card_name} 在 {category} 回饋更高的卡片有：\n\n"
            for card_data in better_cards[:10]:  # 顯示前10張
                rate_display = ChatbotDataService._format_reward_rate(card_data['reward'].min_rate, card_data['reward'].max_rate)
                response += f"- {card_data['card'].bank} {card_data['card'].name}: {rate_display} {card_data['reward'].reward_type}\n"
            
            return response
        else:
            return f"很抱歉，目前沒有比您的 {user_card_name} 在 {category} 回饋更高的卡片。您的卡片已經是該類別回饋最高的選擇之一！"
