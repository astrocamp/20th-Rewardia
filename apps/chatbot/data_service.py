# Chatbot 資料庫查詢服務
import logging
from django.db.models import Q, Value, DecimalField, CharField
from django.db.models.functions import Coalesce, Concat
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory
from apps.users.models import UserCard, User
from apps.chatbot.config import (
    BANK_MAPPING, FORMAT_CONFIG
)
from .utils import handle_database_errors

# 設定日誌記錄器
logger = logging.getLogger(__name__)


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
        # 如果 card_name 包含銀行名稱（格式：銀行名稱 卡片名稱），則提取卡片名稱
        if ' ' in card_name:
            parts = card_name.split(' ', 1)
            if len(parts) == 2:
                bank_name, actual_card_name = parts
                # 先嘗試完整匹配
                rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                    card__name=card_name
                ).select_related('card')
                
                # 如果沒有找到，嘗試只用卡片名稱匹配
                if not rewards.exists():
                    rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                        card__name=actual_card_name,
                        card__bank__icontains=bank_name
                    ).select_related('card')
        else:
            # 如果沒有空格，直接使用原始名稱
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
