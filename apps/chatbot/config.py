# Chatbot 配置檔案
# 銀行映射配置
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
    '永豐銀行': {
        'keywords': ['永豐銀行', '永豐'],
        'display_name': '永豐銀行'
    },
    '聯邦銀行': {
        'keywords': ['聯邦銀行', '聯邦'],
        'display_name': '聯邦銀行'
    },
    '滙豐銀行': {
        'keywords': ['滙豐銀行', '滙豐'],
        'display_name': '滙豐銀行'
    },
    '第一銀行': {
        'keywords': ['第一銀行', '第一'],
        'display_name': '第一銀行'
    },
    '合作金庫': {
        'keywords': ['合作金庫', '合庫'],
        'display_name': '合作金庫'
    },
    '兆豐銀行': {
        'keywords': ['兆豐銀行', '兆豐'],
        'display_name': '兆豐銀行'
    },
    '遠東銀行': {
        'keywords': ['遠東銀行', '遠東'],
        'display_name': '遠東銀行'
    },
    '凱基銀行': {
        'keywords': ['凱基銀行', '凱基'],
        'display_name': '凱基銀行'
    },
    '樂天銀行': {
        'keywords': ['樂天銀行', '樂天'],
        'display_name': '樂天銀行'
    },
    '彰化銀行': {
        'keywords': ['彰化銀行', '彰化'],
        'display_name': '彰化銀行'
    },
    '華南銀行': {
        'keywords': ['華南銀行', '華南'],
        'display_name': '華南銀行'
    },
    '新光銀行': {
        'keywords': ['新光銀行', '新光'],
        'display_name': '新光銀行'
    },
    '上海商銀': {
        'keywords': ['上海商銀', '上海'],
        'display_name': '上海商銀'
    },
    '美國運通': {
        'keywords': ['美國運通', '美國'],
        'display_name': '美國運通'
    },
    '渣打銀行': {
        'keywords': ['渣打銀行', '渣打'],
        'display_name': '渣打銀行'
    },
    '陽信銀行': {
        'keywords': ['陽信銀行', '陽信'],
        'display_name': '陽信銀行'
    },
    'Line Bank': {
        'keywords': ['Line Bank', 'LineBank'],
        'display_name': 'Line Bank'
    },
    '將來銀行': {
        'keywords': ['將來銀行', '將來'],
        'display_name': '將來銀行'
    },
    '元大銀行': {
        'keywords': ['元大銀行', '元大'],
        'display_name': '元大銀行'
    },
    '台中銀行': {
        'keywords': ['台中銀行', '台中'],
        'display_name': '台中銀行'
    },
    '王道銀行': {
        'keywords': ['王道銀行', '王道'],
        'display_name': '王道銀行'
    }
}

# 常見關鍵字配置（用於意圖分析）
COMMON_KEYWORDS = [
    # 購物相關
    "購物", "百貨", "線上購物", "網購", "電商", "商城", "商店",
    # 美食相關  
    "美食", "饗宴", "餐廳", "吃飯", "用餐", "料理", "食物", "餐飲",
    # 加油相關
    "加油", "加油站", "油錢", "汽油", "中油", "台塑",
    # 旅遊相關
    "旅遊", "住宿", "飯店", "旅館", "出遊", "旅行", "觀光", "酒店",
    # 電影相關
    "電影", "電影票", "影城", "戲院", "看電影", "電影院", "票卷",
    # 保險相關
    "保險", "人壽", "保費", "投保", "保障",
    # 海外相關
    "海外", "國外", "出國", "境外", "國外消費", "海外消費",
    # 3C通訊相關
    "3C", "通訊", "手機", "電信", "網路", "通話", "上網", "電信費"
]

# 個人查詢關鍵字
PERSONAL_QUERY_KEYWORDS = [
    "我有哪些卡", "我的卡", "我持有", "我的信用卡", "我有的卡",
    "我設定的", "我加入的", "我設的", "我加的", "我的哪些有", "我的有哪些",
    "我有哪些信用卡", "我的卡片", "我的卡片有哪些", "我有哪些卡片", "我登記的卡片"
]

# 回饋類型查詢關鍵字
REWARD_TYPE_KEYWORDS = [
    "回饋類型", "回饋種類", "哪些類型", "哪些種類", "什麼類型", "什麼種類", "什麼優惠", "哪些優惠", "哪些回饋"
]

