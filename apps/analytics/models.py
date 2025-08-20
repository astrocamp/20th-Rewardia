from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.merchants.models import Merchant
from apps.cards.models import CreditCard


class OnlineTransaction(models.Model):
    # 線上交易記錄 - 專注於網路購物和數位支付

    # 交易來源
    class TransactionSource(models.TextChoices):
        CHROME_EXTENSION = "CHROME", "Chrome 擴展偵測"
        MANUAL_ENTRY = "MANUAL", "用戶手動輸入"

    # 支付方式
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = "CREDIT", "信用卡"
        DIGITAL_WALLET = "WALLET", "數位錢包"
        MOBILE_PAY = "MOBILE", "行動支付"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="online_transactions",
        verbose_name="User",  # 用戶
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="online_transactions",
        verbose_name="Merchant",  # 購物網站
    )
    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name="online_transactions",
        verbose_name="Credit Card Used",  # 使用信用卡
    )

    # 交易基本資訊
    amount = models.DecimalField(
        "Transaction Amount",  # 交易金額
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    reward_earned = models.DecimalField(
        "Actual Reward Earned",  # 實際獲得回饋
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="用戶實際獲得的回饋金額",
    )
    transaction_date = models.DateTimeField("Transaction Date")  # 交易時間

    # 線上交易特有資訊
    source = models.CharField(
        "Transaction Source",  # 交易來源
        max_length=10,
        choices=TransactionSource.choices,
        default=TransactionSource.CHROME_EXTENSION,
    )
    payment_method = models.CharField(
        "Payment Method",  # 支付方式
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CREDIT_CARD,
    )

    # Chrome 擴展相關
    url = models.URLField(
        "Shopping Page URL",  # 購物頁面 URL
        blank=True,
        help_text="用戶購物時的頁面 URL",
    )
    page_title = models.CharField(
        "Page Title", max_length=200, blank=True, help_text="購物頁面的標題"  # 頁面標題
    )

    # 推薦系統相關
    was_recommended = models.BooleanField(
        "System Recommended",  # 系統有推薦
        default=False,
        help_text="系統是否有推薦此卡片",
    )
    recommended_card = models.ForeignKey(
        CreditCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommended_for_transactions",
        verbose_name="System Recommended Card",  # 系統推薦卡片
    )
    used_recommended_card = models.BooleanField(
        "Used Recommended Card",  # 使用推薦卡片
        default=False,
        help_text="用戶是否使用了系統推薦的卡片",
    )
    potential_reward_missed = models.DecimalField(
        "Potential Reward Missed",  # 錯失的回饋
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="如果使用推薦卡片可以獲得的額外回饋",
    )

    # 類別標記
    category = models.CharField(
        "Spending Category",  # 消費分類
        max_length=20,
        blank=True,
        help_text="自動識別或手動分類的消費類型",
    )
    tags = models.JSONField(
        "Tags", default=list, help_text="額外的分類標籤，如：特價、節慶促銷等"  # 標籤
    )

    # 備註
    notes = models.TextField("Notes", blank=True)  # 備註

    created_at = models.DateTimeField("Record Time", auto_now_add=True)  # 記錄時間

    class Meta:
        db_table = "online_transactions"
        verbose_name = "Online Transaction"  # 線上交易
        verbose_name_plural = "Online Transactions"  # 線上交易
        ordering = ["-transaction_date"]
        indexes = [
            models.Index(
                fields=["user", "-transaction_date"], name="online_trans_user_date_idx"
            ),
            models.Index(
                fields=["merchant", "-transaction_date"],
                name="online_trans_merchant_date_idx",
            ),
            models.Index(
                fields=["card", "-transaction_date"], name="online_trans_card_date_idx"
            ),
            models.Index(
                fields=["source", "-transaction_date"],
                name="online_trans_source_date_idx",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} @ {self.merchant.name}: ${self.amount}"

    @property
    def reward_rate(self):
        # 實際回饋率
        if self.amount > 0:
            return (self.reward_earned / self.amount) * 100
        return 0

    @property
    def recommendation_accuracy(self):
        # 推薦準確度（用戶是否採用推薦）
        if self.was_recommended:
            return self.used_recommended_card
        return None


class RewardCalculationCache(models.Model):
    # 回饋計算快取 - 針對線上購物優化

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="cached_calculations",
        verbose_name="Merchant",  # 購物網站
    )
    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name="cached_calculations",
        verbose_name="Credit Card",  # 信用卡
    )

    # 常見的線上購物金額區間
    amount = models.DecimalField(
        "Spending Amount",  # 消費金額
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="預計算的金額，如：100, 500, 1000, 2000, 5000",
    )
    calculated_reward = models.DecimalField(
        "Calculated Reward",  # 計算回饋
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    reward_rate = models.DecimalField(
        "Reward Rate",  # 回饋率
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="百分比形式的回饋率",
    )

    # 快取管理
    calculation_date = models.DateTimeField(
        "Calculation Time", auto_now_add=True
    )  # 計算時間
    is_valid = models.BooleanField(
        "Calculation Valid",  # 計算有效
        default=True,
        help_text="回饋規則變更時會標記為無效",
    )
    last_used = models.DateTimeField(
        "Last Used Time",  # 最後使用時間
        null=True,
        blank=True,
        help_text="記錄此快取最後被使用的時間",
    )
    usage_count = models.IntegerField(
        "Usage Count", default=0, help_text="此快取被使用的總次數"  # 使用次數
    )

    class Meta:
        db_table = "reward_calculation_cache"
        verbose_name = "Reward Calculation Cache"  # 回饋計算快取
        verbose_name_plural = "Reward Calculation Caches"  # 回饋計算快取
        ordering = ["-calculation_date"]
        indexes = [
            models.Index(
                fields=["merchant", "amount", "is_valid"],
                name="cache_merchant_amount_idx",
            ),
            models.Index(fields=["card", "is_valid"], name="cache_card_valid_idx"),
            models.Index(
                fields=["is_valid", "-last_used"], name="cache_valid_used_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "card", "amount"],
                name="unique_merchant_card_amount",
            )
        ]

    def __str__(self):
        return f"{self.merchant.name} + {self.card.name}: ${self.amount} → ${self.calculated_reward}"

    def mark_as_used(self):
        # 標記快取被使用
        self.last_used = timezone.now()
        self.usage_count += 1
        self.save(update_fields=["last_used", "usage_count"])


class UserSpendingPattern(models.Model):
    # 用戶線上消費模式分析

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="spending_patterns",
        verbose_name="User",  # 用戶
    )

    # 統計時間區間
    year = models.IntegerField("Year")  # 年份
    month = models.IntegerField("Month")  # 月份

    # 線上消費統計
    total_online_spending = models.DecimalField(
        "Total Online Spending",  # 線上總消費
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    total_rewards_earned = models.DecimalField(
        "Total Rewards Earned", max_digits=8, decimal_places=2, default=0  # 總回饋獲得
    )
    total_rewards_missed = models.DecimalField(
        "Total Rewards Missed",  # 錯失回饋
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="使用推薦卡片可獲得的額外回饋",
    )
    transaction_count = models.IntegerField("Transaction Count", default=0)  # 交易筆數

    # Chrome 擴展使用統計
    chrome_detected_transactions = models.IntegerField(
        "Chrome Detected Transactions",  # Chrome 偵測交易數
        default=0,
        help_text="由 Chrome 擴展自動偵測的交易數量",
    )
    recommendations_shown = models.IntegerField(
        "Recommendations Shown",  # 推薦次數
        default=0,
        help_text="Chrome 擴展顯示推薦的次數",
    )
    recommendations_followed = models.IntegerField(
        "Recommendations Followed",  # 採用推薦次數
        default=0,
        help_text="用戶採用推薦的次數",
    )

    # 詳細分析數據（JSON 格式）
    merchant_spending = models.JSONField(
        "Merchant Spending Statistics",  # 網站消費統計
        default=dict,
        help_text='各購物網站的消費統計：{"shopee.tw": 15000, "momo.com.tw": 8500}',
    )
    category_spending = models.JSONField(
        "Category Spending Statistics",  # 分類消費統計
        default=dict,
        help_text='各消費分類的金額統計：{"electronics": 20000, "clothing": 5000}',
    )
    card_usage = models.JSONField(
        "Card Usage Statistics",  # 卡片使用統計
        default=dict,
        help_text='各卡片的使用統計：{"card_1": {"amount": 15000, "transactions": 25}}',
    )
    payment_methods = models.JSONField(
        "Payment Methods Statistics",  # 支付方式統計
        default=dict,
        help_text="各種支付方式的使用統計",
    )

    class Meta:
        db_table = "user_spending_patterns"
        verbose_name = "User Spending Pattern"  # 用戶消費模式
        verbose_name_plural = "User Spending Patterns"  # 用戶消費模式
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "year", "month"], name="unique_user_year_month"
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "-year", "-month"], name="patterns_user_date_idx"
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.year}/{self.month:02d}"

    @property
    def average_reward_rate(self):
        # 平均回饋率#
        if self.total_online_spending > 0:
            return (self.total_rewards_earned / self.total_online_spending) * 100
        return 0

    @property
    def recommendation_adoption_rate(self):
        # 推薦採用率#
        if self.recommendations_shown > 0:
            return (self.recommendations_followed / self.recommendations_shown) * 100
        return 0

    @property
    def chrome_usage_rate(self):
        # Chrome 擴展使用率#
        if self.transaction_count > 0:
            return (self.chrome_detected_transactions / self.transaction_count) * 100
        return 0


