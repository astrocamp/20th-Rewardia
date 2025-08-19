from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from banks.models import Bank

# Create your models here.
class CreditCard(models.Model):
    # 信用卡資訊
    
    # 卡片網路選擇
    class CardNetwork(models.TextChoices):
        VISA = 'VISA', 'Visa'
        MASTERCARD = 'MC', 'MasterCard'
        JCB = 'JCB', 'JCB'
        AMEX = 'AMEX', 'American Express'
        UNION_PAY = 'UP', '銀聯'
    
    # 卡片等級選擇
    class CardType(models.TextChoices):
        CLASSIC = 'CLASSIC', '一般卡'
        GOLD = 'GOLD', '金卡'
        PLATINUM = 'PLATINUM', '白金卡'
        INFINITE = 'INFINITE', '無限卡'
        TITANIUM = 'TITANIUM', '鈦金卡'
        WORLD = 'WORLD', '世界卡'
        SIGNATURE = 'SIGNATURE','御璽卡'
        BUSINESS = 'BUSINESS', '商務卡'
        SIGBUSINESS = 'SIGBUSINESS', '商務御璽卡'

    
    name = models.CharField('信用卡名稱', max_length=100)
    bank = models.ForeignKey(
        Bank,
        on_delete=models.CASCADE,
        related_name='credit_cards',
        verbose_name='發卡銀行'
    )
    annual_fee = models.DecimalField(
        '年費',
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    signup_bonus = models.IntegerField(
        '新戶禮',
        default=0,
        validators=[MinValueValidator(0)],
        help_text='新戶禮金額或點數'
    )
    credit_limit_min = models.IntegerField(
        '最低額度',
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    credit_limit_max = models.IntegerField(
        '最高額度',
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    apr_min = models.DecimalField(
        '最低利率',
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    apr_max = models.DecimalField(
        '最高利率',
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    foreign_transaction_fee = models.DecimalField(
        '海外交易手續費',
        max_digits=4,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='百分比，例如 1.5 表示 1.5%'
    )
    card_network = models.CharField(
        '卡片網路',
        max_length=20,
        choices=CardNetwork.choices
    )
    card_type = models.CharField(
        '卡片等級',
        max_length=20,
        choices=CardType.choices
    )
    is_active = models.BooleanField('是否啟用', default=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)