from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserCard(models.Model):
    # 用戶持卡記錄
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_cards',
        verbose_name='User'  # 用戶
    )
    card = models.ForeignKey(
        'cards.CreditCard',
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='Credit Card'  # 信用卡
    )
    nickname = models.CharField(
        'Card Nickname',  # 卡片暱稱
        max_length=50,
        blank=True,
        null=True,
        help_text='用戶自定義的卡片名稱'
    )
    added_date = models.DateTimeField('Added Date', auto_now_add=True)  # 新增日期
    is_primary = models.BooleanField(
        'Primary Card',  # 主要卡片
        default=False,
        help_text='用戶的主要推薦卡片'
    )
    is_active = models.BooleanField('Is Active', default=True)  # 啟用狀態
    
    class Meta:
        db_table = 'user_cards'
        verbose_name = 'User Card'  # 用戶持卡
        verbose_name_plural = 'User Cards'  # 用戶持卡
        ordering = ['-added_date']
        unique_together = [['user', 'card']]
        indexes = [
            models.Index(fields=['user', 'is_active'], name='user_cards_active_idx'),
        ]
    
    def __str__(self):
        display_name = self.nickname or self.card.name
        return f"{self.user.username} - {display_name}"


class UserPreference(models.Model):
    #用戶偏好設定
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name='User'  # 用戶
    )
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preference'  # 用戶偏好
        verbose_name_plural = 'User Preferences'  # 用戶偏好
    
    def __str__(self):
        return f"{self.user.username} 的偏好設定"


# 自動創建 Preference 的信號
@receiver(post_save, sender=User)
def create_user_preference(sender, instance, created, **kwargs):
    #當創建新用戶時，自動創建對應的偏好設定¶
    if created:
        UserPreference.objects.create(user=instance)