# 導航相關關鍵字
NAVIGATION_KEYWORDS = {
    # 會員專區相關
    'member_area': [
        "會員專區", "我的資料", "我的個人資料", "個人資料"
    ],
    # 一般頁面導航
    'general_pages': {
        'home': ["去首頁", "首頁"],
        'download': ["去下載專區", "下載專區"],
        'calculator': ["去優惠試算", "優惠試算"],
        'about': ["去關於功能", "關於功能"],
        'privacy': ["隱私權政策", "去隱私權政策", "隱私權"],
        'tos': ["服務條款", "去服務條款", "條款"]
    },
    # 新增卡片相關
    'add_card': ["擷取卡號", "擷取卡片", "去新增卡片", "新增卡片", "加卡片", "去加卡片"],
    # 登出相關
    'logout': ["登出", "退出", "登出會員"],
    # 登入註冊相關
    'auth_pages': {
        'login': ["登入", "去登入", "登入頁面"],
        'register': ["註冊", "去註冊", "註冊頁面"]
    }
}

# 消費類別關鍵字映射
CATEGORY_KEYWORDS = {
    "保險": ["保險", "人壽", "產險", "健康險", "意外險"],
    "加油": ["加油", "加油站", "油品", "汽油", "柴油"],
    "線上購物": ["線上購物", "網購", "電商", "購物", "網路購物"],
    "旅遊": ["旅遊", "住宿", "飯店", "機票", "交通", "國外", "出國", "渡假"],
    "餐飲": ["餐飲", "餐廳", "美食", "吃飯", "用餐", "聚餐", "聚會"],
    "超市": ["超市", "量販", "全聯", "家樂福", "Costco"],
    "便利商店": ["便利商店", "超商", "7-11", "全家", "萊爾富"],
    "電影": ["電影", "戲院", "娛樂", "看電影"],
    "交通": ["交通", "捷運", "公車", "計程車", "Uber"]
}

# 比較相關關鍵字
COMPARISON_KEYWORDS = {
    # 比較指示詞
    'comparison_indicators': [
        "比較", "比", "對比", "對照", "哪一個", "哪個", "哪張", "哪一張"
    ],
    # 最高級指示詞
    'highest_indicators': [
        "最高", "最好", "最佳", "最優", "最大", "最棒", "最強"
    ],
    # 銀行限定指示詞
    'bank_limited_indicators': [
        "銀行", "哪一家", "哪個銀行", "在.*銀行"
    ],
    # 比某張卡片更高的指示詞
    'better_than_card_indicators': [
        "比我", "比我的", "比這張", "比那張", "更高的", "更高的嗎", "更好的", "更好的嗎"
    ]
}

# 個人化推薦關鍵字
PERSONAL_RECOMMENDATION_KEYWORDS = {
    # 個人化指示詞
    'personal_indicators': [
        "我喜歡", "我常", "我愛", "我習慣", "我經常", "我偏好", "我最常"
    ],
    # 推薦指示詞
    'recommendation_indicators': [
        "最適合我", "適合我", "推薦給我", "推薦我", "建議我", "給我建議"
    ],
    # 特定商家/類別
    'specific_merchants': [
        "壽司郎", "爭鮮", "藏壽司", "海壽司", "點爭鮮"
    ]
}

# 卡片比較推薦關鍵字
CARD_COMPARISON_RECOMMENDATION_KEYWORDS = {
    # 比較指示詞
    'comparison_indicators': [
        "有比", "比我的", "比這張", "比這張卡", "比我的卡", "比我的卡片"
    ],
    # 優惠/回饋指示詞
    'reward_indicators': [
        "更多", "更高", "更好", "更優", "更棒", "更強", "更佳","更划算"
    ],
    # 其他卡片指示詞
    'other_card_indicators': [
        "其它卡片", "其他卡片", "別的卡片", "其他卡", "別的卡", "其它卡"
    ],
    # 銀行限定指示詞
    'bank_limited_indicators': [
        "銀行", "哪一家", "哪個銀行", "在.*銀行"
    ]
}

