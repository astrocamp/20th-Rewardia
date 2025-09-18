from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
import base64
import logging


class UserCard(models.Model):
    # 用戶持卡記錄

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_cards",
        verbose_name="User",  # 用戶
    )
    card = models.ForeignKey(
        "cards.CreditCard",
        on_delete=models.CASCADE,
        related_name="users",
        verbose_name="Credit Card",
    )
    nickname = models.CharField(
        "Card Nickname",
        max_length=50,
        blank=True,
        null=True,
        help_text="用戶自定義的卡片名稱",
    )
    added_date = models.DateTimeField("Added Date", auto_now_add=True)  # 新增日期
    is_primary = models.BooleanField(
        "Primary Card",
        default=False,
        help_text="用戶的主要推薦卡片",
    )

    is_active = models.BooleanField("Is Active", default=True)
    
    card_number_encrypted = models.TextField(
        "Encrypted Card Number",
        blank=True,
        null=True,
        help_text="加密後的信用卡卡號"
    )

    class Meta:
        db_table = "user_cards"
        verbose_name = "User Card"  # 用戶持卡
        verbose_name_plural = "User Cards"  # 用戶持卡
        ordering = ["-added_date"]
        unique_together = [["user", "card"]]
        indexes = [
            models.Index(fields=["user", "is_active"], name="user_cards_active_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.is_primary:
            UserCard.objects.filter(user=self.user, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
        super().save(*args, **kwargs)

    def set_card_number(self, card_number):
        """加密並存儲卡號"""
        if card_number:
            try:
                # 從 settings 取得加密金鑰
                key = getattr(settings, 'FERNET_KEY', Fernet.generate_key()).encode()
                fernet = Fernet(key)
                encrypted_data = fernet.encrypt(card_number.encode())
                self.card_number_encrypted = base64.b64encode(encrypted_data).decode()
            except (ValueError, TypeError, UnicodeDecodeError, AttributeError) as e:
                # 記錄具體錯誤並設定為 None
                logger = logging.getLogger(__name__)
                logger.error(f"Card number encryption failed: {e}")
                self.card_number_encrypted = None
        else:
            self.card_number_encrypted = None
    
    def get_card_number(self):
        """解密並返回卡號"""
        if self.card_number_encrypted:
            try:
                key = getattr(settings, 'FERNET_KEY', Fernet.generate_key()).encode()
                fernet = Fernet(key)
                encrypted_data = base64.b64decode(self.card_number_encrypted.encode())
                decrypted_data = fernet.decrypt(encrypted_data)
                return decrypted_data.decode()
            except InvalidToken as e:
                # 處理 Fernet 解密錯誤（金鑰不匹配、資料損毀等）
                logger = logging.getLogger(__name__)
                logger.error(f"Card number decryption failed - Invalid token: {e}")
                return None
            except (ValueError, TypeError, UnicodeDecodeError, AttributeError) as e:
                # 記錄具體錯誤並返回 None
                logger = logging.getLogger(__name__)
                logger.error(f"Card number decryption failed: {e}")
                return None
        return None

    def get_masked_card_number(self):
        """取得遮罩後的卡號顯示（前8後4，中間用*）"""
        card_number = self.get_card_number()
        if card_number:
            # 移除所有非數字字元
            clean_number = ''.join(filter(str.isdigit, card_number))
            if len(clean_number) >= 16:  # 至少 16 位數（標準信用卡）
                # 前8碼 + 中間4個* + 後4碼
                return f"{clean_number[:8]}-****-{clean_number[-4:]}"
            elif len(clean_number) >= 12:  # 至少 12 位數
                # 前8碼 + 中間用* + 後4碼
                middle_stars = '*' * (len(clean_number) - 12)
                return f"{clean_number[:8]}-{middle_stars}-{clean_number[-4:]}"
            else:
                return "****-****-****-****"
        return "未設定"

    def __str__(self):
        display_name = self.nickname or self.card.name
        return f"{self.user.username} - {display_name}"
