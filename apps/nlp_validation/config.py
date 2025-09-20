class NLPConfig:
    @staticmethod
    def get_category_scope_seeds():
        """消費類別和範圍的語義種子詞"""
        return {
            "一般消費": {
                "國內": ["國內", "境內", "台灣", "本土", "台灣境內", "台幣"],
                "海外": [
                    "海外",
                    "國外",
                    "境外",
                    "國際",
                    "外幣",
                    "外國",
                    "日幣",
                    "韓元",
                    "美金",
                    "歐元",
                    "日本",
                    "韓國",
                    "泰國",
                    "當地",
                    "實體",
                ],
            },
            "旅遊": {
                "航空公司": [
                    "航空",
                    "華航",
                    "長榮",
                    "星宇",
                    "虎航",
                    "國泰航空",
                    "立榮",
                    "華信",
                    "機票",
                ],
                "KKday": ["KKday", "kkday", "KKDay"],
                "Klook": ["Klook", "klook"],
                "旅行社": [
                    "旅行社",
                    "旅遊",
                    "雄獅",
                    "可樂",
                    "東南",
                    "五福",
                    "易遊網",
                    "ezfly易飛網",
                    "山富",
                    "鳳凰",
                    "百威",
                    "大興",
                    "長汎",
                    "康迅",
                ],
                "訂房網站": [
                    "訂房",
                    "住宿",
                    "agoda",
                    "booking.com",
                    "hotels.com",
                    "expedia",
                    "trip.com",
                    "asiayo",
                    "airbnb",
                ],
                "機場服務": ["機場", "貴賓室", "機場接送", "龍騰出行"],
            },
            "旅遊/航空": {
                "機票、旅行社": [
                    "機票",
                    "旅行社",
                    "旅遊",
                    "klook",
                    "kkday",
                    "雄獅",
                    "可樂",
                    "東南",
                    "五福",
                    "易遊網",
                    "ezfly易飛網",
                    "山富",
                    "鳳凰",
                    "百威",
                    "大興",
                    "長汎",
                    "康迅",
                ],
                "機票、機場接送、貴賓室": ["機場", "貴賓室", "接送", "龍騰出行"],
            },
            "網購": {
                "Coupang": ["coupang", "酷澎"],
                "蝦皮購物": ["蝦皮", "shopee", "蝦皮購物"],
                "momo購物": ["momo", "富邦momo", "momo購物", "momo網", "momo購物網"],
                "pchome": [
                    "pchome",
                    "pc home",
                    "pc商店街",
                    "pchome24h",
                    "PChome",
                    "PCHome",
                    "PChome 24h購物",
                    "PChome 24h",
                ],
                "其他平台": [
                    "網購",
                    "電商",
                    "線上購物",
                    "網路消費",
                    "平台",
                    "yahoo",
                    "奇摩",
                    "yahoo購物",
                    "淘寶",
                    "天貓",
                    "amazon",
                ],
            },
            "交通/加油": {
                "行動支付": [
                    "悠遊卡自動加值",
                    "ipass money",
                    "icash pay",
                    "悠遊付",
                    "line pay",
                    "linepay",
                ],
                "大眾運輸": ["高鐵", "台鐵", "捷運", "公車", "客運"],
                "Uber": ["Uber", "uber", "UBER"],
                "計程車/租車": [
                    "計程車",
                    "yoxi",
                    "台灣大車隊",
                    "irent",
                    "goshare",
                    "wemo",
                    "租車",
                ],
                "加油": ["加油", "中油", "台塑", "全國", "台亞"],
            },
            "餐飲美食": {
                "國內餐廳": ["餐廳", "餐飲", "美食", "用餐"],
                "咖啡廳": ["路易莎", "cama"],
                "星巴克": ["星巴克", "星巴克咖啡", "starbucks", "Starbucks"],
                "速食": [
                    "麥當勞",
                    "mcdonald's",
                    "肯德基",
                    "kfc",
                    "摩斯漢堡",
                    "mos burger",
                    "漢堡王",
                    "burger king",
                ],
            },
            "百貨/量販/超商": {
                "誠品": ["誠品"],
                "新光三越": ["新光三越"],
                "SOGO": ["sogo", "sogo百貨", "遠東sogo"],
                "百貨公司": ["百貨", "遠東百貨", "微風", "101"],
                "量販超市": [
                    "全聯",
                    "家樂福",
                    "carrefour",
                    "大潤發",
                    "rt-mart",
                    "愛買",
                    "美廉社",
                    "頂好",
                    "jasons market place",
                    "costco",
                    "好市多",
                ],
                "7-11": ["7-11", "711", "7-ELEVEN"],
                "全家": ["全家", "全家便利商店", "FamilyMart", "familymart"],
                "便利超商": [
                    "小七",
                    "統一超商",
                    "萊爾富",
                    "okmart",
                    "ok超商",
                ],
                "康是美": ["康是美", "cosmed"],
                "寶雅": ["寶雅", "poya"],
                "屈臣氏": ["屈臣氏", "watsons"],
                "藥妝美妝": [
                    "松本清",
                    "マツモトキヨシ",
                    "大國藥妝",
                    "ダイコクドラッグ",
                    "olive young",
                    "日藥本舖",
                ],
            },
            "生活娛樂": {
                "Netflix": ["netflix", "網飛"],
                "Spotify": ["spotify"],
                "影音串流": [
                    "disney+",
                    "youtube premium",
                    "kkbox",
                ],
                "電影院": ["影城", "電影"],
                "電信費": ["電信費", "中華電信", "台灣大哥大", "遠傳"],
                "保險": ["保費", "保險"],
                "遊樂園": [
                    "迪士尼",
                    "disneyland",
                    "環球影城",
                    "universal studios",
                    "樂天世界",
                    "lotte world",
                    "愛寶樂園",
                    "everland",
                    "六福村",
                    "九族文化村",
                    "劍湖山",
                ],
            },
            "餐飲/外送": {
                "foodpanda": ["foodpanda", "熊貓", "panda", "胖達", "胖達幣"],
                "Uber Eats": ["uber eats", "ubereats"],
                "其他外送": ["外送", "送餐", "美食外送"],
            },
            "指定通路": {
                "依活動檔期": ["指定", "活動", "檔期", "特定通路", "專屬", "精選"]
            },
        }

    @staticmethod
    def get_reward_keywords():
        """回饋指標關鍵詞"""
        return [
            "回饋",
            "％",
            "%",
            "最高",
            "無上限",
            "享",
        ]

    @staticmethod
    def get_reward_patterns():
        """用於從文本中提取百分比數字"""
        return [
            r"(?:享|最高|可享|獲得|回饋|達).*?(\d+\.?\d*)[%％]",
            r"(\d+\.?\d*)[%％].*?(?:回饋|優惠|折扣|刷卡金|點數)",
            r"(\d+\.?\d*)[%％]",
            r"(\d+\.?\d*)趴",
            r"百分之(\d+\.?\d*)",
            r"加碼.*?(\d+\.?\d*)[%％]",
        ]

    @staticmethod
    def get_exclude_keywords():
        """排除不是回饋資訊的關鍵詞"""
        return [
            "循環利率",
            "年利率",
            "手續費",
            "年費",
            "費用",
            "分期",
            "利息",
            "罰息",
            "滯納金",
            "預借現金",
            "申辦條件",
            "謹慎理財",
            "上限為",
            "利率上限",
            "基準利率",
            "加碼利率",
            "~",
            "～",
            "預借",
            "活儲",
        ]

    @staticmethod
    def get_reward_type_keywords():
        """用於識別回饋的種類"""
        return {
            "cashback": ["現金回饋", "刷卡金", "現金"],
            "points": [
                "點",
                "p幣",
                "P 幣",
                "蝦幣",
                "胖達幣",
                "豐點",
                "好多金",
                "點數",
                "happy go",
                "openpoint",
            ],
        }

    @staticmethod
    def get_physical_store_keywords():
        """實體商店過濾關鍵詞（因為只要線上回饋）"""
        return [
            "實體商店",
            "實體餐廳",
            "店內消費",
            "門市",
            "櫃檯",
            "現場",
            "臨櫃",
            "實體通路",
            "店面消費",
            "店內",
            "實體",
            "門店",
            "櫃位",
            "現場刷卡",
        ]

    @staticmethod
    def get_auto_expand_patterns():
        """用於自動將特定詞彙歸類到對應類別"""
        return {
            "海外": {
                "keywords": [
                    "日本",
                    "韓國",
                    "泰國",
                    "美國",
                    "歐洲",
                    "亞洲",
                    "新加坡",
                    "馬來西亞",
                    "菲律賓",
                    "日",
                    "韓",
                    "泰",
                    "美",
                    "歐",
                ],
                "category": "一般消費",
                "scope": "海外",
            },
            "線上": {
                "keywords": ["網站", "APP", "線上", "數位", "虛擬", "網路", "官網"],
                "category": "網購",
                "scope": "其他平台",
            },
            "交通": {
                "keywords": [
                    "高鐵",
                    "台鐵",
                    "捷運",
                    "公車",
                    "計程車",
                    "租車",
                    "yoxi",
                    "uber",
                    "irent",
                    "goshare",
                    "wemo",
                    "台灣大車隊",
                ],
                "category": "交通/加油",
                "scope": "大眾運輸",
            },
            "行動支付": {
                "keywords": [
                    "line pay",
                    "linepay",
                    "街口",
                    "街口支付",
                    "apple pay",
                    "google pay",
                    "samsung pay",
                    "icash pay",
                    "悠遊付",
                    "全盈",
                    "全盈支付",
                    "全盈+pay",
                    "pxpay",
                    "全聯pay",
                ],
                "category": "交通/加油",
                "scope": "行動支付",
            },
        }

    @staticmethod
    def get_domain_synonyms():
        """用於spaCy語義擴展"""
        return {
            "網購": ["網路購物", "線上購物", "電商", "網拍", "網路商城"],
            "外送": ["送餐", "外賣", "餐點外送", "美食外送"],
            "旅遊": ["旅行", "觀光", "度假", "遊玩"],
            "機票": ["航班", "班機", "飛機票", "機位"],
            "餐廳": ["餐館", "飯店", "食肆", "用餐"],
            "百貨": ["購物中心", "商場", "百貨公司", "商城"],
            "超市": ["超商", "賣場", "市場"],
            "加油": ["油站", "加油站", "汽油"],
            "電影": ["電影院", "戲院", "影廳"],
            "咖啡": ["咖啡廳", "咖啡店", "cafe"],
            "海外": ["國外", "境外", "國際", "外國"],
            "國內": ["境內", "台灣", "本土", "本國"],
        }

    @staticmethod
    def get_punctuation_map():
        """半形轉全形"""
        return {",": "，", ":": "：", ";": "；", "!": "！", "?": "？"}

    @staticmethod
    def get_keyword_variations():
        """關鍵詞自動變形規則"""
        return [
            lambda keyword: keyword + "購物",
            lambda keyword: keyword + "消費",
            lambda keyword: keyword + "刷卡",
            lambda keyword: "線上" + keyword if "網" in keyword else None,
            lambda keyword: keyword.replace("網", "線上") if "網" in keyword else None,
        ]

    @staticmethod
    def get_unnecessary_symbols_regex():
        """移除不必要符號"""
        return r"[/\\【】「」《》〈〉『』|]"

    @staticmethod
    def get_sentence_endings():
        return ["。", "！", "？", "；"]

    @staticmethod
    def get_bank_pattern():
        """銀行名稱"""
        return r"(滙豐|中國信託|國泰|玉山|台新|富邦|第一|一銀|合庫|兆豐|永豐|遠東|凱基|聯邦|星展|樂天|彰化|華南|新光|上海商銀|美國|渣打|陽信|Bank|將來|元大|台中|王道)"

    @staticmethod
    def get_settings():
        """處理器設定參數"""
        return {
            "similarity_threshold": 0.6,
            "min_sentence_length": 8,
            "smart_keyword_expansion": True,
            "expansion_similarity_threshold": 0.7,
            "deduplication_threshold": 0.7,
            "rate_range": {"min": 0.1, "max": 50.0},
            "confidence_scores": {
                "direct_match": 1.0,
                "auto_expand": 0.8,
                "default_classification": 0.3,
            },
            "test_parameters": {
                "min_test_cards": 100,
                "max_test_cards": 103,
                "json_file_path": "apps/nlp_validation/crawler_data_202508281713.json",
                "fallback_test_data": [
                    "泰 KOKO (COMBO)悠遊聯名卡（停發）,國泰 KOKO (COMBO)悠遊聯名卡（停發）評價好嗎？真實回饋攻略讓達人告訴你,5 大權益天天切換，指定消費 3% 起，回饋無上限"
                ],
            },
        }

    @classmethod
    def load_config(cls):
        """載入完整配置"""
        return {
            "category_scope_seeds": cls.get_category_scope_seeds(),
            "reward_keywords": {"_keywords": cls.get_reward_keywords()},
            "reward_patterns": {"_patterns": cls.get_reward_patterns()},
            "exclude_keywords": {"_keywords": cls.get_exclude_keywords()},
            "reward_type_keywords": cls.get_reward_type_keywords(),
            "physical_store_keywords": {"_keywords": cls.get_physical_store_keywords()},
            "auto_expand_patterns": cls.get_auto_expand_patterns(),
            "domain_synonyms": cls.get_domain_synonyms(),
            "keyword_variations": cls.get_keyword_variations(),
            "punctuation_map": cls.get_punctuation_map(),
            "unnecessary_symbols_regex": cls.get_unnecessary_symbols_regex(),
            "sentence_endings": cls.get_sentence_endings(),
            "bank_pattern": cls.get_bank_pattern(),
            "settings": cls.get_settings(),
        }
