# Chatbot 資料庫查詢服務
from django.db.models import Q
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory, PendingReward
from apps.users.models import UserCard
from apps.chatbot.knowledge_base import REWARDIA_KNOWLEDGE_BASE, SYSTEM_PROMPT


class ChatbotDataService:
    """AI 助理資料庫查詢服務"""
    
    # 統一的銀行名稱配置
    BANK_MAPPING = {
        '富邦銀行': {
            'keywords': ['富邦銀行', '富邦'],
            'display_name': '富邦銀行'
        },
        '台新銀行': {
            'keywords': ['台新銀行', '台新'],
            'display_name': '台新銀行'
        },
        '玉山銀行': {
            'keywords': ['玉山銀行', '玉山'],
            'display_name': '玉山銀行'
        },
        '國泰世華': {
            'keywords': ['國泰世華', '國泰'],
            'display_name': '國泰世華'
        },
        '中國信託': {
            'keywords': ['中國信託', '中信'],
            'display_name': '中國信託'
        },
        '星展': {
            'keywords': ['星展'],
            'display_name': '星展'
        },
        '永豐': {
            'keywords': ['永豐'],
            'display_name': '永豐'
        },
        '聯邦': {
            'keywords': ['聯邦'],
            'display_name': '聯邦'
        }
    }
    
    @staticmethod
    def get_cards_by_bank(bank_name):
        """根據銀行名稱查詢信用卡"""
        try:
            # 使用統一的銀行映射配置
            bank_config = ChatbotDataService.BANK_MAPPING.get(bank_name, {'keywords': [bank_name]})
            search_terms = bank_config['keywords']
            
            # 使用 Q 物件進行 OR 查詢
            from django.db.models import Q
            query = Q()
            for term in search_terms:
                query |= Q(bank__icontains=term)
            
            cards = CreditCard.objects.filter(
                query,
                is_active=True
            ).values('name', 'bank')
            return list(cards)
        except Exception as e:
            return []
    
    @staticmethod
    def get_cards_by_category(category):
        """根據消費類別查詢最佳回饋信用卡（使用 pending_rewards 表格）"""
        try:
            # 查詢該類別回饋率最高的前5張卡片
            rewards = PendingReward.objects.filter(
                nlp_category__icontains=category
            ).select_related('card').order_by('-max_rate')[:5]
            
            result = []
            for reward in rewards:
                # 使用 max_rate 作為主要回饋率，如果沒有則使用 min_rate
                rate = float(reward.max_rate) if reward.max_rate else float(reward.min_rate) if reward.min_rate else 0
                result.append({
                    'card_name': reward.card.name,
                    'bank': reward.card.bank,
                    'rate': rate,
                    'reward_type': reward.reward_type,
                    'nlp_scope': reward.nlp_scope,
                    'min_rate': float(reward.min_rate) if reward.min_rate else None,
                    'max_rate': float(reward.max_rate) if reward.max_rate else None
                })
            return result
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_active_cards():
        """取得所有啟用的信用卡"""
        try:
            cards = CreditCard.objects.filter(is_active=True).values('name', 'bank')
            return list(cards)
        except Exception as e:
            return []
    
    @staticmethod
    def get_user_cards(user):
        """取得用戶的信用卡（需要登入）"""
        if not user.is_authenticated:
            return []
        
        try:
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
        except Exception as e:
            return []
    
    @staticmethod
    def search_cards(query):
        """搜尋信用卡（根據名稱或銀行）"""
        try:
            cards = CreditCard.objects.filter(
                Q(name__icontains=query) | Q(bank__icontains=query),
                is_active=True
            ).values('name', 'bank')[:10]
            return list(cards)
        except Exception as e:
            return []
    
    @staticmethod
    def get_reward_categories():
        """取得所有消費類別（從 pending_rewards 表格）"""
        try:
            # 從 pending_rewards 表格獲取消費類別
            categories = PendingReward.objects.values_list('nlp_category', flat=True).distinct()
            return list(categories)
        except Exception as e:
            return []
    
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
                for standard_name, config in ChatbotDataService.BANK_MAPPING.items():
                    if bank in config['keywords']:
                        normalized_bank = standard_name
                        break
                
                if normalized_bank not in normalized_banks:
                    normalized_banks.append(normalized_bank)
            
            return sorted(normalized_banks)
        except Exception as e:
            return []


