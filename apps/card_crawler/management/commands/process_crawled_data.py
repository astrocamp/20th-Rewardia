from django.core.management.base import BaseCommand
from apps.card_crawler.models import CrawledData
from apps.cards.models import CreditCard
from apps.rewards.models import RewardCategory
import re
import json


class Command(BaseCommand):
    help = "處理爬取的信用卡資料，轉換成 CreditCard 和 RewardCategory 記錄"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='處理的資料筆數限制'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(f"開始處理爬取的信用卡資料，限制 {limit} 筆...")
        
        # 取得爬取的資料
        crawled_data = CrawledData.objects.filter(is_active=True)[:limit]
        
        processed_count = 0
        created_cards = 0
        created_rewards = 0
        
        for data in crawled_data:
            try:
                # 解析內容
                content = data.content.split(',')
                if not content:
                    continue
                
                # 提取銀行和卡片名稱
                first_line = content[0].strip()
                bank_name, card_name = self.extract_bank_and_card(first_line)
                
                if not bank_name or not card_name:
                    self.stdout.write(f"無法提取銀行或卡片名稱: {first_line}")
                    continue
                
                # 建立或取得信用卡記錄
                card, created = CreditCard.objects.get_or_create(
                    name=card_name,
                    bank=bank_name,
                    defaults={'is_active': True}
                )
                
                if created:
                    created_cards += 1
                    self.stdout.write(f"建立新卡片: {bank_name} {card_name}")
                
                # 處理回饋資訊（簡化版本）
                reward_count = self.create_reward_categories(card, content)
                created_rewards += reward_count
                
                processed_count += 1
                
            except Exception as e:
                self.stdout.write(f"處理資料時發生錯誤: {e}")
                continue
        
        self.stdout.write(
            f"處理完成！\n"
            f"處理資料: {processed_count} 筆\n"
            f"建立卡片: {created_cards} 張\n"
            f"建立回饋: {created_rewards} 筆"
        )

    def extract_bank_and_card(self, text):
        """簡化的銀行和卡片名稱提取"""
        # 常見銀行關鍵字
        bank_keywords = [
            '中國信託', '中信', '國泰世華', '國泰', '玉山銀行', '玉山',
            '台新銀行', '台新', '富邦銀行', '富邦', '星展', '永豐',
            '聯邦', '滙豐', '第一銀行', '第一', '合作金庫', '合庫',
            '兆豐', '遠東', '凱基', '樂天', '彰化', '華南', '新光',
            '上海商銀', '上海', '美國運通', '渣打', '陽信', 'Line Bank',
            '將來', '元大', '台中', '王道'
        ]
        
        bank_name = None
        card_name = None
        
        # 尋找銀行名稱
        for bank in bank_keywords:
            if bank in text:
                bank_name = bank
                break
        
        # 提取卡片名稱（移除銀行名稱後的部分）
        if bank_name:
            card_name = text.replace(bank_name, '').strip()
            # 移除常見後綴
            card_name = re.sub(r'\s*(信用卡|卡)$', '', card_name)
        
        return bank_name, card_name

    def create_reward_categories(self, card, content_lines):
        """建立回饋分類記錄（簡化版本）"""
        reward_count = 0
        
        # 簡化的回饋率提取
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            
            # 尋找回饋率模式
            rate_match = re.search(r'(\d+(?:\.\d+)?)%', line)
            if rate_match:
                rate = float(rate_match.group(1))
                
                # 判斷消費類別（簡化）
                category = "一般消費"
                scope = "國內"
                reward_type = "現金回饋"
                
                if any(keyword in line for keyword in ['餐廳', '美食', '餐飲']):
                    category = "美食"
                    scope = "餐廳"
                elif any(keyword in line for keyword in ['加油', '加油站']):
                    category = "加油"
                    scope = "加油站"
                elif any(keyword in line for keyword in ['購物', '百貨', '電商']):
                    category = "購物"
                    scope = "百貨"
                elif any(keyword in line for keyword in ['海外', '國外']):
                    scope = "海外"
                
                # 建立回饋記錄
                try:
                    RewardCategory.objects.create(
                        card=card,
                        category=category,
                        scope=scope,
                        min_rate=rate,
                        max_rate=rate,
                        reward_type=reward_type,
                        is_active=True
                    )
                    reward_count += 1
                except Exception as e:
                    # 忽略重複記錄錯誤
                    pass
        
        return reward_count

