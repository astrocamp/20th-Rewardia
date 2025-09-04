from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.cards.models import CreditCard
from django.utils import timezone
from decimal import Decimal


class RewardCategory(models.Model):
    """已通過審核的回饋分類規則"""

    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name="reward_categories",
        verbose_name="信用卡",
    )

    category = models.CharField(
        "消費類別", max_length=50, help_text="例如：餐廳、加油站"
    )
    scope = models.CharField(
        "消費種類", max_length=50, help_text="例如：速食、一般餐廳"
    )

    min_rate = models.DecimalField(
        "最低回饋率",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="1.00 代表 1%",
    )
    max_rate = models.DecimalField(
        "最高回饋率",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="5.00 代表 5%",
    )

    reward_type = models.CharField(
        "回饋類型", max_length=20, help_text="例如：現金回饋、紅利點數"
    )

    is_active = models.BooleanField("是否啟用", default=True)

    created_at = models.DateTimeField("建立時間", auto_now_add=True)
    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        db_table = "reward_categories"
        verbose_name = "回饋分類規則"
        verbose_name_plural = "回饋分類規則"
        ordering = ["card", "-max_rate"]
        indexes = [
            models.Index(fields=["card", "category"], name="rewards_card_category_idx"),
            models.Index(fields=["is_active"], name="rewards_active_idx"),
            models.Index(
                fields=["min_rate", "max_rate"], name="rewards_rate_range_idx"
            ),
        ]
        unique_together = [["card", "category", "scope"]]

    def __str__(self):
        if self.min_rate is not None and self.max_rate is not None:
            if self.min_rate == self.max_rate:
                rate_display = f"{self.min_rate:.2f}%"
            else:
                rate_display = f"{self.min_rate:.2f}-{self.max_rate:.2f}%"
        elif self.min_rate is not None:
            rate_display = f"{self.min_rate:.2f}%"
        elif self.max_rate is not None:
            rate_display = f"{self.max_rate:.2f}%"
        else:
            rate_display = "未知回饋率"

        return f"{self.card.name} - {self.category}/{self.scope}: {rate_display}"

    @property
    def effective_rate(self):
        """有效回饋率 - 取最高值"""
        if self.max_rate is not None:
            return self.max_rate
        elif self.min_rate is not None:
            return self.min_rate
        else:
            return Decimal("0")

    # def __str__(self):
    #     """顯示格式：信用卡名 - 分類/範圍: 回饋率"""
    #     rate_display = f"{self.min_rate}%" if self.min_rate else "未知回饋率"
    #     if self.max_rate and self.max_rate != self.min_rate:
    #         rate_display = f"{self.min_rate}-{self.max_rate}%"

    #     return f"{self.card.name} - {self.category}/{self.scope}: {rate_display}"

    # @property
    # def effective_rate(self):
    #     """有效回饋率 - 取最高值"""
    #     return self.max_rate or self.min_rate or 0

    # 以下為版本控制，暫時備注
    # 回饋分類規則

    # 回饋類型選擇
    # class RewardType(models.TextChoices):
    #     CASHBACK = "CASHBACK", "現金回饋"
    #     POINTS = "POINTS", "紅利點數"
    #     LINEPAY = "LINEPAY", "Line Pay 點數"
    #     MILES = "MILES", "哩程"
    #     OTHER = "OTHER", "其他"

    # 消費分類選擇
    # class Category(models.TextChoices):
    #     ONLINE_SHOPPING = "ONLINE", "電商"
    #     SUPERMARKET = "SUPER", "超市"
    #     DEPARTMENT_STORE = "DEPT", "百貨公司"
    #     CONVENIENCE_STORE = "CVS", "便利商店"
    #     GAS_STATION = "GAS", "加油站"
    #     RESTAURANT = "REST", "餐廳"
    #     ENTERTAINMENT = "ENT", "休閒娛樂"
    #     TRANSPORT = "TRANS", "交通運輸"
    #     HOSPITAL = "HOSP", "醫療院所"
    #     EDUCATION = "EDU", "教育學習"
    #     TELECOM = "TEL", "電信通訊"
    #     INSURANCE = "INS", "保險"
    #     UTILITY = "UTIL", "公用事業"
    #     STREAMING = "STREAM", "串流平台"
    #     TRAVEL = "TRA", "旅遊/訂房"
    #     OTHER = "OTHER", "其他"

    # card = models.ForeignKey(
    #     CreditCard,
    #     on_delete=models.CASCADE,
    #     related_name="reward_categories",
    #     verbose_name="Credit Card",
    # )
    # category = models.CharField("Spending Category", max_length=20)
    # rate = models.DecimalField(
    #     "Reward Rate",
    #     max_digits=4,
    #     decimal_places=2,
    #     validators=[MinValueValidator(0), MaxValueValidator(100)],
    #     help_text="百分比，例如 3.0 表示 3%",
    # )
    # reward_type = models.CharField("回饋類型", max_length=20)
    # points_value = models.DecimalField(
    #     "Points Value",
    #     max_digits=4,
    #     decimal_places=3,
    #     null=True,
    #     blank=True,
    #     validators=[MinValueValidator(0)],
    #     help_text="1點等於多少元，例如 0.5 表示 1點=0.5元",
    # )
    # max_spending = models.DecimalField(
    #     "Maximum Reward Spending",
    #     max_digits=8,
    #     decimal_places=2,
    #     null=True,
    #     blank=True,
    #     validators=[MinValueValidator(0)],
    #     help_text="超過此金額的消費不給回饋或降級回饋",
    # )
    # is_rotating = models.BooleanField(
    #     "Is Rotating", default=False, help_text="是否為季度輪替回饋"
    # )
    # start_date = models.DateField("Start Date", null=True, blank=True)
    # end_date = models.DateField("End Date", null=True, blank=True)
    # requires_activation = models.BooleanField(
    #     "Requires Activation", default=False, help_text="是否需要事先登錄才能享有回饋"
    # )
    # created_at = models.DateTimeField("Created At", auto_now_add=True)

    # class Meta:
    #     db_table = "reward_categories"
    #     verbose_name = "Reward Category"
    #     verbose_name_plural = "Reward Categories"
    #     ordering = ["card", "-rate"]
    #     indexes = [
    #         models.Index(fields=["card", "category"], name="rewards_card_category_idx"),
    #         models.Index(
    #             fields=["start_date", "end_date"], name="rewards_date_range_idx"
    #         ),
    #     ]
    #     unique_together = [["card", "category", "start_date"]]

    # def __str__(self):
    #     # 回傳：信用卡名 - 分類: 回饋趴數%
    #     return f"{self.card.name} - {self.get_category_display()}: {self.rate}%"

    # @property
    # def effective_rate(self):
    #     # 有效回饋率（考慮點數價值)

    #     # 現金回饋率
    #     if self.reward_type == self.RewardType.CASHBACK:
    #         return self.rate
    #     # 點數回饋率
    #     elif (
    #         self.reward_type in [self.RewardType.POINTS, self.RewardType.LINEPAY]
    #         and self.points_value
    #     ):
    #         return self.rate * self.points_value
    #     else:
    #         return self.rate

    # @property
    # def is_active(self):
    #     # 檢查回饋規則是否在有效期間內
    #     today = timezone.now().date()

    #     if self.start_date and today < self.start_date:
    #         return False

    #     if self.end_date and today > self.end_date:
    #         return False

    #     return True


