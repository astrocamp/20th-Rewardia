# Chatbot 意圖分析服務
from apps.chatbot.config import (
    BANK_MAPPING, COMMON_KEYWORDS, NAVIGATION_KEYWORDS, COMPARISON_KEYWORDS, 
    PERSONAL_RECOMMENDATION_KEYWORDS, CARD_COMPARISON_RECOMMENDATION_KEYWORDS, 
    RESPONSE_MESSAGES, PAGE_MAPPING, INTENT_KEYWORDS, FORMAT_CONFIG, 
    DATABASE_CONFIG, CATEGORY_KEYWORDS
)
from .data_service import ChatbotDataService
from .knowledge_base import SYSTEM_PROMPT


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
            
        # 從對話歷史中提取上下文資訊（銀行、類別、卡片等）
        if conversation_history:
            for msg in conversation_history[-DATABASE_CONFIG['conversation_history_limit']:]:  # 檢查最近對話
                if msg.get('type') == 'ai':
                    ai_content = msg.get('content', '')
                    
                    # 提取銀行資訊
                    for standard_name, config in BANK_MAPPING.items():
                        for keyword in config['keywords']:
                            if keyword in ai_content:
                                if standard_name not in intent["context_banks"]:
                                    intent["context_banks"].append(standard_name)
                                break
                    
                    # 提取類別資訊
                    context_categories = ChatbotResponseBuilder._extract_categories_from_history(ai_content)
                    for category in context_categories:
                        if category not in intent.get("context_categories", []):
                            if "context_categories" not in intent:
                                intent["context_categories"] = []
                            intent["context_categories"].append(category)

    @staticmethod
    def _extract_categories_from_history(ai_content):
        """從對話歷史中提取類別資訊"""
        categories = []
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in ai_content:
                    categories.append(category)
                    break
        
        return categories

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
                # 已登入：無論在哪個頁面都回傳導航指令，讓前端處理具體邏輯
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
            
            # 如果沒有明確的類別，嘗試從上下文獲取
            if not intent.get("categories") and intent.get("context_categories"):
                intent["categories"] = intent["context_categories"]
            
            # 分析比較類型
            if any(sep in user_message for sep in INTENT_KEYWORDS['comparison_separators']):
                # 特定卡片比較：A卡與B卡
                intent["comparison_type"] = "specific_cards"
                comparison_cards = []
                for sep in INTENT_KEYWORDS['comparison_separators']:
                    if sep in user_message:
                        parts = user_message.split(sep)
                        if len(parts) >= 2:
                            comparison_cards = [part.strip() for part in parts[:2]]
                            break
                intent["comparison_cards"] = comparison_cards
            elif has_highest:
                # 最高回饋查詢
                intent["comparison_type"] = "highest_reward"
            else:
                # 一般比較查詢
                intent["comparison_type"] = "general_comparison"

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
        from .knowledge_base import REWARDIA_KNOWLEDGE_BASE
        context += RESPONSE_MESSAGES['platform_info']['header']
        context += RESPONSE_MESSAGES['platform_info']['main_features'].format(
            features=', '.join(REWARDIA_KNOWLEDGE_BASE['website_info']['main_features'])
        )
        
        return context

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
            context += RESPONSE_MESSAGES['context']['analysis_6']
            context += RESPONSE_MESSAGES['context']['analysis_7']
            context += RESPONSE_MESSAGES['context']['analysis_conclusion']
            context += RESPONSE_MESSAGES['context']['context_examples']
            context += RESPONSE_MESSAGES['context']['example_1']
            context += RESPONSE_MESSAGES['context']['example_2']
            context += RESPONSE_MESSAGES['context']['example_3']
        
        return context

    @staticmethod
    def validate_response(response, user_message, user_id=None):
        """驗證 AI 回應是否包含虛假的卡片名稱"""
        try:
            # 基本驗證邏輯
            if not response or response.strip() == "":
                return "抱歉，我無法處理您的問題，請稍後再試或聯繫客服。"
            
            # 檢查回應長度
            if len(response) > 1000:
                response = response[:1000] + "..."
            
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
                
                response = '\n'.join(validated_lines)
            
            return response
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error validating response: {str(e)}")
            return response  # 如果驗證失敗，返回原始回應

    @staticmethod
    def enhance_response_with_data(response, intent, user_id=None, current_page=''):
        """根據意圖增強 AI 回應"""
        user_message = intent.get("raw_message", "")

        # 處理導航意圖（優先處理）
        if intent.get("is_navigation", False):
            return ChatbotResponseBuilder._handle_navigation_intent(intent, user_id, current_page)

        # 處理比較意圖（優先處理）
        if intent.get("is_comparison", False):
            from .comparison_service import ComparisonService
            return ComparisonService._handle_comparison_intent(intent, user_id)

        # 處理個人化推薦意圖（優先處理）
        if intent.get("is_personal_recommendation", False):
            return ChatbotResponseBuilder._handle_personal_recommendation_intent(intent, user_id)

        # 處理卡片比較推薦意圖（優先處理）
        if intent.get("is_card_comparison_recommendation", False):
            return ChatbotResponseBuilder._handle_card_comparison_recommendation_intent(intent, user_id)

        # 未登入防護：偵測個人查詢關鍵字但沒有 user_id 時，直接回覆尚未登入
        if (not user_id) and any(keyword in user_message for keyword in COMMON_KEYWORDS):
            return "你尚未登入"
        
        return response
