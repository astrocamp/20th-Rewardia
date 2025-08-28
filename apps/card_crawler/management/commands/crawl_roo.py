from django.core.management.base import BaseCommand
from apps.card_crawler.roo import crawl_roo_cards, crawl_roo_urls, get_card_info
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
            self.stdout.write("🦘開始抓取袋鼠金融信用卡分類🦘")
            category_urls = crawl_roo_urls()

            self.stdout.write("🦘開始抓取分類中的信用卡資料🦘")
            crawl_roo_cards(category_urls)
            self.stdout.write("✅抓取和存取資料完畢")
        except Exception as error:
            self.stdout.write(f"失敗: {error}")

        try:
            # 把失敗的卡再帶進來抓一次
            for failed in self.failed_cards:
                get_card_info(failed["url"])
        except Exception as error:
            self.stdout.write(f"失敗: {error}")
