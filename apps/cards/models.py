from django.db import models


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

    name = models.CharField("信用卡名稱", max_length=100)
    bank = models.CharField("銀行名稱", max_length=50)
    # annual_fee = models.DecimalField(
    #     "Annual Fee",
    #     max_digits=8,
    #     decimal_places=2,
    #     blank=True,
    #     null=True,
    # )
    # signup_bonus = models.IntegerField(
    #     "Sign Up Bonus", blank=True, null=True, help_text="新戶禮金額或點數"
    # )
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

    @property
    def has_annual_fee(self):
        return self.annual_fee > 0

    def calculate_reward(self, merchant, amount):
        """計算這張卡在指定商家的回饋"""
        from apps.rewards.models import RewardCategory, MerchantReward
        from decimal import Decimal

        amount = Decimal(str(amount))

        # 1. 優先找特定商家回饋
        try:
            merchant_reward = MerchantReward.objects.get(
                card=self, merchant=merchant, is_active=True
            )
            rate = Decimal(str(merchant_reward.effective_rate))
            reward_amount = amount * rate / 100
            return float(reward_amount), float(rate), "使用商家特殊回饋"
        except MerchantReward.DoesNotExist:
            pass

        # 2. 找分類回饋
        try:
            category_reward = RewardCategory.objects.get(
                card=self, category=merchant.category, is_active=True
            )
            rate = Decimal(str(category_reward.effective_rate))
            reward_amount = amount * rate / 100
            return float(reward_amount), float(rate), "使用分類回饋"
        except RewardCategory.DoesNotExist:
            pass

        # 3. 使用基本回饋
        basic_rate = Decimal("1.0")
        reward_amount = amount * basic_rate / 100
        return float(reward_amount), float(basic_rate), "使用基本回饋(1%)"