# 回應訊息配置
RESPONSE_MESSAGES = {
    'navigation': {
        'member_area': "好的，我帶你去會員專區",
        'already_here': "這裡就是了喔", 
        'login_required': "請先登入會員",
        'logout': "好的，記得常回來喔",
        'not_logged_in': "您尚未登入",
        'default': "好的，我帶你去",
        'add_card': "好的，我帶你去新增卡片",
        'already_logged_in': "你已經登入了喔",
        'already_registered': "你已經註冊過了喔",
        'general_pages': {
            'home': "好的，我帶你去首頁",
            'download': "好的，我帶你去下載專區",
            'calculator': "好的，我帶你去優惠試算", 
            'about': "好的，我帶你去關於功能",
            'privacy': "好的，我帶你去隱私權政策",
            'tos': "好的，我帶你去服務條款"
        },
        'auth_pages': {
            'login': "好的，我帶你去登入頁面",
            'register': "好的，我帶你去註冊頁面"
        }
    },
    'comparison': {
        'no_cards_found': "無法找到指定的卡片進行比較",
        'no_category_specified': "請指定要比較的回饋類別",
        'no_cards_specified': "請指定要比較的兩張卡片",
        'no_data_found': "目前沒有 {category} 相關的回饋資料",
        'bank_no_data': "{bank} 目前沒有 {category} 相關的回饋資料",
        'comparison_title': "{category} 回饋比較：\n\n",
        'no_reward': "- {bank} {name}: 無 {category} 回饋\n",
        'highest_in_bank': "{bank} 在 {category} 回饋最高的信用卡：\n- {name}: {rate} {type}",
        'highest_unlimited': "{category} 回饋最高的信用卡：\n- {bank} {name}: {rate} {type}",
        'highest_tied': "{bank} 在 {category} 回饋最高的信用卡（並列）：\n",
        'highest_tied_unlimited': "{category} 回饋最高的信用卡（並列）：\n",
        'cards_in_bank': "{bank} 在 {category} 回饋的信用卡：\n",
        'cards_unlimited': "{category} 回饋的信用卡：\n"
    },
    'personal': {
        'no_cards_set': "您目前沒有設定任何信用卡",
        'no_rewards': "您持有的卡片目前沒有回饋資訊",
        'no_category_specified': "請告訴我您喜歡的消費類別，例如：出國、購物、看電影、現金回饋等",
        'no_card_specified': "請告訴我您要比較的卡片名稱，例如：我的富邦卡、我的中信卡等"
    },
    'recommendation': {
        'no_better_cards': "很抱歉，目前沒有比您的 {card_name} 在 {category} 回饋更高的其他卡片。您的卡片已經是 {category} 方面回饋最高的選擇了！",
        'found_better_cards': "是的！有比您的 {card_name} 在 {category} 回饋更高的卡片：\n\n- {bank} {better_card_name}: {rate} {reward_type}\n\n這張卡片的回饋率比您目前的卡片更高！",
        'personal_recommendation_bank': "根據您喜歡 {category} 的消費習慣，{bank} 最適合您的信用卡是：\n\n- {name}: {rate} {type}\n\n這張卡片在 {category} 消費時能給您最高的回饋！",
        'personal_recommendation_unlimited': "根據您喜歡 {category} 的消費習慣，最適合您的信用卡是：\n\n- {bank} {name}: {rate} {type}\n\n這張卡片在 {category} 消費時能給您最高的回饋！",
        'bank_no_recommendation': "很抱歉，{bank} 目前沒有 {category} 相關的回饋信用卡。建議您可以考慮其他銀行，或選擇該銀行的其他回饋類別。",
        'no_recommendation': "很抱歉，目前沒有 {category} 相關的回饋信用卡。建議您可以選擇其他消費類別，或聯繫我們了解更多信用卡資訊。",
        'no_comparison_data': "您的 {card_name} 在 {category} 方面沒有回饋資料，無法進行比較。",
        'better_card_in_bank': "是的！{bank} 有比您的 {card_name} 在 {category} 回饋更高的卡片：\n\n- {name}: {rate} {type}\n\n這張卡片的回饋率比您目前的卡片更高！",
        'no_better_card_in_bank': "很抱歉，{bank} 目前沒有比您的 {card_name} 在 {category} 回饋更高的其他卡片。您的卡片已經是該銀行在 {category} 方面回饋最高的選擇了！"
    },
    'context': {
        'conversation_history': "\n\n## 對話歷史\n",
        'history_description': "以下是最近的對話記錄，請根據上下文理解用戶的問題：\n\n",
        'user_prefix': "用戶：",
        'ai_prefix': "AI：",
        'context_analysis': "\n## 上下文分析\n",
        'analysis_points': "請特別注意以下幾點：\n",
        'analysis_1': "1. 如果用戶問「哪一個回饋最高」、「哪一張最好」，請根據前面對話中提到的類別（如保險、加油、線上購物等）來回答\n",
        'analysis_2': "2. 如果前面提到了特定類別的回饋資訊，後續的比較問題應該限定在該類別範圍內\n",
        'analysis_3': "3. 如果用戶問「哪一張有XXX」，請根據前面提到的銀行或卡片範圍來回答\n",
        'analysis_4': "4. 如果前面提到了特定銀行的卡片，後續問題應該限定在該銀行的範圍內\n",
        'analysis_5': "5. 優先使用提供的資料庫查詢結果，不要基於關鍵字推測\n",
        'analysis_6': "6. 不要重複前面已經列出的卡片清單，而是要根據問題提供具體的回饋資訊\n",
        'analysis_7': "7. 特別注意：如果用戶問「哪一個回饋最高」，且前面對話提到了特定類別，請直接比較該類別的回饋率\n\n",
        'analysis_conclusion': "請根據以上對話歷史和上下文分析，理解用戶當前問題的具體含義，並提供準確的回應。\n",
        'context_examples': "\n## 上下文理解範例\n",
        'example_1': "範例1：如果前面對話提到「保險回饋」，用戶問「哪一個回饋最高」，應該比較保險類別的回饋率\n",
        'example_2': "範例2：如果前面列出了富邦的卡片，用戶問「哪一張最好」，應該限定在富邦銀行範圍內\n",
        'example_3': "範例3：如果前面提到了線上購物的回饋，用戶問「哪一個」，應該理解為線上購物類別的回饋比較\n\n"
    },
    'user_info': {
        'header': "\n\n## 用戶資訊\n用戶已登入，目前持有的信用卡：\n",
        'nickname_prefix': " (暱稱: ",
        'nickname_suffix': ")",
        'primary_marker': " [主要卡片]"
    },
    'database_info': {
        'header': "\n\n## 可查詢的資料庫資訊\n",
        'description': "注意：以下資料庫資訊是實際可查詢的資料，請優先使用這些資料回答用戶問題。\n\n",
        'supported_banks': "支援的銀行:\n",
        'more_banks': "- 等共 {count} 家銀行\n",
        'categories': "消費類別:\n",
        'more_categories': "- 等共 {count} 個類別\n",
        'total_cards': "可用信用卡: 共 {count} 張\n"
    },
    'card_benefit': {
        'header': "\n\n## 特定卡片優惠問題處理\n",
        'description': "用戶詢問特定卡片的優惠資訊。請查詢資料庫中該卡片的回饋資料。\n",
        'query_prefix': "\n### 查詢 ",
        'query_suffix': " 的優惠：\n",
        'no_data': "- 資料庫中沒有 {name} 的回饋資料\n",
        'unrecognized': "- 無法識別具體的卡片名稱，請提供更詳細的資訊\n"
    },
    'context_question': {
        'header': "\n\n## 上下文問題處理\n",
        'description': "用戶問的是關於 {banks} 的上下文問題。\n",
        'bank_category_prefix': "\n### ",
        'bank_category_suffix': " 的回饋：\n",
        'no_bank_data': "- 資料庫中沒有 {bank} 在 {category} 的回饋資料\n"
    },
    'bank_cards': {
        'header': "\n\n## {bank} 的信用卡：\n",
        'category_rewards': "\n### {category} 回饋：\n",
        'no_category_rewards': "- 暫無 {category} 回饋的卡片\n"
    },
    'bank_rewards': {
        'header': "\n\n## {bank} 的消費回饋：\n"
    },
    'platform_info': {
        'header': "\n\n## Rewardia 平台資訊\n",
        'main_features': "主要功能: {features}\n"
    },
    'supported_banks': {
        'header': "Rewardia 支援以下銀行：\n"
    },
    'reward_types': {
        'header': "您持有的卡片有以下回饋類型：\n",
        'type_prefix': "\n{type}：\n",
        'more_rewards': "- 等共 {count} 個{type}回饋\n"
    },
    'user_cards': {
        'header': "您目前持有的信用卡有：\n"
    },
    'user_category_rewards': {
        'header': "您持有的卡片中，{category}相關的回饋："
    },
    'no_user_category_rewards': "您持有的卡片中沒有{category}相關的回饋。",
    'card_rewards': {
        'header': "{name}的回饋：\n",
        'no_rewards': "{name}目前沒有回饋資料。",
        'unrecognized_card': "無法識別您詢問的卡片名稱，請提供更詳細的資訊。"
    }
}

