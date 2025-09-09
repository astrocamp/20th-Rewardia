# Chatbot 資料庫查詢服務
import logging
from django.db.models import Q, Value, DecimalField
from django.db.models.functions import Coalesce
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory
from apps.users.models import UserCard, User
from apps.chatbot.knowledge_base import REWARDIA_KNOWLEDGE_BASE, SYSTEM_PROMPT
from apps.chatbot.config import BANK_MAPPING, COMMON_KEYWORDS, PERSONAL_QUERY_KEYWORDS, REWARD_TYPE_KEYWORDS

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
    def _format_reward_rate(min_rate, max_rate):
        """格式化回饋率顯示"""
        rate = f"{min_rate or ''}-{max_rate or ''}".strip('-')
        return f"{rate}%" if rate else "未知"
    
    @staticmethod
    def _format_reward_rate_from_dict(reward_dict):
        """從字典格式化回饋率顯示"""
        min_rate = reward_dict.get('min_rate', '') or ''
        max_rate = reward_dict.get('max_rate', '') or ''
        return ChatbotDataService._format_reward_rate(min_rate, max_rate)
    
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
    def get_cards_by_bank(bank_name):
        """根據銀行名稱查詢信用卡"""
        try:
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
        except Exception as e:
            logger.error(f"Error in get_cards_by_bank for bank '{bank_name}': {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def get_cards_by_category(category, limit=5):
        """根據消費類別查詢最佳回饋信用卡（使用 reward_categories 表格）"""
        try:
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
        except Exception as e:
            logger.error(f"Error in get_cards_by_category for category '{category}': {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def get_all_active_cards():
        """取得所有啟用的信用卡"""
        try:
            cards = CreditCard.objects.filter(is_active=True).values('name', 'bank')
            return list(cards)
        except Exception as e:
            logger.error(f"Error in get_all_active_cards: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def get_user_cards(user_id):
        """取得用戶的信用卡（需要登入）"""
        if not user_id:
            return []
        
        try:
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
        except (User.DoesNotExist, Exception) as e:
            logger.error(f"Error in get_user_cards for user_id '{user_id}': {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def get_card_rewards_by_category(card_name, category):
        """取得特定卡片在特定類別的回饋"""
        try:
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
        except Exception as e:
            logger.error(f"Error in get_card_rewards_by_category for card '{card_name}' and category '{category}': {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def get_card_all_rewards(card_name):
        """取得特定卡片的所有回饋"""
        try:
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
        except Exception as e:
            logger.error(f"Error in get_card_all_rewards for card '{card_name}': {str(e)}", exc_info=True)
            return []
    
    
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
    def get_supported_banks():
        """取得支援的銀行列表（從實際資料庫資料去重）"""
        try:
            # 從實際資料庫獲取銀行列表並去重
            banks = CreditCard.objects.filter(is_active=True).values_list('bank', flat=True).distinct()
            # 過濾掉 "無" 和空值
            banks = [bank for bank in banks if bank and bank != "無"]
            
            # 使用統一的銀行映射配置進行標準化
            normalized_banks = []
            for bank in banks:
                # 找到對應的標準銀行名稱
                normalized_bank = bank
                for standard_name, config in BANK_MAPPING.items():
                    if bank in config['keywords']:
                        normalized_bank = standard_name
                        break
                
                if normalized_bank not in normalized_banks:
                    normalized_banks.append(normalized_bank)
            
            return sorted(normalized_banks)
        except Exception as e:
            logger.error(f"Error in get_supported_banks: {str(e)}", exc_info=True)
            return []


class ChatbotResponseBuilder:
    """AI 助理回應建構器"""

    # 動態產生一份包含所有銀行關鍵字的列表
    _bank_related_keywords = ['信用卡', '卡', '銀行', '信託'] + [
        keyword 
        for bank_config in BANK_MAPPING.values() 
        for keyword in bank_config['keywords']
    ]

    @staticmethod
    def analyze_user_intent(user_message, conversation_history=None):
        """分析使用者意圖，回傳結構化意圖物件"""
        
        # 預設意圖結構
        intent = {
            "banks": [],
            "categories": [],
            "is_comparison": "比較" in user_message,
            "is_listing_banks": ("銀行" in user_message and ("列出" in user_message or "哪些" in user_message or "條列式" in user_message)),
            "has_reward_keyword": "回饋" in user_message,
            "has_card_keyword": "信用卡" in user_message or "卡" in user_message,
            "raw_message": user_message,
            "is_context_question": False,
            "is_card_benefit_question": False,
            "context_banks": []
        }
        
        # 檢查是否為上下文相關問題
        context_indicators = ["哪一張", "哪張", "哪個", "哪個有", "哪張有", "哪一張有"]
        # 檢查是否為特定卡片優惠問題
        card_benefit_indicators = ["有什麼優惠", "有什麼回饋", "優惠", "回饋", "有什麼好處"]
        
        if any(indicator in user_message for indicator in context_indicators):
            intent["is_context_question"] = True
        elif any(indicator in user_message for indicator in card_benefit_indicators):
            intent["is_card_benefit_question"] = True
            
            # 從對話歷史中提取銀行資訊
            if conversation_history:
                for msg in conversation_history[-3:]:  # 檢查最近3條對話
                    if msg.get('type') == 'ai':
                        ai_content = msg.get('content', '')
                        # 檢查AI回應中是否提到銀行
                        for standard_name, config in BANK_MAPPING.items():
                            for keyword in config['keywords']:
                                if keyword in ai_content:
                                    if standard_name not in intent["context_banks"]:
                                        intent["context_banks"].append(standard_name)
                                    break

        # 找出訊息中提及的銀行
        for standard_name, config in BANK_MAPPING.items():
            for keyword in config['keywords']:
                if keyword in user_message:
                    if standard_name not in intent["banks"]:
                        intent["banks"].append(standard_name)
                    break 
        
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
                    if word in user_message and len(word) > 1:  # 避免單字符匹配
                        if word not in intent["categories"]:
                            intent["categories"].append(word)
                        break
                    # 檢查部分詞彙匹配（如「美食」匹配「美食饗宴」）
                    elif len(word) > 2 and any(part in user_message for part in [word[:2], word[:3], word[:4]] if len(part) > 1):
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
            
        return intent

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
            context += "\n\n## 對話歷史\n"
            context += "以下是最近的對話記錄，請根據上下文理解用戶的問題：\n\n"
            
            for msg in conversation_history[-6:]:  # 只取最近6條
                if msg.get('type') == 'user':
                    context += f"用戶：{msg.get('content', '')}\n"
                elif msg.get('type') == 'ai':
                    context += f"AI：{msg.get('content', '')}\n"
            
            # 分析對話上下文
            context += "\n## 上下文分析\n"
            context += "請特別注意以下幾點：\n"
            context += "1. 如果用戶問「哪一張有XXX」，請根據前面提到的銀行或卡片範圍來回答\n"
            context += "2. 如果前面提到了特定銀行的卡片，後續問題應該限定在該銀行的範圍內\n"
            context += "3. 如果用戶問「哪一張有加油站」，請查詢資料庫中該銀行卡片的加油站回饋資料\n"
            context += "4. 優先使用提供的資料庫查詢結果，不要基於關鍵字推測\n"
            context += "5. 不要重複前面已經列出的卡片清單，而是要根據問題提供具體的回饋資訊\n\n"
            
            context += "請根據以上對話歷史和上下文分析，理解用戶當前問題的具體含義，並提供準確的回應。\n"
        
        return context

    @staticmethod
    def build_context_prompt(intent, user_id=None):
        """根據分析後的意圖建構上下文提示詞"""
        
        context = SYSTEM_PROMPT
        
        # 添加用戶資訊
        if user_id:
            user_cards = ChatbotDataService.get_user_cards(user_id)
            if user_cards:
                context += f"\n\n## 用戶資訊\n用戶已登入，目前持有的信用卡：\n"
                for card in user_cards:
                    context += f"- {card['card__bank']} {card['card__name']}"
                    if card['nickname']:
                        context += f" (暱稱: {card['nickname']})"
                    if card['is_primary']:
                        context += " [主要卡片]"
                    context += "\n"
        
        # 添加通用資料庫資訊 (可考慮快取)
        context += f"\n\n## 可查詢的資料庫資訊\n"
        context += f"注意：以下資料庫資訊是實際可查詢的資料，請優先使用這些資料回答用戶問題。\n\n"
        
        banks = ChatbotDataService.get_supported_banks()
        context += f"支援的銀行:\n"
        for bank in banks[:10]: context += f"- {bank}\n"
        if len(banks) > 10: context += f"- 等共 {len(banks)} 家銀行\n"
        
        categories = ChatbotDataService.get_reward_categories()
        context += f"消費類別:\n"
        for category in categories[:10]: context += f"- {category}\n"
        if len(categories) > 10: context += f"- 等共 {len(categories)} 個類別\n"
        
        total_cards = len(ChatbotDataService.get_all_active_cards())
        context += f"可用信用卡: 共 {total_cards} 張\n"
        
        # 處理特定卡片優惠問題
        if intent.get("is_card_benefit_question", False):
            context += f"\n\n## 特定卡片優惠問題處理\n"
            context += f"用戶詢問特定卡片的優惠資訊。請查詢資料庫中該卡片的回饋資料。\n"
            
            # 提取卡片名稱
            user_message = intent.get("raw_message", "")
            card_name = None
            bank_name = None
            
            # 從用戶訊息中提取卡片名稱
            for bank, config in BANK_MAPPING.items():
                for keyword in config['keywords']:
                    if keyword in user_message:
                        bank_name = bank
                        break
                if bank_name:
                    break
            
            # 提取卡片名稱（如 CUBE卡、momo卡 等）
            card_keywords = ["CUBE卡", "momo卡", "LINE Pay卡", "U Bear卡", "J卡", "KOKO卡"]
            for keyword in card_keywords:
                if keyword in user_message:
                    card_name = keyword
                    break
            
            if card_name and bank_name:
                context += f"\n### 查詢 {bank_name} {card_name} 的優惠：\n"
                # 查詢該卡片的回饋資料
                rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                    Q(card__bank__icontains=bank_name) & Q(card__name__icontains=card_name)
                )
                if rewards.exists():
                    for reward in rewards:
                        rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                        context += f"- {reward.category}: {rate_display} {reward.reward_type}\n"
                else:
                    context += f"- 資料庫中沒有 {bank_name} {card_name} 的回饋資料\n"
            else:
                context += f"- 無法識別具體的卡片名稱，請提供更詳細的資訊\n"

        # 處理上下文相關問題
        if intent.get("is_context_question", False) and intent.get("context_banks"):
            context += f"\n\n## 上下文問題處理\n"
            context += f"用戶問的是關於 {', '.join(intent['context_banks'])} 的上下文問題。\n"
            
            # 如果問的是特定類別的回饋
            if intent["categories"]:
                for bank in intent["context_banks"]:
                    for category in intent["categories"]:
                        context += f"\n### {bank} 在 {category} 的回饋：\n"
                        # 查詢該銀行在該類別的回饋
                        rewards = ChatbotDataService.get_cards_by_category(category)
                        bank_rewards = [r for r in rewards if bank in r.get('bank', '')]
                        if bank_rewards:
                            for reward in bank_rewards:
                                rate = f"{reward.get('min_rate', '') or ''}-{reward.get('max_rate', '') or ''}".strip('-')
                                rate_display = f"{rate}%" if rate else "未知"
                                context += f"- {reward['card_name']}: {rate_display} {reward['reward_type']}\n"
                        else:
                            context += f"- 資料庫中沒有 {bank} 在 {category} 的回饋資料\n"
            else:
                # 如果沒有指定類別，提供該銀行的所有回饋資料
                for bank in intent["context_banks"]:
                    context += f"\n### {bank} 的回饋資料：\n"
                    rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                        card__bank__icontains=bank
                    )
                    if rewards.exists():
                        for reward in rewards[:10]:
                            rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                            context += f"- {reward.card.name}: {reward.category} {rate_display} {reward.reward_type}\n"
                    else:
                        context += f"- 資料庫中沒有 {bank} 的回饋資料\n"

        # 根據意圖添加特定上下文
        if intent["banks"] and intent["has_card_keyword"]:
            for bank in intent["banks"]:
                # 如果同時問了類別，提供該銀行在該類別的回饋
                if intent["categories"]:
                    context += f"\n\n## {bank} 的信用卡：\n"
                    for category in intent["categories"]:
                        rewards = ChatbotDataService.get_cards_by_category(category)
                        bank_rewards = [r for r in rewards if bank in r['bank']]
                        if bank_rewards:
                            context += f"\n### {category} 回饋：\n"
                            for reward in bank_rewards:
                                rate = f"{reward.get('min_rate', '') or ''}-{reward.get('max_rate', '') or ''}".strip('-')
                                rate_display = f"{rate}%" if rate else "未知"
                                context += f"- {reward['card_name']}: {rate_display} {reward['reward_type']}\n"
                        else:
                            context += f"- 暫無 {category} 回饋的卡片\n"
                else:
                    # 否則，提供該銀行的卡片列表
                    cards = ChatbotDataService.get_cards_by_bank(bank)
                    if cards:
                        context += f"\n\n## {bank} 的信用卡：\n"
                        for card in cards[:5]: context += f"- {card['name']}\n"
                
                # 如果意圖包含回饋或比較，也提供回饋資料
                if intent["has_reward_keyword"] or intent["is_comparison"]:
                    rewards = ChatbotDataService._get_reward_queryset_with_sorting().filter(
                        card__bank__icontains=bank
                    )
                    if rewards.exists():
                        context += f"\n\n## {bank} 的消費回饋：\n"
                        for reward in rewards[:5]:
                            rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                            context += f"- {reward.card.name}: {reward.category} {rate_display} {reward.reward_type}\n"
        
        # 添加知識庫資訊
        context += f"\n\n## Rewardia 平台資訊\n"
        context += f"主要功能: {', '.join(REWARDIA_KNOWLEDGE_BASE['website_info']['main_features'])}\n"
        
        return context

    @staticmethod
    def enhance_response_with_data(response, intent, user_id=None):
        """根據意圖增強 AI 回應"""
        
        user_message = intent.get("raw_message", "")

        # 未登入防護：偵測個人查詢關鍵字但沒有 user_id 時，直接回覆尚未登入
        if (not user_id) and any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS):
            return "你尚未登入"
        
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
                        
                        response = "您持有的卡片有以下回饋類型：\n"
                        for reward_type, rewards in reward_types.items():
                            response += f"\n{reward_type}：\n"
                            for reward in rewards[:3]:  # 每種類型最多顯示3個
                                rate_display = ChatbotDataService._format_reward_rate_from_dict(reward)
                                response += f"- {reward['bank']} {reward['card_name']}: {rate_display} ({reward['category']})\n"
                            if len(rewards) > 3:
                                response += f"- 等共 {len(rewards)} 個{reward_type}回饋\n"
                        return response
                    else:
                        return "您持有的卡片目前沒有回饋資訊。"
                else:
                    return "您目前沒有設定任何信用卡。"
            
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
                        title = f"您持有的卡片中，{intent['categories'][0]}相關的回饋："
                        response = ChatbotDataService._build_reward_list_response(matching_cards, title)
                        return response
                    else:
                        return f"您持有的卡片中沒有{intent['categories'][0]}相關的回饋。"
            
            # 3. 查詢使用者個人卡片（僅當沒有類別查詢時）
            if any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS) and not intent["categories"]:
                user_cards = ChatbotDataService.get_user_cards(user_id)
                if user_cards:
                    response = "您目前持有的信用卡有：\n"
                    for card in user_cards:
                        response += f"- {card['card__bank']} {card['card__name']}"
                        if card['nickname']:
                            response += f" (暱稱: {card['nickname']})"
                        if card['is_primary']:
                            response += " [主要卡片]"
                        response += "\n"
                    return response
                else:
                    return "您目前沒有設定任何信用卡。"
        
        # 如果意圖是列出銀行，但回應中沒有，則補充
        if intent["is_listing_banks"] and "銀行" not in response:
            banks = ChatbotDataService.get_supported_banks()
            response = "Rewardia 支援以下銀行：\n"
            for bank in banks[:10]: response += f"- {bank}\n"
            if len(banks) > 10: response += f"- 等共 {len(banks)} 家銀行\n"
            return response # 直接回傳，因為這是主要意圖

        # 如果意圖是查詢特定銀行的卡片，但回應中沒有條列式內容，則補充
        if intent["banks"] and not intent["has_reward_keyword"] and not intent["is_comparison"]:
            # 檢查回應是否已經包含條列式內容
            if not any(line.strip().startswith('-') for line in response.split('\n')):
                for bank in intent["banks"]:
                    cards = ChatbotDataService.get_cards_by_bank(bank)
                    if cards:
                        response += f"\n\n{bank} 的信用卡：\n"
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
                            response += f"\n\n{category} 回饋最高的信用卡：\n"
                        else:
                            # 根據問題類型選擇更合適的標題
                            if any(keyword in user_message for keyword in ["有哪些", "哪些", "什麼", "什麼卡", "所有", "全部", "有", "的卡", "卡片", "信用卡"]):
                                response += f"\n\n{category}的信用卡：\n"
                            else:
                                response += f"\n\n{category} 消費的最佳回饋卡片：\n"
                        
                        for reward in rewards:
                            rate_display = ChatbotDataService._format_reward_rate_from_dict(reward)
                            response += f"- {reward['bank']} {reward['card_name']}: {rate_display} {reward['reward_type']}\n"

        # 其他增強邏輯可以根據需要繼續添加... 
        
        return response