class ChatbotResponseBuilder:
    """AI 助理回應建構器"""

    # 動態產生一份包含所有銀行關鍵字的列表
    _bank_related_keywords = ['信用卡', '卡', '銀行', '信託'] + [
        keyword 
        for bank_config in ChatbotDataService.BANK_MAPPING.values() 
        for keyword in bank_config['keywords']
    ]

    @staticmethod
    def analyze_user_intent(user_message):
        """分析使用者意圖，回傳結構化意圖物件"""
        
        # 預設意圖結構
        intent = {
            "banks": [],
            "categories": [],
            "is_comparison": "比較" in user_message,
            "is_listing_banks": ("銀行" in user_message and ("列出" in user_message or "哪些" in user_message or "條列式" in user_message)),
            "has_reward_keyword": "回饋" in user_message,
            "has_card_keyword": "信用卡" in user_message or "卡" in user_message,
            "raw_message": user_message
        }

        # 找出訊息中提及的銀行
        for standard_name, config in ChatbotDataService.BANK_MAPPING.items():
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
            
        return intent

    @staticmethod
    def validate_response(response, user_message, user=None):
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
    def build_context_prompt(intent, user=None):
        """根據分析後的意圖建構上下文提示詞"""
        
        context = SYSTEM_PROMPT
        
        # 添加用戶資訊
        if user and user.is_authenticated:
            user_cards = ChatbotDataService.get_user_cards(user)
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
        banks = ChatbotDataService.get_supported_banks()
        context += f"支援的銀行:\n"
        for bank in banks[:10]: context += f"- {bank}\n"
        if len(banks) > 10: context += f"- 等共 {len(banks)} 家銀行\n"
        
        categories = ChatbotDataService.get_reward_categories()
        context += f"消費類別:\n"
        for category in categories[:10]: context += f"- {category}\n"
        if len(categories) > 10: context += f"- 等共 {len(categories)} 個類別\n"
        
        total_cards = CreditCard.objects.filter(is_active=True).count()
        context += f"可用信用卡: 共 {total_cards} 張\n"
        
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
                    rewards = PendingReward.objects.filter(card__bank__icontains=bank)
                    if rewards.exists():
                        context += f"\n\n## {bank} 的消費回饋：\n"
                        for reward in rewards[:5]:
                            rate = f"{reward.min_rate or ''}-{reward.max_rate or ''}".strip('-')
                            rate_display = f"{rate}%" if rate else "未知"
                            context += f"- {reward.card.name}: {reward.nlp_category} {rate_display} {reward.reward_type}\n"
        
        # 添加知識庫資訊
        context += f"\n\n## Rewardia 平台資訊\n"
        context += f"主要功能: {', '.join(REWARDIA_KNOWLEDGE_BASE['website_info']['main_features'])}\n"
        
        return context

    @staticmethod
    def enhance_response_with_data(response, intent, user=None):
        """根據意圖增強 AI 回應"""
        
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
        
        # 如果意圖是查詢特定類別的回饋，但沒有指定銀行，且回應不完整，則補充
        if intent["categories"] and not intent["banks"]:
            if not any(line.strip().startswith('-') for line in response.split('\n')):
                for category in intent["categories"]:
                    rewards = ChatbotDataService.get_cards_by_category(category)
                    if rewards:
                        response += f"\n\n{category} 消費的最佳回饋卡片：\n"
                        for reward in rewards:
                            rate = f"{reward.get('min_rate', '') or ''}-{reward.get('max_rate', '') or ''}".strip('-')
                            rate_display = f"{rate}%" if rate else "未知"
                            response += f"- {reward['bank']} {reward['card_name']}: {rate_display} {reward['reward_type']}\n"

        # 其他增強邏輯可以根據需要繼續添加... 
        
        return response