# 頁面映射配置
PAGE_MAPPING = {
    'general_pages': {
        'home': '首頁',
        'download': '下載專區', 
        'calculator': '優惠試算',
        'about': '關於功能',
        'privacy': '隱私權政策',
        'tos': '服務條款'
    },
    'auth_pages': {
        'login': '登入頁面',
        'register': '註冊頁面'
    }
}

# 意圖分析關鍵字
INTENT_KEYWORDS = {
    'context_indicators': ["哪一張", "哪張", "哪個", "哪個有", "哪張有", "哪一張有"],
    'card_benefit_indicators': ["有什麼優惠", "有什麼回饋", "優惠", "回饋", "有什麼好處", "全部優惠", "所有優惠", "全部回饋", "所有回饋"],
    'comparison_separators': ["與", "及", "和", "vs"],
    'user_card_indicators': [
        "您目前持有的信用卡有",
        "持有的信用卡", 
        "在您的卡片中",
        "您的卡片中",
        "您持有的卡片中"
    ],
    'bank_related_keywords': ['信用卡', '卡', '銀行', '信託'],
    'comparison_prefixes': ["請比較", "比較", "比比看", "比看看", "比一下", "請比一下"],
    'card_suffixes': ["卡", "信用卡"],
    'priority_categories': ['保險', '電影', '購物', '出國', '現金回饋', '紅利回饋'],
    'highest_indicators': ["最高", "最好", "最佳", "最優", "最大", "最棒", "所有", "全部", "全部銀行", "所有銀行"],
    'bank_limited_keywords': ["銀行", "哪一家", "哪個銀行"]
}

