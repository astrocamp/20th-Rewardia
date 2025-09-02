from django.db import models
import re


# Create your models here.
class CreditCard(models.Model):
    # 信用卡資訊

    # 卡片網路選擇
    class CardNetwork(models.TextChoices):
        VISA = "Visa", "Visa"
        MASTERCARD = "Mastercard", "Mastercard"
        JCB = "JCB", "JCB"
        AMEX = "美國運通 AMEX", "美國運通"
        UNION_PAY = "銀聯", "銀聯"

    # 卡片等級選擇
    class CardType(models.TextChoices):
        CLASSIC = "CLASSIC", "一般卡"
        GOLD = "GOLD", "金卡"
        PLATINUM = "PLATINUM", "白金卡"
        INFINITE = "INFINITE", "無限卡"
        TITANIUM = "TITANIUM", "鈦金卡"
        WORLD = "WORLD", "世界卡"
        SIGNATURE = "SIGNATURE", "御璽卡"
        BUSINESS = "BUSINESS", "商務卡"
        SIGBUSINESS = "SIGBUSINESS", "商務御璽卡"

    class Bank(models.TextChoices):
        滙豐 = "滙豐"
        中國信託 = "中國信託"
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
        上海商銀 = "上海商銀"
        美國運通 = "美國運通"
        渣打 = "渣打"
        陽信 = "陽信"
        LINE_Bank = "LINE Bank"
        將來 = "將來"
        元大 = "元大"
        台中 = "台中"
        王道 = "王道"
        無 = "無"

    name = models.CharField("信用卡名稱", max_length=100)
    bank = models.CharField("銀行名稱", max_length=50, choices=Bank.choices)
    foreign_transaction_fee = models.DecimalField(
        "Foreign Transaction Fee",
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="百分比，例如 1.5 表示 1.5%",
    )
    card_network = models.CharField(
        "Card Network",
        max_length=20,
        blank=True,
        null=True,
        choices=CardNetwork.choices,
    )
    card_type = models.CharField(
        "Card Type", max_length=20, blank=True, null=True, choices=CardType.choices
    )
    is_active = models.BooleanField("Is Active", default=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        db_table = "credit_cards"
        verbose_name = "Credit Card"
        verbose_name_plural = "Credit Cards"
        ordering = ["bank", "name"]
        indexes = [
            models.Index(fields=["bank", "is_active"], name="cards_bank_active_idx"),
            models.Index(fields=["card_network"], name="cards_network_idx"),
            models.Index(fields=["card_type"], name="cards_type_idx"),
        ]

    def __str__(self):
        return f"{self.bank} {self.name}"

    def save(self, *args, **kwargs):
        self.bank = self.format_bank_name(self.bank)
        super().save(*args, **kwargs)

    def format_bank_name(self, bank_name):
        if re.search(r"(合作?金?庫)", bank_name):
            return "合庫"
        if bank_name not in CreditCard.Bank.values:
            return "無"
        return bank_name
