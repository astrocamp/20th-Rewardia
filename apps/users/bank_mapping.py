"""
銀行名稱中英文對照配置
根據附件提供的中英文對照表建立映射關係
"""

# 英文銀行名稱 -> 中文銀行名稱對照表
BANK_NAME_MAPPING = {
    # 從附件中英文對照表提取
    'CITIBANK, N.A.': '花旗銀行台灣',
    'Cathay United Bank': '國泰世華銀行',
    'Bank Sinopac': '永豐銀行',
    'Jih Sun International Bank': '日盛銀行',
    'Bank of Kaohsiung': '高雄銀行',
    'Kings Town Bank': '京城銀行',
    'Land Bank of Taiwan': '土地銀行',
    'Mega International Commercial Bank': '兆豐國際商業銀行',
    'Taipei Fubon Commercial Bank': '台北富邦銀行',
    'Taishin International Bank': '台新銀行',
    'Taiwan Business Bank': '台灣企銀',
    'Taiwan Cooperative Bank': '合作金庫銀行',
    'Taiwan Rakuten Card Inc.': '樂天信用卡',
    'Taiwan Shin Kong Commercial Bank': '新光銀行',
    'Union Bank of Taiwan': '聯邦銀行',
    'Yuanta Commercial Bank': '元大銀行',
    'Standard Chartered Bank (Taiwan), Ltd.': '渣打銀行',
    'Sunny Bank': '陽信銀行',
    'Ta Chong Bank, Ltd.': '大眾銀行',
    'Taichung Commercial Bank': '台中商業銀行',
    'Tainan Business Bank': '台南銀行',
    'First Commercial Bank': '第一銀行',
    'Fuhwa Commercial Bank': '富華銀行',
    'HSBC Bank (Taiwan), Ltd.': '滙豐銀行',
    'Chang Hwa Commercial Bank, Ltd.': '彰化銀行',
    'Chinatrust Commercial Bank': '中國信託銀行',
    'DBS Bank (Taiwan), Ltd.': '東亞銀行',
    'E.Sun Commercial Bank': '玉山銀行',
    
    # 可能的其他變體名稱
    'CITIBANK TAIWAN LTD': '花旗銀行台灣',
    'CITIBANK N.A.': '花旗銀行台灣',  # API 返回的格式
    'CATHAY UNITED BANK': '國泰世華銀行',
    'BANK SINOPAC': '永豐銀行',
    'TAIPEI FUBON BANK': '台北富邦銀行',
    'TAISHIN BANK': '台新銀行',
    'CHINATRUST BANK': '中國信託銀行',
    'ESUN BANK': '玉山銀行',
    'E.SUN BANK': '玉山銀行',
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
    return english_name in BANK_NAME_MAPPING


def get_all_mapped_banks() -> dict:
    """
    取得所有已對照的銀行名稱
    
    Returns:
        英文到中文的映射字典
    """
    return BANK_NAME_MAPPING.copy()