class PendingReward(models.Model):
    """待審核的回饋規則"""

    class Status(models.TextChoices):
        PENDING = "PENDING", "待審核"
        REVIEWING = "REVIEWING", "審核中"
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

    # 軟刪除
    soft_deleted_at = models.DateTimeField("軟刪除時間", null=True, blank=True)
    
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

    def approve_and_create_reward_category(self):
        """通過審核並建立RewardCategory"""
        if self.status != self.Status.APPROVED:
            self.status = self.Status.APPROVED
            self.save()

            # 建立新的RewardCategory
            reward_category = RewardCategory.objects.create(
                card=self.card,
                category=self.nlp_category,
                scope=self.nlp_scope,
                min_rate=self.min_rate,
                max_rate=self.max_rate,
                reward_type=self.reward_type,
                is_active=True,
            )
            return reward_category
        return None

    def reject(self):
        """駁回審核"""
        self.status = self.Status.REJECTED
        self.save()
        
    def soft_delete(self):
        """軟刪除 - 移到審核中狀態"""
        self.soft_deleted_at = timezone.now()
        self.status = self.Status.REVIEWING
        self.save()
    
    @classmethod
    def detect_and_soft_delete_duplicates(cls):
        """檢測並軟刪除重複資料"""
        from django.db.models import Count
        
        # 找出有重複的群組
        duplicates = cls.objects.filter(
            status=cls.Status.PENDING
        ).values(
            'card_id', 'nlp_category', 'nlp_scope', 'reward_type'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for duplicate_group in duplicates:
            # 找出這群組中的所有記錄
            records = cls.objects.filter(
                card_id=duplicate_group['card_id'],
                nlp_category=duplicate_group['nlp_category'],
                nlp_scope=duplicate_group['nlp_scope'],
                reward_type=duplicate_group['reward_type'],
                status=cls.Status.PENDING
            ).order_by('-created_at')  # 最新的在前
            
            # 保留最新的，其他軟刪除
            if records.count() > 1:
                for record in records[1:]:  # 跳過第一筆（最新的）
                    record.soft_delete()
