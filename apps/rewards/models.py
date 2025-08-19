from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.cards.models import CreditCard
from apps.merchants.models import Merchant
from django.utils import timezone


class RewardCategory(models.Model):
    # 回饋分類規則
    
    # 回饋類型選擇
    class RewardType(models.TextChoices):
        CASHBACK = 'CASHBACK', '現金回饋'
        POINTS = 'POINTS', '紅利點數'
        LINEPAY = 'LINEPAY', 'Line Pay 點數'
        MILES = 'MILES', '哩程'
        OTHER = 'OTHER', '其他'
    
    # 消費分類選擇
    class Category(models.TextChoices):
        ONLINE_SHOPPING = 'ONLINE', '電商'
        SUPERMARKET = 'SUPER', '超市'
        DEPARTMENT_STORE = 'DEPT', '百貨公司'
        CONVENIENCE_STORE = 'CVS', '便利商店'
        GAS_STATION = 'GAS', '加油站'
        RESTAURANT = 'REST', '餐廳'
        ENTERTAINMENT = 'ENT', '休閒娛樂'
        TRANSPORT = 'TRANS', '交通運輸'
        HOSPITAL = 'HOSP', '醫療院所'
        EDUCATION = 'EDU', '教育學習'
        TELECOM = 'TEL', '電信通訊'
        INSURANCE = 'INS', '保險'
        UTILITY = 'UTIL', '公用事業'
        STREAMING = 'STREAM', '串流平台'
        TRAVEL = 'TRA', '旅遊/訂房'
        OTHER = 'OTHER', '其他'
    
    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name='reward_categories',
        verbose_name='Credit Card'
    )
    category = models.CharField(
        'Spending Category',
        max_length=20,
        choices=Category.choices
    )
    rate = models.DecimalField(
        'Reward Rate',
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='百分比，例如 3.0 表示 3%'
    )
    reward_type = models.CharField(
        'Reward Type',
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.CASHBACK
    )
    points_value = models.DecimalField(
        'Points Value',
        max_digits=4,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='1點等於多少元，例如 0.5 表示 1點=0.5元'
    )
    max_spending = models.DecimalField(
        'Maximum Reward Spending',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='超過此金額的消費不給回饋或降級回饋'
    )
    is_rotating = models.BooleanField(
        'Is Rotating',
        default=False,
        help_text='是否為季度輪替回饋'
    )
    start_date = models.DateField('Start Date', null=True, blank=True)
    end_date = models.DateField('End Date', null=True, blank=True)
    requires_activation = models.BooleanField(
        'Requires Activation',
        default=False,
        help_text='是否需要事先登錄才能享有回饋'
    )
    created_at = models.DateTimeField('Created At', auto_now_add=True)

    class Meta:
        db_table = 'reward_categories'
        verbose_name = 'Reward Category'
        verbose_name_plural = 'Reward Categories'
        ordering = ['card', '-rate']
        indexes = [
            models.Index(fields=['card', 'category'], name='rewards_card_category_idx'),
            models.Index(fields=['start_date', 'end_date'], name='rewards_date_range_idx'),
        ]
        unique_together = [['card', 'category', 'start_date']]

    def __str__(self):
        # 回傳：信用卡名 - 分類: 回饋趴數%
        return f"{self.card.name} - {self.get_category_display()}: {self.rate}%"
    
    @property
    def effective_rate(self):
        #有效回饋率（考慮點數價值)

        # 現金回饋率
        if self.reward_type == self.RewardType.CASHBACK:
            return self.rate
        # 點數回饋率
        elif self.reward_type in [self.RewardType.POINTS, self.RewardType.LINEPAY] and self.points_value:
            return self.rate * self.points_value
        else:
            return self.rate

    @property
    def is_active(self):
        #檢查回饋規則是否在有效期間內
        today = timezone.now().date()
        
        if self.start_date and today < self.start_date:
            return False
        
        if self.end_date and today > self.end_date:
            return False
        
        return True

class MerchantReward(models.Model):
    # 特定商家回饋規則
    
    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name='merchant_rewards',
        verbose_name='Credit Card'
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='reward_rules',
        verbose_name='Merchant'
    )
    category = models.ForeignKey(
        RewardCategory,
        on_delete=models.CASCADE,
        related_name='merchant_overrides',
        verbose_name='Corresponding Reward Category',
        # e.g. RewardCategory.objects.get(pk=1).merchant_overrides
        # 來看這一個reward類別有沒有可以覆蓋的rewards
        help_text='此特殊規則會覆蓋對應的分類回饋'
    )
    rate = models.DecimalField(
        'Reward Rate',
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='覆蓋原分類回饋率，留空則使用分類回饋率'
    )
    reward_type = models.CharField(
        'Reward Type',
        max_length=20,
        choices=RewardCategory.RewardType.choices,
        blank=True,
        help_text='留空則使用分類設定'
    )
    points_value = models.DecimalField(
        'Points Value',
        max_digits=4,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='1點等於多少元，例如 0.5 表示 1點=0.5元'
    )
    max_spending = models.DecimalField(
        'Maximum Merchant Reward Amount',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    start_date = models.DateField('Start Date', null=True, blank=True)
    end_date = models.DateField('End Date', null=True, blank=True)
    is_promotional = models.BooleanField(
        'Promotional Campaign',
        default=False,
        help_text='是否為限時促銷活動'
    )
    created_at = models.DateTimeField('Created At', auto_now_add=True)

    class Meta:
        db_table = 'merchant_rewards'
        verbose_name = 'Merchant Special Reward'
        verbose_name_plural = 'Merchant Special Rewards'
        ordering = ['card', 'merchant']
        indexes = [
            models.Index(fields=['merchant', 'card'], name='merchant_rewards_idx'),
            models.Index(fields=['start_date', 'end_date'], name='merchant_rewards_date_idx'),
        ]

    def __str__(self):
        # 回傳：信用卡名 - 商家名稱: 回饋趴數%
        rate = self.rate or self.category.rate
        return f"{self.card.name} @ {self.merchant.name}: {rate}%"
    
    @property
    def effective_rate(self):
        #有效回饋率
        rate = self.rate or self.category.rate
        reward_type = self.reward_type or self.category.reward_type
        points_value = self.points_value or self.category.points_value
        
        # 現金回饋率
        if reward_type == RewardCategory.RewardType.CASHBACK:
            return rate
        # 點數回饋率
        elif reward_type in [RewardCategory.RewardType.POINTS, RewardCategory.RewardType.LINEPAY] and points_value:
            return rate * points_value
        else:
            return rate
    
    @property
    def is_active(self):
        # 檢查回饋規則是否在有效期間內
        today = timezone.now().date()
        
        if self.start_date and today < self.start_date:
            return False
        
        if self.end_date and today > self.end_date:
            return False
        
        return True