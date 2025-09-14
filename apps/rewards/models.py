from django.db import models
from apps.cards.models import CreditCard
from django.utils import timezone
from decimal import Decimal
from django.db.models import Count


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
                rate_display = f"{self.min_rate:.2f} ~ {self.max_rate:.2f}%"
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
        """通過審核並建立/更新RewardCategory"""
        if self.status != self.Status.APPROVED:
            # 使用 update_or_create 處理重複情況
            reward_category, created = RewardCategory.objects.update_or_create(
                card=self.card,
                category=self.nlp_category,
                scope=self.nlp_scope,
                defaults={
                    'min_rate': self.min_rate,
                    'max_rate': self.max_rate,
                    'reward_type': self.reward_type,
                    'is_active': True,
                }
            )
            
            # 成功處理後才更新狀態
            self.status = self.Status.APPROVED
            self.save()
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

    def restore_from_soft_delete(self):
        """從軟刪除狀態恢復"""
        self.soft_deleted_at = None
        self.status = self.Status.PENDING
        self.save()

    @classmethod
    def restore_all_soft_deleted(cls):
        """恢復所有被軟刪除的記錄到 PENDING 狀態"""
        soft_deleted_records = cls.objects.filter(
            soft_deleted_at__isnull=False, status=cls.Status.REVIEWING
        )

        count = 0
        for record in soft_deleted_records:
            record.restore_from_soft_delete()
            count += 1

        return count

    @classmethod
    def detect_and_soft_delete_duplicates(cls):
        """檢測並軟刪除重複資料"""

        # 找出有重複的群組 (只查詢未被軟刪除且狀態為 PENDING 的記錄)
        duplicates = (
            cls.objects.filter(status=cls.Status.PENDING, soft_deleted_at__isnull=True)
            .values("card_id", "nlp_category", "nlp_scope", "reward_type")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for duplicate_group in duplicates:
            # 找出這群組中的所有記錄 (只查詢未被軟刪除且狀態為 PENDING 的記錄)
            records = cls.objects.filter(
                card_id=duplicate_group["card_id"],
                nlp_category=duplicate_group["nlp_category"],
                nlp_scope=duplicate_group["nlp_scope"],
                reward_type=duplicate_group["reward_type"],
                status=cls.Status.PENDING,
                soft_deleted_at__isnull=True,
            ).order_by("-created_at")

            # 保留最新的，其他軟刪除
            if records.count() > 1:
                for record in records[1:]:
                    record.soft_delete()