class WebsiteAnalytics(models.Model):
    # 購物網站分析數據

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="analytics",
        verbose_name="Merchant",  # 購物網站
    )

    # 統計時間
    date = models.DateField("Statistics Date")  # 統計日期

    # 網站活動統計
    total_transactions = models.IntegerField(
        "Total Transactions", default=0
    )  # 總交易數
    total_transaction_value = models.DecimalField(
        "Total Transaction Value",  # 總交易金額
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    unique_users = models.IntegerField("Unique Users", default=0)  # 獨立用戶數

    # Chrome 擴展相關
    chrome_extension_views = models.IntegerField(
        "Chrome Extension Views",  # 擴展顯示次數
        default=0,
        help_text="Chrome 擴展在此網站的顯示次數",
    )
    recommendation_clicks = models.IntegerField(
        "Recommendation Clicks",  # 推薦點擊次數
        default=0,
        help_text="用戶點擊推薦卡片的次數",
    )

    # 最受歡迎的卡片
    most_used_cards = models.JSONField(
        "Most Used Cards",  # 最常使用卡片
        default=dict,
        help_text="在此網站最常使用的卡片統計",
    )

    # 平均數據
    average_transaction_value = models.DecimalField(
        "Average Transaction Value",  # 平均交易金額
        max_digits=8,
        decimal_places=2,
        default=0,
    )
    average_reward_rate = models.DecimalField(
        "Average Reward Rate", max_digits=4, decimal_places=2, default=0  # 平均回饋率
    )

    created_at = models.DateTimeField("Created At", auto_now_add=True)  # 建立時間

    class Meta:
        db_table = "website_analytics"
        verbose_name = "Website Analytics"  # 網站分析
        verbose_name_plural = "Website Analytics"  # 網站分析
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "date"], name="unique_merchant_date"
            )
        ]
        indexes = [
            models.Index(fields=["merchant", "-date"], name="website_analytics_idx"),
            models.Index(fields=["-date"], name="website_analytics_date_idx"),
        ]

    def __str__(self):
        return f"{self.merchant.name} - {self.date}"
