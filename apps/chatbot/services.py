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
    
    @staticmethod
    def validate_response(response, user_message, user=None):
        """驗證 AI 回應是否包含虛假的卡片名稱"""
        try:
            # 如果回應包含銀行相關內容，進行驗證
            if any(bank in user_message for bank in ['信用卡', '卡', '銀行', '信託', '中信', '富邦', '台新', '玉山', '國泰', '星展', '永豐', '聯邦']):
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
                        is_real_card = any(real_name in card_name or card_name in real_name 
                                         for real_name in real_card_names)
                        if is_real_card:
                            validated_lines.append(line)
                        else:
                            # 如果是虛假的卡片名稱，跳過這一行
                            continue
                    else:
                        validated_lines.append(line)
                
                # 如果驗證後沒有有效的卡片列表，使用資料庫資料
                if not any(line.strip().startswith('-') for line in validated_lines):
                    # 檢查是否詢問特定銀行的信用卡
                    for standard_name, config in ChatbotDataService.BANK_MAPPING.items():
                        for keyword in config['keywords']:
                            if keyword in user_message:
                                cards = ChatbotDataService.get_cards_by_bank(standard_name)
                                if cards:
                                    validated_lines.append(f"\n{standard_name} 的信用卡：")
                                    for card in cards:
                                        validated_lines.append(f"- {card['name']}")
                                break
                        if any(line.strip().startswith('-') for line in validated_lines):
                            break
                
                return '\n'.join(validated_lines)
            
            return response
        except Exception as e:
            return response
    
    @staticmethod
    def build_context_prompt(user_message, user=None):
        """建構包含資料庫資訊的上下文提示詞"""
        
        # 基礎系統提示詞
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
        
        # 動態獲取資料庫資訊
        context += f"\n\n## 可查詢的資料庫資訊\n"
        
        # 動態獲取銀行列表
        banks = ChatbotDataService.get_supported_banks()
        context += f"支援的銀行:\n"
        for bank in banks[:10]:
            context += f"- {bank}\n"
        if len(banks) > 10:
            context += f"- 等共 {len(banks)} 家銀行\n"
        
        # 動態獲取回饋類別
        categories = ChatbotDataService.get_reward_categories()
        context += f"消費類別:\n"
        for category in categories[:10]:
            context += f"- {category}\n"
        if len(categories) > 10:
            context += f"- 等共 {len(categories)} 個類別\n"
        
        # 動態獲取信用卡總數
        total_cards = CreditCard.objects.filter(is_active=True).count()
        context += f"可用信用卡: 共 {total_cards} 張\n"
        
        # 如果用戶詢問特定銀行的信用卡，直接提供該銀行的卡片資料
        matched_banks = []
        
        # 使用統一的銀行映射配置檢查關鍵字
        for standard_name, config in ChatbotDataService.BANK_MAPPING.items():
            for keyword in config['keywords']:
                if keyword in user_message and ("信用卡" in user_message or "卡" in user_message):
                    if standard_name not in matched_banks:  # 避免重複添加
                        matched_banks.append(standard_name)
                    break
        
        # 檢查是否詢問特定回饋類別
        mentioned_categories = []
        for category in ChatbotDataService.get_reward_categories():
            if category in user_message and category not in mentioned_categories:
                mentioned_categories.append(category)
        
        # 為所有匹配的銀行提供卡片資料
        for bank in matched_banks:
            if mentioned_categories:
                # 如果詢問特定回饋類別，只提供有該回饋的卡片
                context += f"\n\n## {bank} 的信用卡：\n"
                for category in mentioned_categories:
                    rewards = ChatbotDataService.get_cards_by_category(category)
                    bank_rewards = [r for r in rewards if bank in r['bank']]
                    if bank_rewards:
                        context += f"\n### {category} 回饋：\n"
                        for reward in bank_rewards:
                            if reward['min_rate'] and reward['max_rate']:
                                rate_display = f"{reward['min_rate']}%-{reward['max_rate']}%"
                            elif reward['max_rate']:
                                rate_display = f"{reward['max_rate']}%"
                            elif reward['min_rate']:
                                rate_display = f"{reward['min_rate']}%"
                            else:
                                rate_display = "未知"
                            
                            context += f"- {reward['card_name']}: {rate_display} {reward['reward_type']}"
                            if reward['nlp_scope']:
                                context += f" ({reward['nlp_scope']})"
                            context += "\n"
                    else:
                        context += f"- 暫無 {category} 回饋的卡片\n"
                break  # 只處理第一個匹配的銀行，避免重複
            else:
                # 如果沒有詢問特定回饋類別，提供所有卡片
                cards = ChatbotDataService.get_cards_by_bank(bank)
                if cards:
                    context += f"\n\n## {bank} 的信用卡：\n"
                    for card in cards[:5]:
                        # 只顯示卡片名稱，不添加銀行名稱前綴
                        context += f"- {card['name']}\n"
                
                # 如果用戶詢問回饋相關內容或比較，也提供回饋資料
                if "回饋" in user_message or "比較" in user_message:
                    rewards = PendingReward.objects.filter(card__bank__icontains=bank)
                    if rewards.exists():
                        context += f"\n\n## {bank} 的消費回饋：\n"
                        for reward in rewards[:5]:  # 只顯示前5個回饋
                            if reward.min_rate and reward.max_rate:
                                rate_display = f"{reward.min_rate}%-{reward.max_rate}%"
                            elif reward.max_rate:
                                rate_display = f"{reward.max_rate}%"
                            elif reward.min_rate:
                                rate_display = f"{reward.min_rate}%"
                            else:
                                rate_display = "未知"
                            
                            context += f"- {reward.card.name}: {reward.nlp_category} {rate_display} {reward.reward_type}"
                            if reward.nlp_scope:
                                context += f" ({reward.nlp_scope})"
                            context += "\n"
                    else:
                        context += f"\n\n## {bank} 的消費回饋：\n- 目前沒有提供消費回饋\n"
        
        # 添加知識庫資訊
        context += f"\n\n## Rewardia 平台資訊\n"
        context += f"主要功能: {', '.join(REWARDIA_KNOWLEDGE_BASE['website_info']['main_features'])}\n"
        
        return context
    
    @staticmethod
    def enhance_response_with_data(response, user_message, user=None):
        """根據用戶問題增強回應內容"""
        
        # 如果用戶詢問銀行列表（排除詢問特定銀行卡片的情況）
        if ("銀行" in user_message and ("列出" in user_message or "哪些" in user_message or "條列式" in user_message) 
            and not any(card_name in user_message for card_name in ['CUBE卡', 'momo卡', 'U Bear卡', 'LINE Pay卡', 'J 卡', 'J卡'])):
            banks = ChatbotDataService.get_supported_banks()
            if not response or "銀行" not in response:
                response = "Rewardia 支援以下銀行：\n"
                for bank in banks[:10]:
                    response += f"- {bank}\n"
                if len(banks) > 10:
                    response += f"- 等共 {len(banks)} 家銀行\n"
        
        # 如果用戶詢問比較
        if "比較" in user_message:
            # 找出用戶要比較的銀行和卡片組合
            bank_card_pairs = []
            for standard_name, config in ChatbotDataService.BANK_MAPPING.items():
                for keyword in config['keywords']:
                    if keyword in user_message:
                        # 檢查該銀行名稱後面是否跟著卡片名稱
                        bank_index = user_message.find(keyword)
                        if bank_index != -1:
                            # 在銀行名稱後面尋找卡片名稱
                            after_bank = user_message[bank_index + len(keyword):]
                            # 查找常見的卡片名稱
                            card_names = ['CUBE卡', 'momo卡', 'U Bear卡', 'LINE Pay卡', 'J 卡', 'J卡']
                            for card_name in card_names:
                                if card_name in after_bank:
                                    bank_card_pairs.append((standard_name, card_name))
                                    break
                        break
            
            if bank_card_pairs:
                response = "比較結果：\n\n"
                for bank, card_name in bank_card_pairs:
                    # 查詢該銀行的指定卡片回饋資料
                    rewards = PendingReward.objects.filter(
                        card__bank__icontains=bank,
                        card__name__icontains=card_name
                    )
                    if rewards.exists():
                        response += f"{bank} {card_name} 回饋：\n"
                        for reward in rewards:
                            if reward.min_rate and reward.max_rate:
                                rate_display = f"{reward.min_rate}%-{reward.max_rate}%"
                            elif reward.max_rate:
                                rate_display = f"{reward.max_rate}%"
                            elif reward.min_rate:
                                rate_display = f"{reward.min_rate}%"
                            else:
                                rate_display = "未知"
                            
                            response += f"{reward.nlp_category} {rate_display} {reward.reward_type}"
                            if reward.nlp_scope:
                                response += f" ({reward.nlp_scope})"
                            response += "\n"
                    else:
                        response += f"{bank} {card_name} 目前沒有回饋資訊。\n\n"
        
        # 如果用戶詢問特定銀行是否有回饋
        elif "回饋" in user_message:
            # 檢查 Gemini 是否已經提供了回饋資訊（必須包含具體的回饋資料）
            has_reward_info = (any(keyword in response.lower() for keyword in ['cashback', 'points', '%']) or 
                              ('回饋' in response.lower() and any(keyword in response.lower() for keyword in ['%', 'cashback', 'points'])))
            
            if not has_reward_info:
                for standard_name, config in ChatbotDataService.BANK_MAPPING.items():
                    for keyword in config['keywords']:
                        if keyword in user_message:
                            # 查詢該銀行的回饋資料
                            rewards = PendingReward.objects.filter(card__bank__icontains=keyword)
                            if rewards.exists():
                                if not response or f"{standard_name} 提供以下消費回饋" not in response:
                                    # 檢查是否詢問特定卡片
                                    mentioned_cards = [card_name for card_name in ['CUBE卡', 'momo卡', 'U Bear卡', 'LINE Pay卡', 'J 卡', 'J卡'] if card_name in user_message]
                                    
                                    if mentioned_cards:
                                        response += f"\n\n{standard_name} 提供以下消費回饋：\n"
                                        for card_name in mentioned_cards:
                                            card_rewards = rewards.filter(card__name__icontains=card_name)
                                            for reward in card_rewards:
                                                if reward.min_rate and reward.max_rate:
                                                    rate_display = f"{reward.min_rate}%-{reward.max_rate}%"
                                                elif reward.max_rate:
                                                    rate_display = f"{reward.max_rate}%"
                                                elif reward.min_rate:
                                                    rate_display = f"{reward.min_rate}%"
                                                else:
                                                    rate_display = "未知"
                                                
                                                response += f"- {reward.card.name}: {reward.nlp_category} {rate_display} {reward.reward_type}"
                                                if reward.nlp_scope:
                                                    response += f" ({reward.nlp_scope})"
                                                response += "\n"
                                    else:
                                        # 沒有指定卡片，顯示所有回饋
                                        response += f"\n\n{standard_name} 提供以下消費回饋：\n"
                                        for reward in rewards[:5]:  # 只顯示前5個回饋
                                            if reward.min_rate and reward.max_rate:
                                                rate_display = f"{reward.min_rate}%-{reward.max_rate}%"
                                            elif reward.max_rate:
                                                rate_display = f"{reward.max_rate}%"
                                            elif reward.min_rate:
                                                rate_display = f"{reward.min_rate}%"
                                            else:
                                                rate_display = "未知"
                                            
                                            response += f"- {reward.card.name}: {reward.nlp_category} {rate_display} {reward.reward_type}"
                                            if reward.nlp_scope:
                                                response += f" ({reward.nlp_scope})"
                                            response += "\n"
                            else:
                                if not response or standard_name not in response:
                                    response += f"\n\n{standard_name} 目前沒有提供消費回饋。\n"
                            break
                    if "回饋" in response:
                        break
        
        # 如果用戶詢問特定銀行的卡片，且原始回應中沒有詳細的卡片列表
        # 但只有在不是詢問回饋相關問題時才添加信用卡列表
        if "回饋" not in user_message and "比較" not in user_message:
            for bank in ChatbotDataService.get_supported_banks():
                if bank in user_message:
                    # 檢查是否已經有該銀行的具體卡片列表（不是只有標題）
                    has_bank_cards = any([
                        f"- {bank}" in response,  # 有條列式列表
                        f"* {bank}" in response,  # 有星號列表
                        f"{bank}" in response and "卡" in response and ("-" in response or "*" in response)  # 有列表符號
                    ])
                    
                    # 如果沒有該銀行的卡片列表，才添加
                    if not has_bank_cards:
                        cards = ChatbotDataService.get_cards_by_bank(bank)
                        if cards:
                            response += f"\n\n{bank} 的信用卡：\n"
                            for card in cards[:5]:
                                # 只顯示卡片名稱，不添加銀行名稱前綴
                                response += f"- {card['name']}\n"
                    break
        
        # 如果用戶詢問特定消費類別的回饋，且沒有指定特定銀行
        mentioned_banks = [bank for bank in ChatbotDataService.get_supported_banks() if bank in user_message]
        if not mentioned_banks:  # 只有在沒有指定特定銀行時，才顯示所有銀行的最佳回饋
            for category in ChatbotDataService.get_reward_categories():
                if category in user_message:
                    rewards = ChatbotDataService.get_cards_by_category(category)
                    if rewards:
                        response += f"\n\n{category} 消費的最佳回饋卡片：\n"
                        for reward in rewards:
                            # 顯示回饋率範圍
                            if reward['min_rate'] and reward['max_rate']:
                                rate_display = f"{reward['min_rate']}%-{reward['max_rate']}%"
                            elif reward['max_rate']:
                                rate_display = f"{reward['max_rate']}%"
                            elif reward['min_rate']:
                                rate_display = f"{reward['min_rate']}%"
                            else:
                                rate_display = "未知"
                            
                            response += f"- {reward['bank']} {reward['card_name']}: {rate_display} {reward['reward_type']}"
                            if reward['nlp_scope']:
                                response += f" ({reward['nlp_scope']})"
                            response += "\n"
                    break
        
        # 如果用戶詢問特定卡片的回饋比較，提供相關回饋資料
        if "回饋" in user_message and "比較" in user_message:
            # 嘗試識別用戶詢問的特定卡片
            mentioned_cards = []
            for bank in ChatbotDataService.get_supported_banks():
                if bank in user_message:
                    cards = ChatbotDataService.get_cards_by_bank(bank)
                    for card in cards:
                        card_name = card['name']
                        # 檢查卡片名稱是否在用戶問題中被提及
                        if card_name in user_message or any(word in user_message for word in card_name.split()):
                            mentioned_cards.append({
                                'bank': card['bank'],
                                'name': card_name,
                                'full_name': f"{card['bank']} {card_name}"
                            })
            
            if mentioned_cards:
                response += f"\n\n指定卡片回饋比較：\n"
                # 查詢這些特定卡片的回饋資料
                for card in mentioned_cards:
                    response += f"\n{card['full_name']}：\n"
                    # 查詢該卡片在各個消費類別的回饋
                    card_rewards = []
                    for category in ChatbotDataService.get_reward_categories():
                        rewards = ChatbotDataService.get_cards_by_category(category)
                        for reward in rewards:
                            if (reward['bank'] in card['bank'] and 
                                reward['card_name'] in card['name']):
                                card_rewards.append({
                                    'category': category,
                                    'reward': reward
                                })
                    
                    if card_rewards:
                        for item in card_rewards[:5]:  # 只顯示前5個類別
                            reward = item['reward']
                            if reward['min_rate'] and reward['max_rate']:
                                rate_display = f"{reward['min_rate']}%-{reward['max_rate']}%"
                            elif reward['max_rate']:
                                rate_display = f"{reward['max_rate']}%"
                            elif reward['min_rate']:
                                rate_display = f"{reward['min_rate']}%"
                            else:
                                rate_display = "未知"
                            
                            response += f"- {item['category']}: {rate_display} {reward['reward_type']}"
                            if reward['nlp_scope']:
                                response += f" ({reward['nlp_scope']})"
                            response += "\n"
                    else:
                        response += "- 暫無回饋資料\n"
            else:
                # 如果無法識別特定卡片，提供一般回饋比較
                main_categories = ['電商', '交通運輸', '百貨公司', '加油站', '旅遊']
                response += f"\n\n主要消費類別回饋比較：\n"
                
                for category in main_categories:
                    rewards = ChatbotDataService.get_cards_by_category(category)
                    if rewards:
                        response += f"\n{category} 消費：\n"
                        for reward in rewards[:2]:
                            if reward['min_rate'] and reward['max_rate']:
                                rate_display = f"{reward['min_rate']}%-{reward['max_rate']}%"
                            elif reward['max_rate']:
                                rate_display = f"{reward['max_rate']}%"
                            elif reward['min_rate']:
                                rate_display = f"{reward['min_rate']}%"
                            else:
                                rate_display = "未知"
                            
                            response += f"- {reward['bank']} {reward['card_name']}: {rate_display} {reward['reward_type']}"
                            if reward['nlp_scope']:
                                response += f" ({reward['nlp_scope']})"
                            response += "\n"
        
        return response
