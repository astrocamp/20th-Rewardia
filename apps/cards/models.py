from django.db import models
import re


class CreditCard(models.Model):
    # 信用卡資訊

    class Bank(models.TextChoices):
        滙豐 = "滙豐"
        中國 = "中國信託"
        國泰 = "國泰"
        玉山 = "玉山"
        台新 = "台新"
        富邦 = "富邦"
        第一 = "第一"
        合庫 = "合庫"
        兆豐 = "兆豐"
        永豐 = "永豐"
        遠東 = "遠東"
        凱基 = "凱基"
        聯邦 = "聯邦"
        星展 = "星展"
        樂天 = "樂天"
        彰化 = "彰化"
        華南 = "華南"
        新光 = "新光"
        上海 = "上海商銀"
        美國 = "美國運通"
        渣打 = "渣打"
        陽信 = "陽信"
        LineBank = "Line Bank"
        將來 = "將來"
        元大 = "元大"
        台中 = "台中"
        王道 = "王道"
        無 = "無"

    name = models.CharField("信用卡名稱", max_length=50)
    bank = models.CharField("銀行名稱", max_length=15)
    is_active = models.BooleanField("Is Active", default=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        db_table = "credit_cards"
        verbose_name = "Credit Card"
        verbose_name_plural = "Credit Cards"
        indexes = [
            models.Index(fields=["bank", "is_active"], name="cards_bank_active_idx")
        ]

    def __str__(self):
        return f"{self.bank} {self.name}"

    def save(self, *args, **kwargs):
        self.bank = self.format_bank_name(self.bank)
        super().save(*args, **kwargs)

    def format_bank_name(self, bank_name):
        # if re.search("Bank", bank_name):
        #     return "Line Bank"
        if re.search("一銀", bank_name):
            return "第一"
        if re.search("美國", bank_name):
            return "美國通運"
        if bank_name not in CreditCard.Bank.values:
            return "無"
        return bank_name
