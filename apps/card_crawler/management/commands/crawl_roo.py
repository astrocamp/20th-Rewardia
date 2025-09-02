from django.core.management.base import BaseCommand
from apps.card_crawler.roo import main_crawler
import random


class Command(BaseCommand):
    help = "在袋鼠金融抓取信用卡資料，並把銀行、信用卡名分別存進對應的資料庫，並把抓取到的資料存進抓取資料的資料庫。"

    def handle(self, *args, **options):
        self.stdout.write("🦘開始抓取袋鼠金融信用卡🦘")

        main_crawler()