# 卡片名稱清理配置
CARD_NAME_CLEANING = {
    # 需要移除的後綴（從卡片名稱結尾移除）
    'suffixes_to_remove': [
        "在回饋", "的回饋", "關於", "的優惠", "的回饋率", "在", "的", "卡", "信用卡",
        "在旅遊", "在購物", "在加油", "在保險", "在電影", "在美食", "在超市",
        "在便利商店", "在交通", "在線上購物", "在餐飲", "關於旅遊", "關於購物",
        "關於加油", "關於保險", "關於電影", "關於美食", "關於超市", "關於便利商店",
        "關於交通", "關於線上購物", "關於餐飲"
    ],
    # 需要移除的前綴（從卡片名稱開頭移除）
    'prefixes_to_remove': [
        "請比較", "比較", "比比看", "比看看", "比一下", "請比一下", "比較一下",
        "請比較一下", "比一比", "比看看", "比較看看"
    ],
    # 需要移除的類別相關後綴
    'category_suffixes': [
        "旅遊", "購物", "加油", "保險", "電影", "美食", "超市", "便利商店", 
        "交通", "線上購物", "餐飲", "海外", "國內", "國外", "出國"
    ]
}

# 格式化相關配置
FORMAT_CONFIG = {
    'unknown_rate': "未知",
    'rate_suffix': "%",
    'filter_exclude': ["無"],
    'min_word_length': 1,
    'min_partial_word_length': 2
}

# 資料庫查詢配置
DATABASE_CONFIG = {
    'conversation_history_limit': 6,
    'max_categories_display': 10,
    'max_banks_display': 10,
    'max_rewards_per_type': 3,
    'max_cards_display': 5,
    'expected_min_cards_all_banks': 8,
    'expected_min_cards_general': 3
}

# 錯誤檢測和回應補充配置
ERROR_DETECTION_CONFIG = {
    'error_indicators': ["沒有", "找不到", "無相關", "無資料", "資料庫中沒有"],
    'all_banks_keywords': ["所有", "全部", "全部銀行", "所有銀行"],
    'highest_keywords': ["最高", "最好", "最佳", "最優", "最大", "最棒"],
    'list_query_keywords': ["有哪些", "哪些", "什麼", "什麼卡", "所有", "全部", "有", "的卡", "卡片", "信用卡"]
}

# 動態回應模板
DYNAMIC_RESPONSE_TEMPLATES = {
    'highest_reward': "{category} 回饋最高的信用卡：",
    'category_cards': "{category}的信用卡：",
    'best_reward_cards': "{category} 消費的最佳回饋卡片："
}