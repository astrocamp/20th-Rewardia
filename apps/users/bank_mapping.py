"""
銀行名稱中英文對照配置
根據附件提供的中英文對照表建立映射關係
"""


def luhn_check(card_number: str) -> bool:
    """
    使用 Luhn 演算法驗證信用卡號的有效性
    
    Args:
        card_number: 信用卡號（純數字字串）
        
    Returns:
        是否為有效的信用卡號
    """
    if not card_number or not card_number.isdigit():
        return False
    
    # 移除所有非數字字符
    clean_number = ''.join(filter(str.isdigit, card_number))
    
    # 信用卡號長度檢查（通常為 13-19 位）
    if len(clean_number) < 13 or len(clean_number) > 19:
        return False
    
    # Luhn 演算法
    def luhn_checksum(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10
    
    return luhn_checksum(clean_number) == 0

# 英文銀行名稱 -> 中文銀行名稱對照表
BANK_NAME_MAPPING = {
    # 從附件中英文對照表提取
    'CITIBANK, N.A.': '花旗',
    'Cathay United Bank': '國泰',
    'Bank Sinopac': '永豐',
    'Jih Sun International Bank': '日盛',
    'Bank of Kaohsiung': '高雄',
    'Kings Town Bank': '京城',
    'Land Bank of Taiwan': '土地',
    'Mega International Commercial Bank': '兆豐',
    'Taipei Fubon Commercial Bank': '富邦',
    'Taishin International Bank': '台新',
    'Taiwan Business Bank': '台灣企銀',
    'Taiwan Cooperative Bank': '合庫',
    'Taiwan Rakuten Card Inc.': '樂天',
    'Taiwan Shin Kong Commercial Bank': '新光',
    'Union Bank of Taiwan': '聯邦',
    'Yuanta Commercial Bank': '元大',
    'Standard Chartered Bank (Taiwan), Ltd.': '渣打',
    'Sunny Bank': '陽信',
    'Ta Chong Bank, Ltd.': '大眾',
    'Taichung Commercial Bank': '台中',
    'Tainan Business Bank': '台南',
    'First Commercial Bank': '第一',
    'Fuhwa Commercial Bank': '富華',
    'HSBC Bank (Taiwan), Ltd.': '滙豐',
    'Chang Hwa Commercial Bank, Ltd.': '彰化',
    'Chinatrust Commercial Bank': '中國信託',
    'DBS Bank (Taiwan), Ltd.': '東亞',
    'E.Sun Commercial Bank': '玉山',
    'E SUN COMMERCIAL BANK': '玉山', 
    
    # 可能的其他變體名稱
    'CITIBANK TAIWAN LTD': '花旗',
    'CITIBANK N.A.': '花旗',  
    'CATHAY UNITED BANK': '國泰',
    'BANK SINOPAC': '永豐',
    'TAIPEI FUBON BANK': '富邦',
    'TAISHIN BANK': '台新',
    'CHINATRUST BANK': '中國信託',
    'ESUN BANK': '玉山',
    'E.SUN BANK': '玉山',
    'UNION BANK OF TAIWAN': '聯邦',
    'SHANGHAI COMMERCIAL AND SAVINGS BANK, LTD.': '上海商銀',
    'SHANGHAI COMMERCIAL BANK': '上海商銀',  # 可能的簡稱
    'KGI Bank': '凱基',
    'KGI Bank Co., Ltd.': '凱基',
    'DBS Bank (Taiwan) Ltd.': '星展',
    'DBS Bank Ltd.': '星展',
    'O-Bank': '王道',
    'O-Bank Co., Ltd.': '王道',
    'Far Eastern International Bank': '遠東',
    'Far Eastern International Bank Co., Ltd.': '遠東',
}


def get_chinese_bank_name(english_name: str) -> str:
    """
    根據英文銀行名稱取得對應的中文名稱
    
    Args:
        english_name: 英文銀行名稱
        
    Returns:
        中文銀行名稱，如果找不到對照則返回原英文名稱
    """
    if not english_name:
        return ""
    
    # 直接查找
    if english_name in BANK_NAME_MAPPING:
        return BANK_NAME_MAPPING[english_name]
    
    # 嘗試不區分大小寫的查找
    english_name_upper = english_name.upper()
    for eng_key, chn_value in BANK_NAME_MAPPING.items():
        if eng_key.upper() == english_name_upper:
            return chn_value
    
    # 嘗試部分匹配（處理可能的變體）- 使用更精確的匹配策略
    for eng_key, chn_value in BANK_NAME_MAPPING.items():
        eng_key_upper = eng_key.upper()
        # 只允許輸入名稱是鍵名的一部分，且長度至少為 3 個字符
        if ((english_name_upper in eng_key_upper and len(english_name_upper) >= 3) or
            (eng_key_upper in english_name_upper and len(eng_key_upper) >= 3)):
            return chn_value
    
    # 找不到對照，返回原英文名稱
    return english_name



def is_bank_name_mapped(english_name: str) -> bool:
    """
    檢查英文銀行名稱是否有對應的中文名稱
    
    Args:
        english_name: 英文銀行名稱
        
    Returns:
        是否有對應的中文名稱
    """
    if not english_name:
        return False
    
    # 直接查找
    if english_name in BANK_NAME_MAPPING:
        return True
    
    # 嘗試不區分大小寫的查找
    english_name_upper = english_name.upper()
    for eng_key in BANK_NAME_MAPPING.keys():
        if eng_key.upper() == english_name_upper:
            return True
    
    # 嘗試部分匹配（處理可能的變體）
    for eng_key in BANK_NAME_MAPPING.keys():
        if english_name_upper in eng_key.upper() or eng_key.upper() in english_name_upper:
            return True
    
    return False


def get_all_mapped_banks() -> dict:
    """
    取得所有已對照的銀行名稱
    
    Returns:
        英文到中文的映射字典
    """
    return BANK_NAME_MAPPING.copy()
