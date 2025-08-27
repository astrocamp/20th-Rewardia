#!/usr/bin/env python
"""
Dora 老師的測試資料創建腳本
在專案根目錄執行：python seed_data.py
"""

import os
import sys
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rewardia.settings')
django.setup()

from apps.banks.models import Bank
from apps.cards.models import CreditCard

def create_banks():
    """創建測試銀行資料"""
    print("🏦 開始建立銀行資料...")
    
    banks_data = [
        {'name': '台新銀行', 'code': 'TSB', 'website_url': 'https://www.taishinbank.com.tw'},
        {'name': '國泰世華', 'code': 'CTBC', 'website_url': 'https://www.cathaybk.com.tw'},
        {'name': '玉山銀行', 'code': 'ESB', 'website_url': 'https://www.esunbank.com.tw'},
        {'name': '中國信託', 'code': 'CTCI', 'website_url': 'https://www.ctbcbank.com'},
        {'name': '富邦銀行', 'code': 'FB', 'website_url': 'https://www.fubon.com'},
        {'name': '第一銀行', 'code': 'FB1', 'website_url': 'https://www.firstbank.com.tw'},
        {'name': '永豐銀行', 'code': 'SINOPAC', 'website_url': 'https://www.sinopac.com'},
    ]
    
    for bank_info in banks_data:
        bank, created = Bank.objects.get_or_create(
            code=bank_info['code'],
            defaults={
                'name': bank_info['name'],
                'website_url': bank_info['website_url'],
                'is_active': True
            }
        )
        if created:
            print(f"  ✅ 創建銀行: {bank.name}")
        else:
            print(f"  📋 銀行已存在: {bank.name}")

def create_cards():
    """創建測試信用卡資料"""
    print("\n💳 開始建立信用卡資料...")
    
    # 先確保銀行存在
    try:
        taishin = Bank.objects.get(code='TSB')
        cathay = Bank.objects.get(code='CTBC') 
        esun = Bank.objects.get(code='ESB')
        ctci = Bank.objects.get(code='CTCI')
        fubon = Bank.objects.get(code='FB')
        first = Bank.objects.get(code='FB1')
        sinopac = Bank.objects.get(code='SINOPAC')
    except Bank.DoesNotExist:
        print("  ❌ 請先創建銀行資料！")
        return
    
    cards_data = [
        # 台新銀行
        {'name': '現金回饋卡', 'bank': taishin, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
        {'name': 'Flygo卡', 'bank': taishin, 'annual_fee': 2400, 'card_network': 'VISA', 'card_type': 'GOLD'},
        {'name': '@GoGo卡', 'bank': taishin, 'annual_fee': 0, 'card_network': 'MC', 'card_type': 'CLASSIC'},
        
        # 國泰世華
        {'name': '御璽卡', 'bank': cathay, 'annual_fee': 2400, 'card_network': 'MC', 'card_type': 'SIGNATURE'},
        {'name': 'momo卡', 'bank': cathay, 'annual_fee': 0, 'card_network': 'MC', 'card_type': 'CLASSIC'},
        {'name': 'CUBE卡', 'bank': cathay, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
        
        # 玉山銀行
        {'name': 'U Bear卡', 'bank': esun, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
        {'name': '玉山Only卡', 'bank': esun, 'annual_fee': 160, 'card_network': 'MC', 'card_type': 'CLASSIC'},
        {'name': 'Pi拍錢包卡', 'bank': esun, 'annual_fee': 0, 'card_network': 'MC', 'card_type': 'CLASSIC'},
        
        # 中國信託
        {'name': 'LINE Pay卡', 'bank': ctci, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
        {'name': '英雄聯盟卡', 'bank': ctci, 'annual_fee': 0, 'card_network': 'MC', 'card_type': 'CLASSIC'},
        {'name': 'ANA極緻卡', 'bank': ctci, 'annual_fee': 8000, 'card_network': 'VISA', 'card_type': 'INFINITE'},
        
        # 富邦銀行
        {'name': 'momo購物卡', 'bank': fubon, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
        {'name': 'J卡', 'bank': fubon, 'annual_fee': 900, 'card_network': 'JCB', 'card_type': 'GOLD'},
        {'name': '產險聯名卡', 'bank': fubon, 'annual_fee': 0, 'card_network': 'MC', 'card_type': 'CLASSIC'},
        
        # 第一銀行
        {'name': 'iLeo卡', 'bank': first, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
        {'name': '綠活卡', 'bank': first, 'annual_fee': 0, 'card_network': 'MC', 'card_type': 'CLASSIC'},
        
        # 永豐銀行
        {'name': '大戶卡', 'bank': sinopac, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
        {'name': 'Sport卡', 'bank': sinopac, 'annual_fee': 0, 'card_network': 'VISA', 'card_type': 'CLASSIC'},
    ]
    
    for card_info in cards_data:
        card, created = CreditCard.objects.get_or_create(
            name=card_info['name'],
            bank=card_info['bank'],
            defaults={
                'annual_fee': card_info['annual_fee'],
                'signup_bonus': 0,
                'apr_min': 5.88,
                'apr_max': 15.00,
                'foreign_transaction_fee': 1.50,
                'card_network': card_info['card_network'],
                'card_type': card_info['card_type'],
                'is_active': True,
            }
        )
        if created:
            print(f"  ✅ 創建卡片: {card.bank.name} {card.name}")
        else:
            print(f"  📋 卡片已存在: {card.bank.name} {card.name}")

def main():
    """主函數"""
    print("🎒 Dora 老師的測試資料創建腳本開始執行！")
    print("=" * 50)
    
    create_banks()
    create_cards()
    
    print("\n" + "=" * 50)
    print("🎉 完成！現在你有豐富的測試資料可以玩了！")
    print("📊 統計資料：")
    print(f"   銀行總數：{Bank.objects.filter(is_active=True).count()} 家")
    print(f"   信用卡總數：{CreditCard.objects.filter(is_active=True).count()} 張")
    print("🔗 現在可以跑 runserver 並測試新增卡片功能！")

if __name__ == '__main__':
    main()
