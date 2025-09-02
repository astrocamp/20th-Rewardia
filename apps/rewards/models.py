from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.cards.models import CreditCard
from django.utils import timezone


class RewardCategory(models.Model):
    # 回饋分類規則

    # 回饋類型選擇
    class RewardType(models.TextChoices):
        CASHBACK = "CASHBACK", "現金回饋"
        POINTS = "POINTS", "紅利點數"
        LINEPAY = "LINEPAY", "Line Pay 點數"
        MILES = "MILES", "哩程"
        OTHER = "OTHER", "其他"

    # 消費分類選擇
    class Category(models.TextChoices):
        ONLINE_SHOPPING = "ONLINE", "電商"
        SUPERMARKET = "SUPER", "超市"
        DEPARTMENT_STORE = "DEPT", "百貨公司"
        CONVENIENCE_STORE = "CVS", "便利商店"
        GAS_STATION = "GAS", "加油站"
        RESTAURANT = "REST", "餐廳"
        ENTERTAINMENT = "ENT", "休閒娛樂"
        TRANSPORT = "TRANS", "交通運輸"
        HOSPITAL = "HOSP", "醫療院所"
        EDUCATION = "EDU", "教育學習"
        TELECOM = "TEL", "電信通訊"
        INSURANCE = "INS", "保險"
        UTILITY = "UTIL", "公用事業"
        STREAMING = "STREAM", "串流平台"
        TRAVEL = "TRA", "旅遊/訂房"
        OTHER = "OTHER", "其他"

    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name="reward_categories",
        verbose_name="Credit Card",
    )
    category = models.CharField(
        "Spending Category", max_length=20, choices=Category.choices
    )
    rate = models.DecimalField(
        "Reward Rate",
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="百分比，例如 3.0 表示 3%",
    )
    reward_type = models.CharField(
        "Reward Type",
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.CASHBACK,
    )
    points_value = models.DecimalField(
        "Points Value",
        max_digits=4,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="1點等於多少元，例如 0.5 表示 1點=0.5元",
    )
    max_spending = models.DecimalField(
        "Maximum Reward Spending",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="超過此金額的消費不給回饋或降級回饋",
    )
    is_rotating = models.BooleanField(
        "Is Rotating", default=False, help_text="是否為季度輪替回饋"
    )
    start_date = models.DateField("Start Date", null=True, blank=True)
    end_date = models.DateField("End Date", null=True, blank=True)
    requires_activation = models.BooleanField(
        "Requires Activation", default=False, help_text="是否需要事先登錄才能享有回饋"
    )
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        db_table = "reward_categories"
        verbose_name = "Reward Category"
        verbose_name_plural = "Reward Categories"
        ordering = ["card", "-rate"]
        indexes = [
            models.Index(fields=["card", "category"], name="rewards_card_category_idx"),
            models.Index(
                fields=["start_date", "end_date"], name="rewards_date_range_idx"
            ),
        ]
        unique_together = [["card", "category", "start_date"]]

    def __str__(self):
        # 回傳：信用卡名 - 分類: 回饋趴數%
        return f"{self.card.name} - {self.get_category_display()}: {self.rate}%"

    @property
    def effective_rate(self):
        # 有效回饋率（考慮點數價值)

        # 現金回饋率
        if self.reward_type == self.RewardType.CASHBACK:
            return self.rate
        # 點數回饋率
        elif (
            self.reward_type in [self.RewardType.POINTS, self.RewardType.LINEPAY]
            and self.points_value
        ):
            return self.rate * self.points_value
        else:
            return self.rate

    @property
    def is_active(self):
        # 檢查回饋規則是否在有效期間內
        today = timezone.now().date()

        if self.start_date and today < self.start_date:
            return False

        if self.end_date and today > self.end_date:
            return False

        return True

class PendingReward(models.Model):
    """待審核的回饋規則"""

    class Status(models.TextChoices):
        PENDING = "PENDING", "待審核"
        APPROVED = "APPROVED", "已通過"
        REJECTED = "REJECTED", "已拒絕"

    # 關聯
    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name="pending_rewards",
        verbose_name="信用卡",
    )

    # NLP 提取資料
    nlp_category = models.CharField("NLP分類", max_length=50)
    nlp_scope = models.CharField("NLP範圍", max_length=50)
    extracted_sentence = models.TextField("提取句子")
    confidence = models.DecimalField("信心度", max_digits=4, decimal_places=3)
    min_rate = models.DecimalField(
        "最低回饋率", max_digits=4, decimal_places=2, null=True, blank=True
    )
    max_rate = models.DecimalField(
        "最高回饋率", max_digits=4, decimal_places=2, null=True, blank=True
    )
    reward_type = models.CharField("回饋類型", max_length=20)

    # 審核狀態
    status = models.CharField(
        "審核狀態", max_length=10, choices=Status.choices, default=Status.PENDING
    )

    # 時間戳記
    created_at = models.DateTimeField("建立時間", auto_now_add=True)

    class Meta:
        db_table = "pending_rewards"
        verbose_name = "待審核回饋規則"
        verbose_name_plural = "待審核回饋規則"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="pending_rewards_status_idx"),
            models.Index(fields=["card"], name="pending_rewards_card_idx"),
            models.Index(fields=["-created_at"], name="pending_rewards_date_idx"),
        ]

    def __str__(self):
        rate_display = self.min_rate or self.max_rate or "未知"
        return (
            f"{self.card.name} - {self.nlp_category}/{self.nlp_scope}: {rate_display}%"
        )
