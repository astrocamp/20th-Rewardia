# apps/nlp_validation/test_basic.py
import spacy
import re

def test_spacy_installation():
    """測試 spaCy 是否正確安裝"""
    try:
        nlp = spacy.load("zh_core_web_md")
        print(" spaCy 中文模型載入成功")
        return True
    except OSError:
        print(" spaCy 中文模型未安裝")
        return False

def test_basic_text_analysis():
    """測試基本文字分析功能"""
    nlp = spacy.load("zh_core_web_md")
    
    # 用你的滙豐銀行文字測試
    test_text = """
    Money101 Credit Cards - Clean Content
Money101 Credit Cards - Extracted Content
Source:
https://www.money101.com.tw/信用卡/產品/滙豐銀行匯鑽卡
Note:
Navigation, filters, footer, images, forms, inputs, and promotional offers have been removed.
CC
product page
滙豐銀行 匯鑽卡
滙豐銀行HSBC推出的匯鑽卡一般消費 1%回饋無上限，行動支付/網購外送/線上訂房/影音遊戲 3%回饋 (包含街口、momo、Amazon、Farfetch、UberEats、Netflix等，每期上限$2,000)，綁定One 能戶或卓越理財帳戶並存款達30萬元，回饋加倍，最高 6% 回饋，現在透過Money101申請還可享通路限定首刷禮優惠喔！
年費折抵
首年免年費
info
保險消費現金回饋
1
%
行動支付現金回饋
6
%
國內消費現金回饋
6
%
info
chevron_left
焦點關注
優惠
產品特色
申辦條件
費用/還款
其他
chevron_right
layers
焦點關注
年費折抵
首年免年費
info
保險消費現金回饋
1
%
行動支付現金回饋
6
%
國內消費現金回饋
6
%
info
6
個適用優惠/活動
關於這張卡片
關於這張卡片
check
串流影音
check
美食外送回饋
check
線上購物回饋
check
訂房網回饋
sentiment_satisfied
優惠
現金回饋
credit_card
基本現金回饋
1
%
info
location_on
國內消費現金回饋
6
%
info
flight
國外消費現金回饋
6
%
info
local_gas_station
加油消費現金回饋
6
%
info
shopping_bag
國內線上消費現金回饋
6
%
shopping_bag
海外線上消費現金回饋
6
%
shield
保險消費現金回饋
1
%
price_change
線上消費現金回饋
6
%
contactless
行動支付現金回饋
6
    """
    
    doc = nlp(test_text)
    
    print("\n 實體識別結果：")
    for ent in doc.ents:
        print(f"  {ent.text} -> {ent.label_}")
    
    print("\n 找到的數字：")
    numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%', test_text)
    print(f"  回饋率: {numbers}")
    
    fees = re.findall(r'NT\$\s*(\d+(?:,\d+)?)', test_text)
    print(f"  費用: {fees}")

if __name__ == "__main__":
    print(" 開始 Day 1 基本功能測試\n")
    
    if test_spacy_installation():
        test_basic_text_analysis()
    
    print("\n Day 1 測試完成！")