#!/usr/bin/env python
"""
Chatbot 全面測試檔案
測試各種用戶可能提出的問題，確保沒有 bug
"""

import os
import sys
import django

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rewardia.settings')
django.setup()

from apps.chatbot.services import ChatbotResponseBuilder
import google.generativeai as genai
from django.conf import settings

# 配置 Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

def test_chatbot_response(user_message, expected_keywords=None, should_not_contain=None, test_name=""):
    """測試 chatbot 回應"""
    print(f"\n{'='*60}")
    print(f"測試: {test_name}")
    print(f"問題: {user_message}")
    print(f"{'='*60}")
    
    try:
        # 建構上下文
        context = ChatbotResponseBuilder.build_context_prompt(user_message, None)
        
        # 組合完整提示詞
        full_prompt = f"{context}\n\n## 用戶問題\n{user_message}\n\n請根據以上資訊回答用戶的問題："
        
        # 呼叫 Gemini API
        model = genai.GenerativeModel('gemini-2.0-flash')
        gemini_response = model.generate_content(full_prompt)
        response_message = gemini_response.text
        
        # 驗證回應
        validated_response = ChatbotResponseBuilder.validate_response(
            response_message, user_message, None
        )
        
        # 增強回應
        enhanced_response = ChatbotResponseBuilder.enhance_response_with_data(
            validated_response, user_message, None
        )
        
        print(f"AI 回應:\n{enhanced_response}")
        
        # 檢查預期關鍵字
        if expected_keywords:
            missing_keywords = []
            for keyword in expected_keywords:
                if keyword not in enhanced_response:
                    missing_keywords.append(keyword)
            if missing_keywords:
                print(f"❌ 缺少預期關鍵字: {missing_keywords}")
                return False
            else:
                print(f"✅ 包含所有預期關鍵字: {expected_keywords}")
        
        # 檢查不應包含的內容
        if should_not_contain:
            found_unwanted = []
            for unwanted in should_not_contain:
                if unwanted in enhanced_response:
                    found_unwanted.append(unwanted)
            if found_unwanted:
                print(f"❌ 包含不應出現的內容: {found_unwanted}")
                return False
            else:
                print(f"✅ 沒有包含不應出現的內容")
        
        # 檢查重複內容（排除空行和常見的無害重複）
        lines = [line.strip() for line in enhanced_response.split('\n') if line.strip()]
        # 過濾掉常見的無害重複（如「暫無回饋資料」）
        harmless_duplicates = ['- 暫無回饋資料', '暫無回饋資料', '目前沒有回饋資訊']
        filtered_lines = [line for line in lines if line not in harmless_duplicates]
        
        unique_lines = set(filtered_lines)
        if len(filtered_lines) != len(unique_lines):
            print(f"❌ 發現重複內容")
            # 顯示重複的行
            from collections import Counter
            line_counts = Counter(filtered_lines)
            duplicates = {line: count for line, count in line_counts.items() if count > 1}
            print(f"重複的行: {duplicates}")
            return False
        else:
            print(f"✅ 沒有重複內容")
        
        print(f"✅ 測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False

def run_comprehensive_tests():
    """執行全面測試"""
    print("開始 Chatbot 全面測試")
    print("="*80)
    
    test_cases = [
        # 1. 基本銀行查詢測試
        {
            "question": "富邦銀行有哪些信用卡",
            "expected_keywords": ["富邦銀行", "信用卡"],
            "should_not_contain": ["重複", "##", "**"],
            "test_name": "基本銀行信用卡查詢"
        },
        
        # 2. 特定卡片回饋查詢測試
        {
            "question": "富邦銀行CUBE卡有哪些回饋",
            "expected_keywords": ["CUBE卡", "電商", "POINTS"],
            "should_not_contain": ["重複", "富邦銀行 的信用卡：", "U Bear卡", "momo卡"],
            "test_name": "特定卡片回饋查詢"
        },
        
        # 3. 比較測試
        {
            "question": "請比較富邦銀行CUBE卡與中國信託momo卡",
            "expected_keywords": ["富邦銀行", "CUBE卡", "中國信託", "momo卡"],
            "should_not_contain": ["重複", "U Bear卡", "LINE Pay卡"],
            "test_name": "兩張卡片比較"
        },
        
        # 4. 多銀行比較測試
        {
            "question": "比較富邦銀行、中國信託、台新銀行的信用卡",
            "expected_keywords": ["富邦銀行", "中國信託", "台新銀行"],
            "should_not_contain": ["重複"],
            "test_name": "多銀行比較"
        },
        
        # 5. 回饋類別查詢測試
        {
            "question": "電商回饋最高的信用卡有哪些",
            "expected_keywords": ["電商", "回饋"],
            "should_not_contain": ["重複"],
            "test_name": "回饋類別查詢"
        },
        
        # 6. 銀行列表查詢測試
        {
            "question": "可以條列式列出網站內有哪些銀行嗎",
            "expected_keywords": ["銀行"],
            "should_not_contain": ["重複", "CUBE卡", "momo卡"],
            "test_name": "銀行列表查詢"
        },
        
        # 7. 回饋率查詢測試
        {
            "question": "中國信託有消費回饋嗎",
            "expected_keywords": ["中國信託", "回饋"],
            "should_not_contain": ["重複", "##", "**"],
            "test_name": "銀行回饋查詢"
        },
        
        # 8. 特定回饋類別測試
        {
            "question": "台新銀行有關於百貨公司回饋的信用卡嗎",
            "expected_keywords": ["LINE Pay卡", "CASHBACK"],
            "should_not_contain": ["重複", "富邦銀行", "中國信託"],
            "test_name": "特定回饋類別查詢"
        },
        
        # 9. 複雜比較測試
        {
            "question": "聯邦賴點卡和永豐大戶卡有哪些回饋項目可以比較",
            "expected_keywords": ["聯邦", "賴點卡", "永豐", "大戶卡", "回饋"],
            "should_not_contain": ["重複", "富邦銀行", "中國信託"],
            "test_name": "複雜比較查詢"
        },
        
        # 10. 避免重複測試
        {
            "question": "富邦銀行CUBE卡有哪些回饋",
            "expected_keywords": ["CUBE卡", "電商", "POINTS"],
            "should_not_contain": ["重複", "富邦銀行 提供以下消費回饋", "富邦銀行 的信用卡："],
            "test_name": "避免重複回應測試"
        },
        
        # 11. 格式測試
        {
            "question": "請比較富邦銀行CUBE卡與中國信託momo卡",
            "expected_keywords": ["富邦銀行", "CUBE卡", "中國信託", "momo卡"],
            "should_not_contain": ["##", "**", "- 富邦銀行", "- 中國信託"],
            "test_name": "格式正確性測試"
        },
        
        # 12. 邊界情況測試
        {
            "question": "不存在的銀行信用卡有哪些",
            "expected_keywords": [],
            "should_not_contain": ["重複"],
            "test_name": "邊界情況測試"
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n進度: {i}/{total_tests}")
        if test_chatbot_response(
            test_case["question"],
            test_case.get("expected_keywords"),
            test_case.get("should_not_contain"),
            test_case["test_name"]
        ):
            passed_tests += 1
    
    print(f"\n{'='*80}")
    print(f"測試完成: {passed_tests}/{total_tests} 通過")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 所有測試都通過！")
    else:
        print(f"⚠️  有 {total_tests - passed_tests} 個測試失敗，需要修正")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
