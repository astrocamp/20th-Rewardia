from django.core.management.base import BaseCommand
from apps.card_crawler.roo import crawl_roo_cards, crawl_roo_urls
import random


class Command(BaseCommand):
    help = "在袋鼠金融抓取信用卡資料，並把銀行、信用卡名分別存進對應的資料庫，並把抓取到的資料存進抓取資料的資料庫。"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_cards = []
        self.processed_urls = set()
        # 仿效真人操作瀏覽器，隨機從0.7-1.4秒之間，挑選暫停秒數
        self.sleep_time = random.uniform(7, 14)

    def handle(self, *args, **options):
        self.stdout.write("🦘開始抓取袋鼠金融信用卡🦘")

        try:
            category_urls = crawl_roo_urls()
            crawl_roo_cards(category_urls)
            self.stdout.write("✅ 成功抓取和存取資料")
        except Exception as e:
            self.stdout.write(f"❌ 失敗: {e}")
