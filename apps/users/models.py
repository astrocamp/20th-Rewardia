from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


# class UserProfile(models.Model):
#     #用戶資料擴展
    
#     # 偏好回饋類型
#     class PreferredRewardType(models.TextChoices):
#         CASHBACK = 'CASHBACK', '現金回饋'
#         POINTS = 'POINTS', '紅利點數'
#         LINEPAY = 'LINEPAY', 'Line Pay 點數'
#         MIXED = 'MIXED', '不限制'
    
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name='profile',
#         verbose_name='User'  # 用戶
#     )
#     preferred_reward_type = models.CharField(
#         'Preferred Reward Type',  # 偏好回饋類型
#         max_length=20,
#         choices=PreferredRewardType.choices,
#         default=PreferredRewardType.CASHBACK
#     )
#     monthly_spending = models.DecimalField(
#         'Monthly Average Spending',  # 月平均消費
#         max_digits=8,
#         decimal_places  =2,
#         null=True,
#         blank=True,
#         validators=[MinValueValidator(0)],
#         help_text='用於個人化推薦'
#     )
    
#     class Meta:
#         db_table = 'user_profiles'
#         verbose_name = 'User Profile'  # 用戶資料
#         verbose_name_plural = 'User Profiles'  # 用戶資料
    
#     def __str__(self):
#         return f"{self.user.username} 的資料"
    
#     @property
#     def display_name(self):
#         # 顯示名稱
#         if self.user.first_name and self.user.last_name:
#             return f"{self.user.first_name} {self.user.last_name}"
#         return self.user.username


# # 自動創建 Profile 的信號
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     # 當創建新用戶時，自動創建對應的 Profile
#     if created:
#         UserProfile.objects.create(user=instance)


# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     # 保存用戶時，同時保存 Profile
#     if hasattr(instance, 'profile'):
#         instance.profile.save()


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
  
    
    added_date = models.DateTimeField('Added Date', auto_now_add=True)  # 新增日期
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
        return f"{self.user.username} - {self.card.name}"
    
    @property
    def display_name(self):
        #  顯示名稱
        return self.card.name


class UserPreference(models.Model):
    #用戶偏好設定
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name='User'  # 用戶
    )

    favorite_cards = models.ManyToManyField(
        'cards.CreditCard',
        blank=True,
        related_name='favorited_by_users',
        verbose_name='收藏的信用卡'
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


