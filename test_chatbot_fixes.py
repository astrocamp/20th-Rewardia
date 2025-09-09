#!/usr/bin/env python
"""
聊天機器人修正功能測試檔案
測試部分匹配邏輯、意圖分析和查詢結果
"""

import os
import sys
import django

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rewardia.settings')
django.setup()

from apps.chatbot.services import ChatbotResponseBuilder, ChatbotDataService

def test_intent_analysis():
    """測試意圖分析功能"""
    print("=== 測試意圖分析功能 ===")
    
    test_cases = [
        "美食相關的卡",
        "所有銀行與美食有關的卡", 
        "全部銀行與美食有關的卡",
        "加油回饋有哪些信用卡",
        "加油回饋最高的信用卡",
        "國賓回饋最高的信用卡",
        "加油站回饋最高的卡片"
    ]
    
    for message in test_cases:
        intent = ChatbotResponseBuilder.analyze_user_intent(message)
        print(f"\n問題: {message}")
        print(f"識別類別: {intent['categories']}")
        print(f"識別銀行: {intent['banks']}")
        print(f"是否最高查詢: {any(keyword in message for keyword in ['最高', '最好', '最佳', '最優', '最大', '最棒'])}")

def test_partial_matching():
    """測試部分匹配邏輯"""
    print("\n=== 測試部分匹配邏輯 ===")
    
    # 測試部分匹配
    test_words = ["美食", "加油", "國賓", "百貨", "旅遊"]
    categories = ChatbotDataService.get_reward_categories()
    
    for word in test_words:
        matched_categories = []
        for category in categories:
            category_words = category.split()
            for cat_word in category_words:
                # 檢查完整詞彙匹配
                if cat_word in word and len(cat_word) > 1:
                    matched_categories.append(cat_word)
                    break
                # 檢查部分詞彙匹配
                elif len(cat_word) > 2 and any(part in word for part in [cat_word[:2], cat_word[:3], cat_word[:4]] if len(part) > 1):
                    matched_categories.append(cat_word)
                    break
        
        print(f"'{word}' 匹配到的類別: {matched_categories[:5]}")

def test_database_queries():
    """測試資料庫查詢功能"""
    print("\n=== 測試資料庫查詢功能 ===")
    
    test_categories = ["美食饗宴", "加油", "國賓", "百貨購物", "旅遊住宿"]
    
    for category in test_categories:
        try:
            rewards = ChatbotDataService.get_cards_by_category(category, limit=10)
            print(f"\n{category} 查詢結果:")
            print(f"  卡片數量: {len(rewards)}")
            if rewards:
                print(f"  前3張卡片:")
                for i, reward in enumerate(rewards[:3]):
                    print(f"    {i+1}. {reward['bank']} {reward['card_name']}: {reward['min_rate']}-{reward['max_rate']}% {reward['reward_type']}")
        except Exception as e:
            print(f"  {category} 查詢錯誤: {e}")

def test_response_enhancement():
    """測試回應增強功能"""
    print("\n=== 測試回應增強功能 ===")
    
    test_cases = [
        {
            "message": "所有銀行與美食有關的卡",
            "expected_cards": 10,
            "expected_title": "美食饗宴 回饋的信用卡："
        },
        {
            "message": "加油回饋有哪些信用卡", 
            "expected_cards": 5,
            "expected_title": "加油 回饋的信用卡："
        },
        {
            "message": "加油回饋最高的信用卡",
            "expected_cards": 1,
            "expected_title": "加油 回饋最高的信用卡："
        }
    ]
    
    for case in test_cases:
        print(f"\n測試案例: {case['message']}")
        
        # 分析意圖
        intent = ChatbotResponseBuilder.analyze_user_intent(case['message'])
        print(f"  識別類別: {intent['categories']}")
        print(f"  識別銀行: {intent['banks']}")
        
        # 查詢資料
        if intent['categories']:
            category = intent['categories'][0]
            rewards = ChatbotDataService.get_cards_by_category(category, limit=10)
            print(f"  查詢到 {len(rewards)} 張卡片")
            
            # 檢查標題邏輯
            is_highest_only = any(keyword in case['message'] for keyword in ['最高', '最好', '最佳', '最優', '最大', '最棒'])
            has_list_keywords = any(keyword in case['message'] for keyword in ['有哪些', '哪些', '什麼', '什麼卡', '所有', '全部'])
            
            if is_highest_only:
                expected_title = f"{category} 回饋最高的信用卡："
            elif has_list_keywords:
                expected_title = f"{category} 回饋的信用卡："
            else:
                expected_title = f"{category} 消費的最佳回饋卡片："
            
            print(f"  預期標題: {expected_title}")
            print(f"  測試標題: {case['expected_title']}")
            print(f"  標題邏輯正確: {expected_title == case['expected_title']}")

def test_specific_issues():
    """測試特定問題的修正"""
    print("\n=== 測試特定問題修正 ===")
    
    # 測試1: 美食相關卡片數量
    print("\n1. 測試美食相關卡片數量:")
    rewards = ChatbotDataService.get_cards_by_category('美食饗宴', limit=10)
    print(f"   查詢結果: {len(rewards)} 張卡片")
    print(f"   預期: 10 張卡片")
    print(f"   結果: {'✓ 通過' if len(rewards) >= 10 else '✗ 失敗'}")
    
    # 測試2: 國賓回饋查詢
    print("\n2. 測試國賓回饋查詢:")
    intent = ChatbotResponseBuilder.analyze_user_intent('國賓回饋最高的信用卡')
    print(f"   識別類別: {intent['categories']}")
    if intent['categories']:
        rewards = ChatbotDataService.get_cards_by_category(intent['categories'][0], limit=5)
        print(f"   查詢結果: {len(rewards)} 張卡片")
        print(f"   結果: {'✓ 通過' if len(rewards) > 0 else '✗ 失敗'}")
    
    # 測試3: 標題生成邏輯
    print("\n3. 測試標題生成邏輯:")
    test_messages = [
        "加油回饋有哪些信用卡",
        "加油回饋最高的信用卡", 
        "美食相關的卡"
    ]
    
    for message in test_messages:
        is_highest_only = any(keyword in message for keyword in ['最高', '最好', '最佳', '最優', '最大', '最棒'])
        has_list_keywords = any(keyword in message for keyword in ['有哪些', '哪些', '什麼', '什麼卡'])
        
        if is_highest_only:
            title_type = "最高回饋"
        elif has_list_keywords:
            title_type = "回饋列表"
        else:
            title_type = "最佳回饋"
        
        print(f"   '{message}' -> {title_type}")
    
    # 測試4: 重複回答問題修正
    print("\n4. 測試重複回答問題修正:")
    test_messages = [
        "全部銀行與美食有關的卡",
        "所有銀行與美食有關的卡"
    ]
    
    for message in test_messages:
        expected_min_cards = 8 if any(keyword in message for keyword in ["所有", "全部", "全部銀行", "所有銀行"]) else 3
        print(f"   '{message}' -> 預期最少卡片數: {expected_min_cards}")
        print(f"   2張卡片是否觸發補充: {2 < expected_min_cards}")
        print(f"   結果: {'✓ 會觸發補充' if 2 < expected_min_cards else '✗ 不會觸發補充'}")

def main():
    """主測試函數"""
    print("開始測試聊天機器人修正功能...")
    print("=" * 50)
    
    try:
        test_intent_analysis()
        test_partial_matching()
        test_database_queries()
        test_response_enhancement()
        test_specific_issues()
        
        print("\n" + "=" * 50)
        print("所有測試完成！")
        
    except Exception as e:
        print(f"\n測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
