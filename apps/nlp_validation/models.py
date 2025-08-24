from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class ValidationRule(models.Model):
    """NLP 驗證規則 """
    
    # 基本資訊
    name = models.CharField('Rule Name', max_length=100, help_text='規則名稱')
    description = models.TextField('Description', blank=True, help_text='規則描述')
    is_active = models.BooleanField('Is Active', default=True, help_text='啟用狀態')
    created_at = models.DateTimeField('Created At', auto_now_add=True, help_text='建立時間')
    

class ValidationResult(models.Model):
    """ NLP 驗證結果記錄 """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', '待處理'
        RUNNING = 'RUNNING', '執行中'
        COMPLETED = 'COMPLETED', '已完成'
        FAILED = 'FAILED', '失敗'
    
    class ResultType(models.TextChoices):
        PASS = 'PASS', '通過'
        WARNING = 'WARNING', '警告'
        ERROR = 'ERROR', '錯誤'
        INFO = 'INFO', '資訊'
    
    # 驗證狀態
    status = models.CharField(
        'Status',
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        help_text='執行狀態'
    )
    result_type = models.CharField(
        'Result Type',
        max_length=10,
        choices=ResultType.choices,
        help_text='結果類型'
    )
    
    # 驗證結果
    score = models.DecimalField(
        'Score',
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text='驗證分數/信心度 (0-1)'
    )
    passed = models.BooleanField('Passed', default=False, help_text='是否通過')
    
    # 詳細結果
    message = models.TextField('Message', blank=True, help_text='驗證訊息')
    details = models.JSONField(
        'Details',
        default=dict,
        help_text='''詳細結果 - 存放提取的信用卡資訊
        預計格式: {
            "extracted_info": {
                "foreign_cashback": 2.8,
                "merchant_momo": 5.3,
                "annual_fee": 2000
            },
            "original_text": "海外消費2.8%回饋，momo購物5.3%",
            "confidence_scores": {
                "foreign_cashback": 0.95,
                "momo": 0.87
            }
        }'''
    )
    
    # 時間戳記
    created_at = models.DateTimeField('Created At', auto_now_add=True, help_text='建立時間')
    started_at = models.DateTimeField('Started At', null=True, blank=True, help_text='開始時間')
    completed_at = models.DateTimeField('Completed At', null=True, blank=True, help_text='完成時間')

class ValidationSession(models.Model):
    """ 批次驗證的記錄 """
    
    class SessionType(models.TextChoices):
        MANUAL = 'MANUAL', '手動觸發'
        SCHEDULED = 'SCHEDULED', '排程執行'
        AUTO = 'AUTO', '自動觸發'
        API = 'API', 'API 呼叫'
    
    class Status(models.TextChoices):
        RUNNING = 'RUNNING', '執行中'
        COMPLETED = 'COMPLETED', '已完成'
        FAILED = 'FAILED', '失敗'
        CANCELLED = 'CANCELLED', '已取消'
    
    # 會話資訊
    session_id = models.CharField('Session ID', max_length=50, unique=True, help_text='會話ID')
    session_type = models.CharField(
        'Session Type',
        max_length=10,
        choices=SessionType.choices,
        default=SessionType.MANUAL,
        help_text='會話類型'
    )
    name = models.CharField('Name', max_length=100, help_text='會話名稱')
    status = models.CharField(
        'Status',
        max_length=10,
        choices=Status.choices,
        default=Status.RUNNING,
        help_text='會話狀態'
    )
    
    # 基本統計
    total_items = models.PositiveIntegerField('Total Items', default=0, help_text='總處理項目數')
    completed_items = models.PositiveIntegerField('Completed Items', default=0, help_text='已完成項目數')
    failed_items = models.PositiveIntegerField('Failed Items', default=0, help_text='失敗項目數')
    
    # 時間記錄
    started_at = models.DateTimeField('Started At', auto_now_add=True, help_text='開始時間')
    completed_at = models.DateTimeField('Completed At', null=True, blank=True, help_text='完成時間')