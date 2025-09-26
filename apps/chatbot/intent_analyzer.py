# Chatbot 意圖分析服務
import re
import logging
import time
from django.conf import settings
from apps.chatbot.config import (
    BANK_MAPPING, COMMON_KEYWORDS, NAVIGATION_KEYWORDS, COMPARISON_KEYWORDS, 
    PERSONAL_RECOMMENDATION_KEYWORDS, CARD_COMPARISON_RECOMMENDATION_KEYWORDS, 
    RESPONSE_MESSAGES, PAGE_MAPPING, INTENT_KEYWORDS, FORMAT_CONFIG, 
    DATABASE_CONFIG, CATEGORY_KEYWORDS, PERSONAL_QUERY_KEYWORDS, CARD_NAME_CLEANING,
    ERROR_DETECTION_CONFIG, DYNAMIC_RESPONSE_TEMPLATES, EXACT_MATCH_CONFIG,
    TOURISM_CATEGORY_MAPPING, TOURISM_CLARIFICATION_MESSAGES
)
from .data_service import ChatbotDataService
from .knowledge_base import SYSTEM_PROMPT, REWARDIA_KNOWLEDGE_BASE
from .comparison_service import ComparisonService

# 設置 logger
logger = logging.getLogger(__name__)


class ChatbotResponseBuilder:
    """AI 助理回應建構器"""

    # 類級別快取
    _all_cards_cache = None
    _cache_timestamp = None
    
    # 動態產生一份包含所有銀行關鍵字的列表
    _bank_related_keywords = INTENT_KEYWORDS['bank_related_keywords'] + [
        keyword 
        for bank_config in BANK_MAPPING.values() 
        for keyword in bank_config['keywords']
    ]

    @classmethod
    def _get_all_cards_cached(cls):
        """獲取快取的所有卡片資料"""
        current_time = time.time()
        
        # 如果快取不存在或超過5分鐘，重新查詢
        if cls._all_cards_cache is None or (cls._cache_timestamp and current_time - cls._cache_timestamp > 300):
            cls._all_cards_cache = ChatbotDataService.get_all_active_cards()
            cls._cache_timestamp = current_time
        
        return cls._all_cards_cache

    @staticmethod
    def _format_card_name(bank_name, card_name):
        """格式化卡片名稱，避免重複顯示銀行名稱"""
        # 如果卡片名稱已經包含銀行名稱，就不重複顯示
        if bank_name in card_name:
            return card_name
        else:
            return f"{bank_name} {card_name}"

    @staticmethod
    def _extract_card_name_from_message(user_message, bank_name=None):
        """從用戶訊息中提取卡片名稱的統一函數"""
        all_cards = ChatbotResponseBuilder._get_all_cards_cached()
        card_name = None
        matches = []
        
        # 第一優先：完整卡片名稱匹配
        for card in all_cards:
            card_full_name = card['name']
            if card_full_name in user_message:
                card_name = card_full_name
                break
        
        # 第二優先：卡片名稱關鍵部分匹配（去除銀行名稱前綴）
        if not card_name:
            for card in all_cards:
                card_full_name = card['name']
                card_key_part = card_full_name.replace(card['bank'], '').strip()
                if card_key_part and card_key_part in user_message:
                    card_name = card_full_name
                    break
        
        # 第三優先：模糊匹配邏輯，處理空格和銀行名稱差異
        if not card_name:
            for card in all_cards:
                card_full_name = card['name']
                # 移除所有空格和「銀行」後綴進行比較
                user_clean = user_message.replace(' ', '').replace('銀行', '').replace('卡', '')
                card_clean = card_full_name.replace(' ', '').replace('銀行', '').replace('卡', '')
                
                # 加入除錯日誌
                if hasattr(settings, 'DEBUG') and settings.DEBUG and '玉山' in card['bank']:
                    logger.info(f"比較: 用戶='{user_clean}' vs 卡片='{card_clean}'")
                
                if user_clean in card_clean or card_clean in user_clean:
                    matches.append(card_full_name)
                    if hasattr(settings, 'DEBUG') and settings.DEBUG:
                        logger.info(f"模糊匹配候選: {card_full_name}")
            
            # 處理匹配結果
            if len(matches) == 1:
                card_name = matches[0]
                if hasattr(settings, 'DEBUG') and settings.DEBUG:
                    logger.info(f"模糊匹配成功: {card_name}")
            elif len(matches) > 1:
                # 最多顯示前3個選項，讓用戶澄清
                options = matches[:3]
                if len(options) == 2:
                    return f"您指的是「{options[0]}」還是「{options[1]}」呢？"
                else:
                    return f"您指的是「{options[0]}」、「{options[1]}」還是「{options[2]}」呢？"
        
        # 部分匹配邏輯已整合到 _extract_card_name_from_message 函數中
        
        return card_name

    @staticmethod
    def _check_tourism_category_match(user_message):
        """檢查旅遊類別匹配，返回精確的旅遊類別或澄清訊息"""
        clarification_messages = TOURISM_CLARIFICATION_MESSAGES
        
        # 檢查每個旅遊類別映射
        for category, keywords in TOURISM_CATEGORY_MAPPING.items():
            if any(keyword in user_message for keyword in keywords):
                # 如果是需要澄清的一般旅遊類別
                if category == "旅遊" and any(keyword in user_message for keyword in ["旅遊", "出去玩"]):
                    # 檢查是否有特定的澄清訊息
                    for ambiguous_key, message in clarification_messages.items():
                        if ambiguous_key in user_message:
                            return message
                    # 預設澄清訊息（個人查詢和一般查詢都需要澄清）
                    return "你指的是「國內旅遊」或「海外旅遊」呢？"
                else:
                    # 返回精確匹配的類別
                    return category
        
        # 沒有匹配到任何旅遊類別
        return None

    @staticmethod
    def _correct_ambiguous_categories(categories, user_message):
        """修正模糊類別匹配，避免錯誤的類別識別"""
        corrected_categories = []
        
        for category in categories:
            # 檢查「中華航空」vs「中華電信」的混淆
            if category == "中華電信" and ("航空" in user_message or "聯名" in user_message):
                # 如果用戶詢問的是航空相關，跳過電信類別
                continue
            
            # 檢查「富邦人壽」vs「富邦momo」的混淆
            if category == "富邦人壽" and "momo" in user_message.lower():
                # 如果用戶詢問的是momo相關，跳過人壽類別
                continue
            # 檢查「富邦人壽」vs「富邦momo」的混淆
            if category == "富邦產險" and "momo" in user_message.lower():
                # 如果用戶詢問的是momo相關，跳過產險類別
                continue
            
            # 檢查「中國人壽」vs其他混淆
            if category == "中國人壽" and ("中信" in user_message or "中國信託" in user_message):
                # 如果用戶詢問的是中信或中國信託相關，跳過中國人壽類別
                continue
            
            corrected_categories.append(category)
        
        return corrected_categories

    @staticmethod
    def _correct_ambiguous_response(response, user_message):
        """修正回覆中的模糊類別錯誤"""
        # 修正「中華電信」錯誤匹配「中華航空」
        if "中華電信" in response and ("航空" in user_message or "聯名" in user_message):
            response = response.replace("中華電信", "您的卡片")
        
        # 修正「富邦人壽」錯誤匹配「富邦momo」
        if "富邦人壽" in response and "momo" in user_message.lower():
            response = response.replace("富邦人壽", "您的卡片")
        
        # 修正「中國人壽」錯誤匹配其他類別
        if "中國人壽" in response and ("momo" in user_message.lower() or "航空" in user_message):
            response = response.replace("中國人壽", "您的卡片")
        
        return response

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
        
        # 優先檢查個人查詢關鍵字，避免被誤識別為卡片優惠查詢
        if any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS):
            # 如果是個人查詢，不設置卡片優惠查詢標記
            pass
        elif any(indicator in user_message for indicator in context_indicators):
            intent["is_context_question"] = True
        elif any(indicator in user_message for indicator in card_benefit_indicators):
            intent["is_card_benefit_question"] = True
            # 檢查是否為「全部優惠」查詢
            all_benefits_keywords = [kw for kw in INTENT_KEYWORDS['card_benefit_indicators'] if '全部' in kw or '所有' in kw]
            if any(keyword in user_message for keyword in all_benefits_keywords):
                intent["is_all_benefits_query"] = True
            
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
                    
                    # 提取用戶卡片資訊
                    context_user_cards = ChatbotResponseBuilder._extract_user_cards_from_history(ai_content)
                    if context_user_cards:
                        if "context_user_cards" not in intent:
                            intent["context_user_cards"] = []
                        for card in context_user_cards:
                            if card not in intent["context_user_cards"]:
                                intent["context_user_cards"].append(card)

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
    def _extract_user_cards_from_history(ai_content):
        """從對話歷史中提取用戶卡片資訊"""
        # 檢查是否包含用戶卡片列表的標題
        user_card_indicators = INTENT_KEYWORDS['user_card_indicators']
        
        if any(indicator in ai_content for indicator in user_card_indicators):
            user_cards = []
            lines = ai_content.split('\n')
            for line in lines:
                line = line.strip()
                # 匹配格式：- 銀行名稱 卡片名稱
                if line.startswith('- ') and len(line) > 2:
                    card_info = line[2:].strip()  # 移除 "- "
                    # 移除可能的暱稱和主要卡片標記
                    card_info = card_info.split(' (')[0]  # 移除暱稱部分
                    card_info = card_info.split(' [')[0]  # 移除主要卡片標記
                    # 移除回饋率資訊（例如：富邦 momo卡: 6.83% 現金回饋 -> 富邦 momo卡）
                    card_info = card_info.split(':')[0].strip()
                    if card_info and len(card_info.split()) >= 2:  # 確保有銀行名稱和卡片名稱
                        user_cards.append(card_info)
            return user_cards
        
        # 如果沒有找到標準格式，嘗試從包含「您的」的句子中提取卡片名稱
        if "您的" in ai_content or "您" in ai_content:
            # 匹配模式：玉山 玉山Unicard 或類似的格式
            pattern = r'([\u4e00-\u9fff]+)\s+([\u4e00-\u9fff]+[A-Za-z]+[\u4e00-\u9fff]*)'
            matches = re.findall(pattern, ai_content)
            for match in matches:
                if len(match) == 2:
                    bank_name, card_name = match
                    # 直接檢查卡片名稱是否在資料庫中
                    all_cards = ChatbotResponseBuilder._get_all_cards_cached()
                    for card in all_cards:
                        if card['name'] == card_name:
                            return [card_name]
        
        return []

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
        # 首先檢查旅遊類別匹配
        tourism_category_result = ChatbotResponseBuilder._check_tourism_category_match(user_message)
        
        # 如果返回澄清訊息，直接設置為澄清回應
        if tourism_category_result and any(keyword in tourism_category_result for keyword in ["你指的是", "呢？"]):
            intent["clarification_needed"] = tourism_category_result
            return
        
        # 如果找到精確匹配的旅遊類別，直接使用
        if tourism_category_result:
            if tourism_category_result not in intent["categories"]:
                intent["categories"].append(tourism_category_result)
            return
        
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
        # 但如果已經識別到卡片名稱，則跳過關鍵字匹配以避免誤判
        if not intent.get("card_name"):
            for keyword in COMMON_KEYWORDS:
                if keyword in user_message:
                    for category in ChatbotDataService.get_reward_categories():
                        if keyword in category and keyword not in intent["categories"]:
                            intent["categories"].append(keyword)
                            break
        
        # 使用統一的模糊類別修正函數
        intent["categories"] = ChatbotResponseBuilder._correct_ambiguous_categories(intent["categories"], user_message)
            
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
    def _clean_card_name(card_name):
        """清理卡片名稱，移除不必要的後綴和前綴"""
        if not card_name or not isinstance(card_name, str):
            return ""
        
        # 移除前後空白
        card_name = card_name.strip()
        
        # 移除前綴
        for prefix in CARD_NAME_CLEANING['prefixes_to_remove']:
            if card_name.startswith(prefix):
                card_name = card_name[len(prefix):].strip()
        
        # 移除後綴
        for suffix in CARD_NAME_CLEANING['suffixes_to_remove']:
            if card_name.endswith(suffix):
                card_name = card_name[:-len(suffix)].strip()
        
        # 移除類別相關後綴
        for category_suffix in CARD_NAME_CLEANING['category_suffixes']:
            # 檢查是否以類別後綴結尾
            if card_name.endswith(category_suffix):
                card_name = card_name[:-len(category_suffix)].strip()
        
        return card_name.strip()

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
                
                # 修正從上下文獲取的錯誤類別
                if "電信" in intent["categories"] and ("航空" in user_message or "聯名" in user_message):
                    intent["categories"] = [cat for cat in intent["categories"] if cat != "電信"]
                
                if "人壽" in intent["categories"] and "momo" in user_message.lower():
                    intent["categories"] = [cat for cat in intent["categories"] if cat != "人壽"]
            
            # 分析比較類型
            if any(sep in user_message for sep in INTENT_KEYWORDS['comparison_separators']):
                # 特定卡片比較：A卡與B卡
                intent["comparison_type"] = "specific_cards"
                comparison_cards = []
                for sep in INTENT_KEYWORDS['comparison_separators']:
                    if sep in user_message:
                        parts = user_message.split(sep)
                        if len(parts) >= 2:
                            # 清理卡片名稱，移除不必要的後綴和前綴
                            cleaned_cards = []
                            for part in parts[:2]:
                                cleaned_card = ChatbotResponseBuilder._clean_card_name(part.strip())
                                if cleaned_card:  # 確保不是空字串
                                    cleaned_cards.append(cleaned_card)
                            
                            if len(cleaned_cards) >= 2:
                                comparison_cards = cleaned_cards
                                break
                intent["comparison_cards"] = comparison_cards
            elif has_highest:
                # 最高回饋查詢
                intent["comparison_type"] = "highest_reward"
            elif any(keyword in user_message for keyword in COMPARISON_KEYWORDS['better_than_card_indicators']):
                # 比某張卡片更高的查詢
                intent["comparison_type"] = "better_than_card"
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
            result = ChatbotResponseBuilder._extract_card_name_from_message(user_message)
            if isinstance(result, str) and result.startswith("您指的是"):
                # 返回澄清訊息
                intent["clarification_needed"] = result
            else:
                # 找到確切的卡片名稱
                intent["user_card_name"] = result
            
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
        
        # 使用類級別快取
        all_cards = ChatbotResponseBuilder._get_all_cards_cached()
        
        # 添加用戶資訊
        if user_id:
            user_cards = ChatbotDataService.get_user_cards(user_id)
            if user_cards:
                context += RESPONSE_MESSAGES['user_info']['header']
                for card in user_cards:
                    context += f"- {ChatbotResponseBuilder._format_card_name(card['card__bank'], card['card__name'])}"
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
        
        total_cards = len(all_cards)
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
                    # 如果是「全部優惠」查詢，顯示所有回饋
                    if intent.get("is_all_benefits_query", False):
                        context += f"{card_name} 的所有優惠包括：\n"
                        for reward in rewards:
                            rate_display = ChatbotDataService._format_reward_rate(reward.min_rate, reward.max_rate)
                            context += f"- {reward.category}/{reward.scope}: {rate_display} {reward.reward_type}\n"
                    else:
                        # 一般查詢，按原邏輯處理
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
                all_cards = ChatbotResponseBuilder._get_all_cards_cached()
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
            
            # 修正回覆中的錯誤類別
            response = ChatbotResponseBuilder._correct_ambiguous_response(response, user_message)
            
            return response
        except Exception as e:
            logger.error(f"Error validating response: {str(e)}")
            return response  # 如果驗證失敗，返回原始回應

    @staticmethod
    def enhance_response_with_data(response, intent, user_id=None, current_page=''):
        """根據意圖增強 AI 回應"""
        user_message = intent.get("raw_message", "")
        
        # 最終保險：修正回覆中的錯誤類別
        response = ChatbotResponseBuilder._correct_ambiguous_response(response, user_message)

        # 處理導航意圖（優先處理）
        if intent.get("is_navigation", False):
            return ChatbotResponseBuilder._handle_navigation_intent(intent, user_id, current_page)

        # 未登入防護：偵測個人查詢關鍵字但沒有 user_id 時，直接回覆尚未登入
        if (not user_id) and any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS):
            return "請先登入以查看您的卡片資訊"

        # 處理比較意圖（優先處理，特別是「比某張卡片更高」的查詢）
        if intent.get("is_comparison", False):
            return ComparisonService.handle_comparison_intent(intent, user_id)

        # 處理個人卡片查詢（優先處理，在卡片優惠查詢之前）
        # 檢查是否為個人查詢：包含個人關鍵字 或 已登入用戶詢問特定銀行的卡片（且用戶有該銀行的卡片）
        is_personal_query = any(keyword in user_message for keyword in PERSONAL_QUERY_KEYWORDS)
        
        # 如果是詢問特定銀行的卡片，需要檢查用戶是否有該銀行的卡片
        # 但是要排除「XXX卡有哪些回饋」這種卡片優惠查詢
        if not is_personal_query and user_id and not any(keyword in user_message for keyword in ["回饋", "優惠", "福利"]):
            mentioned_banks = [bank for bank in BANK_MAPPING.keys() if bank in user_message]
            if mentioned_banks and any(keyword in user_message for keyword in ["有哪些", "哪些", "有什麼", "什麼卡", "的卡", "卡片"]):
                # 檢查用戶是否有該銀行的卡片
                user_cards = ChatbotDataService.get_user_cards(user_id)
                if user_cards:
                    user_banks = set(card['card__bank'] for card in user_cards)
                    if any(bank in user_banks for bank in mentioned_banks):
                        is_personal_query = True
        
        if user_id and is_personal_query:
            # 清除可能被誤設的卡片優惠查詢標記
            intent["is_card_benefit_question"] = False
            
            # 首先檢查旅遊類別澄清邏輯
            tourism_category_result = ChatbotResponseBuilder._check_tourism_category_match(user_message)
            if tourism_category_result and any(keyword in tourism_category_result for keyword in ["你指的是", "呢？"]):
                return tourism_category_result
            
            # 在個人查詢處理開始時就進行錯誤類別檢測和修正
            if "電信" in intent["categories"] and ("航空" in user_message or "聯名" in user_message):
                # 移除錯誤的電信類別
                intent["categories"] = [cat for cat in intent["categories"] if cat != "電信"]
                logger.info(f"修正錯誤類別：移除電信，用戶訊息：{user_message}")
            
            if "人壽" in intent["categories"] and "momo" in user_message.lower():
                # 移除錯誤的人壽類別
                intent["categories"] = [cat for cat in intent["categories"] if cat != "人壽"]
                logger.info(f"修正錯誤類別：移除人壽，用戶訊息：{user_message}")
            
            user_cards = ChatbotDataService.get_user_cards(user_id)
            if user_cards:
                # 檢查是否有類別篩選（如「海外回饋」、「美食回饋」等）
                if intent["categories"]:
                    # 有類別篩選：只回覆用戶卡片中有該類別回饋的卡片
                    filtered_cards = []
                    for card in user_cards:
                        card_name = ChatbotResponseBuilder._format_card_name(card['card__bank'], card['card__name'])
                        card_rewards = ChatbotDataService.get_card_all_rewards(card_name)
                        
                        # 檢查是否有匹配的類別回饋
                        has_matching_category = False
                        for reward in card_rewards:
                            for category in intent["categories"]:
                                if (category in reward.get('category', '') or 
                                    category in reward.get('scope', '') or 
                                    category in reward.get('reward_type', '')):
                                    has_matching_category = True
                                    break
                            if has_matching_category:
                                break
                        
                        if has_matching_category:
                            filtered_cards.append(card)
                    
                    if filtered_cards:
                        # 構建回饋詳細資訊
                        # 加入除錯日誌
                        if hasattr(settings, 'DEBUG') and settings.DEBUG:
                            logger.info(f"個人查詢類別篩選: {intent['categories']}")
                            logger.info(f"用戶訊息: {user_message}")
                            logger.info(f"是否為個人查詢: {is_personal_query}")
                        
                        
                        # 強制修正錯誤的類別匹配
                        if "電信" in intent['categories'] and ("航空" in user_message or "聯名" in user_message):
                            intent['categories'] = [cat for cat in intent['categories'] if cat != "電信"]
                        
                        if "人壽" in intent['categories'] and "momo" in user_message.lower():
                            intent['categories'] = [cat for cat in intent['categories'] if cat != "人壽"]
                        
                        # 如果沒有有效的類別，使用預設回覆
                        if intent['categories']:
                            response = f"{' '.join(intent['categories'])} 回饋的信用卡:\n"
                        else:
                            response = "您的卡片回饋資訊:\n"
                        
                        # 最後的保險：直接修正回覆文字中的錯誤類別
                        response = ChatbotResponseBuilder._correct_ambiguous_response(response, user_message)
                        for card in filtered_cards:
                            card_name = ChatbotResponseBuilder._format_card_name(card['card__bank'], card['card__name'])
                            card_rewards = ChatbotDataService.get_card_all_rewards(card_name)
                            
                            # 找到該類別的回饋
                            category_rewards = []
                            for reward in card_rewards:
                                for category in intent["categories"]:
                                    if (category in reward.get('category', '') or 
                                        category in reward.get('scope', '') or 
                                        category in reward.get('reward_type', '')):
                                        category_rewards.append(reward)
                                        break
                            
                            if category_rewards:
                                # 顯示最高回饋率
                                best_reward = max(category_rewards, 
                                               key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
                                rate_display = ChatbotDataService._format_reward_rate_from_dict(best_reward)
                                response += f"- {card_name}: {rate_display} {best_reward.get('reward_type', '')}\n"
                        return response
                    else:
                        # 用戶的卡片中沒有該類別回饋，提供推薦
                        category_str = ' '.join(intent['categories'])
                        
                        # 查詢該類別的最高回饋卡片作為推薦
                        try:
                            recommendation = ComparisonService.get_highest_reward_unlimited(category_str)
                            if recommendation and "很抱歉" not in recommendation:
                                return f"您的卡片中沒有 {category_str} 回饋的信用卡。我另外推薦你：{recommendation}"
                            else:
                                return f"您的卡片中沒有 {category_str} 回饋的信用卡。"
                        except:
                            return f"您的卡片中沒有 {category_str} 回饋的信用卡。"
                else:
                    # 沒有類別篩選：檢查是否有特定銀行篩選
                    filtered_cards = user_cards
                    
                    # 檢查是否詢問特定銀行的卡片
                    mentioned_banks = []
                    for bank in BANK_MAPPING.keys():
                        if bank in user_message:
                            mentioned_banks.append(bank)
                    
                    if mentioned_banks:
                        # 只顯示特定銀行的卡片（已經在前面確認用戶有該銀行的卡片）
                        filtered_cards = [card for card in user_cards if card['card__bank'] in mentioned_banks]
                        response = RESPONSE_MESSAGES['user_cards']['header']
                        for card in filtered_cards:
                            response += f"- {ChatbotResponseBuilder._format_card_name(card['card__bank'], card['card__name'])}"
                            if card['nickname']:
                                response += f"{RESPONSE_MESSAGES['user_info']['nickname_prefix']}{card['nickname']}{RESPONSE_MESSAGES['user_info']['nickname_suffix']}"
                            if card['is_primary']:
                                response += RESPONSE_MESSAGES['user_info']['primary_marker']
                            response += "\n"
                        # 修正回覆中的錯誤類別
                        response = ChatbotResponseBuilder._correct_ambiguous_response(response, user_message)
                        return response
                    
                    # 列出篩選後的用戶卡片
                    response = RESPONSE_MESSAGES['user_cards']['header']
                    for card in filtered_cards:
                        response += f"- {ChatbotResponseBuilder._format_card_name(card['card__bank'], card['card__name'])}"
                        if card['nickname']:
                            response += f"{RESPONSE_MESSAGES['user_info']['nickname_prefix']}{card['nickname']}{RESPONSE_MESSAGES['user_info']['nickname_suffix']}"
                        if card['is_primary']:
                            response += RESPONSE_MESSAGES['user_info']['primary_marker']
                        response += "\n"
                    # 修正回覆中的錯誤類別
                    response = ChatbotResponseBuilder._correct_ambiguous_response(response, user_message)
                    return response
            else:
                return RESPONSE_MESSAGES['personal']['no_cards_set']

        # 處理特定卡片優惠查詢
        if intent.get("is_card_benefit_question", False):
            return ChatbotResponseBuilder._handle_card_benefit_query(intent)

        # 處理基於上下文的用戶卡片查詢
        if intent.get("context_user_cards") and intent.get("categories"):
            context_cards = intent["context_user_cards"]
            categories = intent["categories"]
            is_highest_query = intent.get("is_highest_query", False)
            
            if len(context_cards) > 0 and len(categories) > 0:
                category = categories[0]  # 使用第一個類別
                matching_cards = []
                
                for card_info in context_cards:
                    # 查詢該卡片的回饋資料
                    card_rewards = ChatbotDataService.get_card_all_rewards(card_info)
                    category_rewards = [r for r in card_rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
                    
                    if category_rewards:
                        # 找到該類別的最佳回饋
                        best_reward = max(category_rewards, key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
                        rate_display = ChatbotDataService._format_reward_rate_from_dict(best_reward)
                        matching_cards.append({
                            'name': card_info,
                            'rate': rate_display,
                            'reward_type': best_reward['reward_type'],
                            'rate_value': float(best_reward.get('max_rate', 0) or best_reward.get('min_rate', 0) or 0)
                        })
                
                if matching_cards:
                    if is_highest_query:
                        # 如果是「最高」查詢，找到回饋率最高的卡片
                        best_card = max(matching_cards, key=lambda x: x['rate_value'])
                        return f"在您的卡片中，{category}回饋最高的是：\n- {best_card['name']}: {best_card['rate']} {best_card['reward_type']}"
                    else:
                        # 一般查詢，列出所有匹配的卡片
                        title = f"在您的卡片中，{category}回饋的卡片有：\n"
                        card_lines = [
                            f"- {card['name']}: {card['rate']} {card['reward_type']}"
                            for card in matching_cards
                        ]
                        return title + '\n'.join(card_lines)
                else:
                    return f"很抱歉，您持有的卡片中沒有提供{category}回饋的卡片。"


        # 處理個人化推薦意圖（優先處理）
        if intent.get("is_personal_recommendation", False):
            return ChatbotResponseBuilder._handle_personal_recommendation_intent(intent, user_id)

        # 處理卡片比較推薦意圖（優先處理）
        if intent.get("is_card_comparison_recommendation", False):
            return ChatbotResponseBuilder._handle_card_comparison_recommendation_intent(intent, user_id)




        # Fallback 機制：檢查 AI 回應是否包含錯誤指示詞，並主動查詢資料庫補充正確資訊
        # 條件：有類別且（沒有特定銀行 或 包含「所有銀行」關鍵字）
        has_all_banks_keyword = any(keyword in user_message for keyword in ERROR_DETECTION_CONFIG['all_banks_keywords'])
        if intent["categories"] and (not intent["banks"] or has_all_banks_keyword):
            # 檢查是否有錯誤的「沒有資料」回答
            error_indicators = ERROR_DETECTION_CONFIG['error_indicators']
            has_error_response = any(indicator in response for indicator in error_indicators)
            
            # 計算回應中的卡片數量
            card_lines = [line for line in response.split('\n') if line.strip().startswith('-')]
            card_count = len(card_lines)
            
            # 取得用戶原始訊息
            user_message = intent.get("raw_message", "")
            
            # 如果沒有條列式內容、有錯誤回答、或卡片數量不足，則補充正確資料
            # 對於「所有銀行」問題，期望更多卡片；對於一般問題，至少3張
            expected_min_cards = DATABASE_CONFIG['expected_min_cards_all_banks'] if has_all_banks_keyword else DATABASE_CONFIG['expected_min_cards_general']
            
            if not any(line.strip().startswith('-') for line in response.split('\n')) or has_error_response or card_count < expected_min_cards:
                for category in intent["categories"]:
                    # 檢查是否詢問「最高」或「最好」的回饋
                    is_highest_only = any(keyword in user_message for keyword in ERROR_DETECTION_CONFIG['highest_keywords'])
                    
                    # 根據問題類型決定返回的卡片數量
                    limit = 1 if is_highest_only else 5
                    rewards = ChatbotDataService.get_cards_by_category(category, limit)
                    
                    if rewards:
                        # 如果有錯誤回答或卡片數量不足，先清除原始內容
                        if has_error_response or card_count < expected_min_cards:
                            response = ""
                        
                        # 根據問題類型選擇合適的標題
                        if is_highest_only:
                            response += f"\n\n{DYNAMIC_RESPONSE_TEMPLATES['highest_reward'].format(category=category)}\n"
                        else:
                            # 根據問題類型選擇更合適的標題
                            if any(keyword in user_message for keyword in ERROR_DETECTION_CONFIG['list_query_keywords']):
                                response += f"\n\n{DYNAMIC_RESPONSE_TEMPLATES['category_cards'].format(category=category)}\n"
                            else:
                                response += f"\n\n{DYNAMIC_RESPONSE_TEMPLATES['best_reward_cards'].format(category=category)}\n"
                        
                        # 補充正確的卡片推薦列表
                        for reward in rewards:
                            rate_display = ChatbotDataService._format_reward_rate_from_dict(reward)
                            response += f"- {reward['bank']} {reward['card_name']}: {rate_display} {reward['reward_type']}\n"

        # 最終保險：修正回覆中的錯誤類別
        response = ChatbotResponseBuilder._correct_ambiguous_response(response, user_message)

        return response

    @staticmethod
    def _handle_navigation_intent(intent, user_id=None, current_page=''):
        """處理導航意圖"""
        nav_type = intent.get("navigation_type")
        nav_target = intent.get("navigation_target")
        
        # 登入頁面導航
        if nav_type == "auth_page" and nav_target == "login":
            if user_id:
                # 已登入：回覆已經登入
                return RESPONSE_MESSAGES['navigation']['already_logged_in']
            else:
                # 未登入：導航到登入頁面
                return f"NAVIGATE:login:{RESPONSE_MESSAGES['navigation']['auth_pages']['login']}"
        
        # 註冊頁面導航
        elif nav_type == "auth_page" and nav_target == "register":
            if user_id:
                # 已登入：回覆已經註冊
                return RESPONSE_MESSAGES['navigation']['already_registered']
            else:
                # 未登入：導航到註冊頁面
                return f"NAVIGATE:register:{RESPONSE_MESSAGES['navigation']['auth_pages']['register']}"
        
        # 新增卡片導航
        elif nav_type == "add_card":
            if user_id:
                # 已登入：檢查是否在新增卡片頁面
                if current_page == '/users/cards/new/':
                    return RESPONSE_MESSAGES['navigation']['already_here']
                else:
                    return f"NAVIGATE:add_card:{RESPONSE_MESSAGES['navigation']['add_card']}"
            else:
                # 未登入：要求先登入
                return RESPONSE_MESSAGES['navigation']['login_required']
        
        # 會員專區相關導航
        elif nav_type == "member_area":
            if user_id:
                # 已登入：檢查是否已在會員專區
                if current_page == '/users/member/':
                    return RESPONSE_MESSAGES['navigation']['already_here']
                else:
                    return f"NAVIGATE:member_area:{RESPONSE_MESSAGES['navigation']['member_area']}"
            else:
                # 未登入
                return RESPONSE_MESSAGES['navigation']['login_required']
        
        # 一般頁面導航
        elif nav_type == "general_page":
            # 建立頁面路徑對應表以簡化邏輯
            page_paths = {
                "home": "/",
                "download": "/download/",
                "calculator": "/calculator/",
                "about": "/faq/",  # 修正路徑以符合前端導航
                "privacy": "/privacy/",
                "tos": "/tos/",
            }
            # 檢查是否已在目標頁面
            if page_paths.get(nav_target) == current_page:
                return RESPONSE_MESSAGES['navigation']['already_here']
            else:
                page_name = PAGE_MAPPING['general_pages'].get(nav_target, nav_target)
                message = RESPONSE_MESSAGES['navigation']['general_pages'].get(nav_target, f"好的，我帶你去{page_name}")
                return f"NAVIGATE:{nav_target}:{message}"
        
        # Chrome擴充功能下載
        elif nav_type == "chrome_extension":
            # 檢查是否為介紹或說明查詢
            user_message = intent.get("raw_message", "").lower()
            if any(keyword in user_message for keyword in ["介紹", "說明", "什麼是", "什麼", "如何", "怎麼", "功能", "作用"]):
                # 提供 Chrome extension 的說明，而不是導向下載頁面
                return RESPONSE_MESSAGES['navigation']['chrome_extension_description']
            else:
                # 一般下載查詢，導向下載頁面
                return f"NAVIGATE:chrome_extension:{RESPONSE_MESSAGES['navigation']['chrome_extension']}"
        
        # 登出
        elif nav_type == "logout":
            if user_id:
                return f"NAVIGATE:logout:{RESPONSE_MESSAGES['navigation']['logout']}"
            else:
                return RESPONSE_MESSAGES['navigation']['not_logged_in']
        
        return RESPONSE_MESSAGES['navigation']['default']

    @staticmethod
    def _handle_personal_recommendation_intent(intent, user_id=None):
        """處理個人化推薦意圖"""
        if not user_id:
            return "你尚未登入"
        
        recommendation_type = intent.get("recommendation_type")
        categories = intent.get("categories", [])
        banks = intent.get("banks", [])
        
        if not categories:
            return RESPONSE_MESSAGES['recommendation']['no_category_specified']
        
        category = categories[0]  # 使用第一個類別
        
        if recommendation_type == "better_cards":
            # 推薦更好的卡片
            if banks:
                # 限定銀行
                bank = banks[0]
                user_cards = ChatbotDataService.get_user_cards(user_id)
                if not user_cards:
                    return RESPONSE_MESSAGES['recommendation']['no_user_cards']
                
                # 使用第一張用戶卡片
                user_card = user_cards[0]
                user_card_name = ChatbotResponseBuilder._format_card_name(user_card['card__bank'], user_card['card__name'])
                return ChatbotResponseBuilder._get_better_cards_in_bank(user_card_name, bank, category)
            else:
                # 不限銀行
                user_cards = ChatbotDataService.get_user_cards(user_id)
                if not user_cards:
                    return RESPONSE_MESSAGES['recommendation']['no_user_cards']
                
                # 使用第一張用戶卡片
                user_card = user_cards[0]
                user_card_name = ChatbotResponseBuilder._format_card_name(user_card['card__bank'], user_card['card__name'])
                return ChatbotResponseBuilder._get_better_cards_unlimited(user_card_name, category)
        
        return RESPONSE_MESSAGES['recommendation']['general_recommendation']

    @staticmethod
    def _handle_card_comparison_recommendation_intent(intent, user_id=None):
        """處理卡片比較推薦意圖"""
        if not user_id:
            return "你尚未登入"
        
        comparison_type = intent.get("card_comparison_type")
        categories = intent.get("categories", [])
        
        if not categories:
            return RESPONSE_MESSAGES['recommendation']['no_category_specified']
        
        category = categories[0]
        user_cards = ChatbotDataService.get_user_cards(user_id)
        
        if not user_cards:
            return RESPONSE_MESSAGES['recommendation']['no_user_cards']
        
        if len(user_cards) < 2:
            return RESPONSE_MESSAGES['recommendation']['need_multiple_cards']
        
        if comparison_type == "compare_user_cards":
            # 比較用戶的卡片
            card1 = user_cards[0]
            card2 = user_cards[1]
            
            card1_name = f"{card1['card__bank']} {card1['card__name']}"
            card2_name = f"{card2['card__bank']} {card2['card__name']}"
            
            return ChatbotResponseBuilder._compare_specific_cards([card1_name, card2_name], category)
        
        return RESPONSE_MESSAGES['recommendation']['general_comparison']

    @staticmethod
    def _get_better_cards_in_bank(user_card_name, bank, category):
        """取得特定銀行中比用戶卡片更好的卡片"""
        # 先查詢用戶卡片的回饋率
        user_card_rewards = ChatbotDataService.get_card_all_rewards(user_card_name)
        user_category_rewards = [r for r in user_card_rewards if category in r.get('category', '') or category in r.get('scope', '') or category in r.get('reward_type', '')]
        
        if not user_category_rewards:
            return RESPONSE_MESSAGES['recommendation']['no_comparison_data'].format(card_name=user_card_name, category=category)
        
        # 取得用戶卡片在該類別的最高回饋率
        user_best_reward = max(user_category_rewards, key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
        user_rate = float(user_best_reward.get('max_rate', 0) or user_best_reward.get('min_rate', 0) or 0)
        
        # 查詢該銀行的其他卡片
        all_cards = ChatbotResponseBuilder._get_all_cards_cached()
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
                        'bank': card['bank'],
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
        all_cards = ChatbotResponseBuilder._get_all_cards_cached()
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
            
            return RESPONSE_MESSAGES['recommendation']['better_card_unlimited'].format(
                card_name=user_card_name, category=category, 
                bank=best_card['bank'], name=best_card['name'], 
                rate=rate_display, type=best_card['reward']['reward_type']
            )
        else:
            return RESPONSE_MESSAGES['recommendation']['no_better_card_unlimited'].format(
                card_name=user_card_name, category=category
            )

    @staticmethod
    def _compare_specific_cards(card_names, category):
        """比較特定卡片"""
        # 查詢兩張卡片的回饋資料
        all_cards = ChatbotResponseBuilder._get_all_cards_cached()
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
        title = RESPONSE_MESSAGES['comparison']['comparison_title'].format(category=category)
        card_lines = []
        
        for card in card_data:
            if card['rewards']:
                best_reward = max(card['rewards'], key=lambda x: float(x.get('max_rate', 0) or x.get('min_rate', 0) or 0))
                rate_display = ChatbotDataService._format_reward_rate_from_dict(best_reward)
                card_lines.append(f"- {card['bank']} {card['name']}: {rate_display} {best_reward['reward_type']}")
            else:
                card_lines.append(RESPONSE_MESSAGES['comparison']['no_reward'].format(
                    bank=card['bank'], name=card['name'], category=category
                ))
        
        return title + '\n'.join(card_lines)

    @staticmethod
    def _handle_card_benefit_query(intent):
        """處理特定卡片優惠查詢"""
        user_message = intent.get("raw_message", "")
        
        # 獲取所有卡片資料
        all_cards = ChatbotResponseBuilder._get_all_cards_cached()
        
        # 加入除錯日誌
        if hasattr(settings, 'DEBUG') and settings.DEBUG:
            logger.info(f"處理卡片優惠查詢: {user_message}")
            logger.info(f"所有卡片數量: {len(all_cards)}")
            logger.info(f"前5張卡片: {[card['name'] for card in all_cards[:5]]}")
        
        # 提取卡片名稱
        card_name = None
        bank_name = None
        
        # 如果是「這張卡」、「這張」等代詞查詢，嘗試從上下文提取
        if any(keyword in user_message for keyword in ["這張卡", "這張", "那張卡", "那張"]):
            # 從對話歷史中提取卡片名稱
            card_name = ChatbotResponseBuilder._extract_card_name_from_context(intent)
        
        # 從用戶訊息中提取銀行名稱
        for bank, config in BANK_MAPPING.items():
            for keyword in config['keywords']:
                if keyword in user_message:
                    bank_name = bank
                    break
            if bank_name:
                break
        
        # 動態提取卡片名稱：從資料庫中所有卡片名稱進行匹配
        # 優先進行精確匹配，避免關鍵字誤匹配
        result = ChatbotResponseBuilder._extract_card_name_from_message(user_message, bank_name)
        if isinstance(result, str) and result.startswith("您指的是"):
            # 返回澄清訊息
            return result
        else:
            # 找到確切的卡片名稱
            card_name = result
        
        # 如果沒有找到完整匹配，嘗試部分匹配
        if not card_name and bank_name:
            for card in all_cards:
                if bank_name in card['bank']:
                    # 檢查卡片名稱是否包含用戶訊息中的關鍵字
                    card_words = card['name'].split()
                    for word in card_words:
                        if len(word) > 2 and word in user_message:
                            card_name = card['name']
                            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                                logger.info(f"部分匹配成功: {card_name}")
                            break
                    if card_name:
                        break
        
        # 額外檢查：處理特殊格式的卡片名稱
        if not card_name:
            # 處理「玉山U Bear卡」格式
            for card in all_cards:
                if '玉山' in card['bank'] and 'bear' in card['name'].lower():
                    if '玉山' in user_message and ('bear' in user_message.lower() or 'ubear' in user_message.lower()):
                        card_name = card['name']
                        if hasattr(settings, 'DEBUG') and settings.DEBUG:
                            logger.info(f"玉山U Bear特殊格式匹配成功: {card_name}")
                        break
            
            # 處理「富邦 momo卡」格式
            if not card_name:
                for card in all_cards:
                    if '富邦' in card['bank'] and 'momo' in card['name'].lower():
                        if '富邦' in user_message and 'momo' in user_message.lower():
                            card_name = card['name']
                            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                                logger.info(f"富邦momo特殊格式匹配成功: {card_name}")
                        break
        
        if card_name:
            # 將找到的卡片名稱設置到 intent 中，避免關鍵字誤匹配
            intent["card_name"] = card_name
            
            # 加入除錯日誌
            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                logger.info(f"找到匹配的卡片: {card_name}")
            
            # 查詢該卡片的回饋資料
            rewards = ChatbotDataService.get_card_all_rewards(card_name)
            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                logger.info(f"卡片 {card_name} 的回饋資料數量: {len(rewards) if rewards else 0}")
            
            if rewards:
                # 如果是「全部優惠」查詢，顯示所有回饋
                if intent.get("is_all_benefits_query", False):
                    title = f"{card_name} 的所有優惠包括：\n"
                    reward_lines = [
                        f"- {reward['category']}/{reward['scope']}: {ChatbotDataService._format_reward_rate_from_dict(reward)} {reward['reward_type']}"
                        for reward in rewards
                    ]
                    return title + '\n'.join(reward_lines)
                else:
                    # 一般查詢，顯示所有回饋
                    title = f"{card_name} 提供的優惠包括：\n"
                    reward_lines = [
                        f"- {reward['category']}/{reward['scope']}: {ChatbotDataService._format_reward_rate_from_dict(reward)} {reward['reward_type']}"
                        for reward in rewards
                    ]
                    return title + '\n'.join(reward_lines)
            else:
                return f"{card_name} 目前沒有回饋資料。"
        else:
            # 加入除錯日誌
            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                logger.warning(f"無法識別卡片名稱: {user_message}")
            return "無法識別您詢問的卡片名稱，請提供更詳細的資訊。"

    @staticmethod
    def _extract_card_name_from_context(intent):
        """從對話上下文中提取卡片名稱"""
        # 檢查是否有 context_user_cards（從用戶卡片查詢中提取的）
        context_user_cards = intent.get("context_user_cards", [])
        if context_user_cards:
            # 返回第一個用戶卡片名稱
            return context_user_cards[0]
        
        # 檢查是否有 context_banks（從銀行查詢中提取的）
        context_banks = intent.get("context_banks", [])
        if context_banks:
            # 如果有銀行上下文，返回該銀行的第一個卡片
            bank_name = context_banks[0]
            # 移除「銀行」後綴進行匹配
            bank_name_clean = bank_name.replace('銀行', '').strip()
            all_cards = ChatbotResponseBuilder._get_all_cards_cached()
            for card in all_cards:
                if bank_name_clean in card['bank'] or bank_name in card['bank']:
                    return card['name']
        
        return None
