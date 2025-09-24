"""
銀行名稱中英文對照配置
根據附件提供的中英文對照表建立映射關係
"""

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
    'E SUN COMMERCIAL BANK': '玉山',  # API 返回的全大寫格式
    
    # 可能的其他變體名稱
    'CITIBANK TAIWAN LTD': '花旗',
    'CITIBANK N.A.': '美國',  # API 返回的格式
    'CATHAY UNITED BANK': '國泰',
    'BANK SINOPAC': '永豐',
    'TAIPEI FUBON BANK': '富邦',
    'TAISHIN BANK': '台新',
    'CHINATRUST BANK': '中國信託',
    'ESUN BANK': '玉山',
    'E.SUN BANK': '玉山',
    'UNION BANK OF TAIWAN': '聯邦',  # API 返回的全大寫格式，對應資料庫中的名稱
}

# 反向映射：中文 -> 英文（用於驗證）
CHINESE_TO_ENGLISH_MAPPING = {v: k for k, v in BANK_NAME_MAPPING.items()}


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
    
    # 嘗試部分匹配（處理可能的變體）
    for eng_key, chn_value in BANK_NAME_MAPPING.items():
        if english_name_upper in eng_key.upper() or eng_key.upper() in english_name_upper:
            return chn_value
    
    # 找不到對照，返回原英文名稱
    return english_name


def get_english_bank_name(chinese_name: str) -> str:
    """
    根據中文銀行名稱取得對應的英文名稱
    
    Args:
        chinese_name: 中文銀行名稱
        
    Returns:
        英文銀行名稱，如果找不到對照則返回原中文名稱
    """
    if not chinese_name:
        return ""
    
    # 直接查找
    if chinese_name in CHINESE_TO_ENGLISH_MAPPING:
        return CHINESE_TO_ENGLISH_MAPPING[chinese_name]
    
    # 找不到對照，返回原中文名稱
    return chinese_name


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
