from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class ValidationRule(models.Model):
    """NLP 驗證規則定義"""
    
    class RuleType(models.TextChoices):
        # 實體識別規則
        ENTITY_EXTRACTION = 'ENTITY', '實體識別'
        # 文字相似度規則  
        TEXT_SIMILARITY = 'SIMILARITY', '文字相似度'
        # 資料完整性規則
        DATA_COMPLETENESS = 'COMPLETENESS', '資料完整性'
        # 格式驗證規則
        FORMAT_VALIDATION = 'FORMAT', '格式驗證'
        # 跨表關聯驗證
        CROSS_VALIDATION = 'CROSS', '跨表驗證'
        # 自定義規則
        CUSTOM = 'CUSTOM', '自定義規則'
    
    class Severity(models.TextChoices):
        LOW = 'LOW', '低'
        MEDIUM = 'MEDIUM', '中'
        HIGH = 'HIGH', '高'
        CRITICAL = 'CRITICAL', '嚴重'
    
    class TargetModel(models.TextChoices):
        # 目標模型選擇
        BANK = 'banks.Bank', '銀行'
        CREDIT_CARD = 'cards.CreditCard', '信用卡'
        MERCHANT = 'merchants.Merchant', '商家'
        REWARD_CATEGORY = 'rewards.RewardCategory', '回饋分類'
        MERCHANT_REWARD = 'rewards.MerchantReward', '商家回饋'
        ALL = 'ALL', '全部模型'
    
    # 基本資訊
    name = models.CharField('Rule Name', max_length=100, help_text='規則名稱')
    description = models.TextField('Description', blank=True, help_text='規則描述')
    rule_type = models.CharField(
        'Rule Type',
        max_length=20,
        choices=RuleType.choices,
        help_text='規則類型'
    )
    severity = models.CharField(
        'Severity',
        max_length=10,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        help_text='嚴重程度'
    )
    
    # 目標配置
    target_model = models.CharField(
        'Target Model',
        max_length=50,
        choices=TargetModel.choices,
        help_text='目標模型'
    )
    target_fields = models.JSONField(
        'Target Fields',
        default=list,
        help_text='目標欄位 - 要驗證的欄位列表，如 ["name", "description"]'
    )
    
    # 規則配置
    rule_config = models.JSONField(
        'Rule Config',
        default=dict,
        help_text='規則設定 - 規則的詳細設定參數'
    )
    
    # 閾值設定
    threshold = models.DecimalField(
        'Threshold',
        max_digits=5,
        decimal_places=3,
        default=0.80,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text='閾值 - 驗證閾值 (0-1)'
    )
    
    # 啟用狀態
    is_active = models.BooleanField('Is Active', default=True, help_text='啟用狀態')
    auto_fix = models.BooleanField(
        'Auto Fix',
        default=False,
        help_text='自動修復 - 是否嘗試自動修復發現的問題'
    )
    
    # 時間戳記
    created_at = models.DateTimeField('Created At', auto_now_add=True, help_text='建立時間')
    updated_at = models.DateTimeField('Updated At', auto_now=True, help_text='更新時間')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Created By',
        help_text='建立者'
    )
    
    class Meta:
        db_table = 'nlp_validation_rules'
        verbose_name = 'NLP 驗證規則'
        verbose_name_plural = 'NLP 驗證規則'
        ordering = ['severity', 'name']
        indexes = [
            models.Index(fields=['rule_type', 'is_active'], name='rules_type_active_idx'),
            models.Index(fields=['target_model'], name='rules_target_model_idx'),
            models.Index(fields=['severity'], name='rules_severity_idx'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
    
    @property
    def severity_color(self):
        """取得嚴重程度對應的顏色"""
        colors = {
            self.Severity.LOW: '#28a745',      # 綠色
            self.Severity.MEDIUM: '#ffc107',   # 黃色
            self.Severity.HIGH: '#fd7e14',     # 橘色
            self.Severity.CRITICAL: '#dc3545', # 紅色
        }
        return colors.get(self.severity, '#6c757d')


class ValidationResult(models.Model):
    """NLP 驗證結果記錄"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', '待處理'
        RUNNING = 'RUNNING', '執行中'
        COMPLETED = 'COMPLETED', '已完成'
        FAILED = 'FAILED', '失敗'
        SKIPPED = 'SKIPPED', '已跳過'
    
    class ResultType(models.TextChoices):
        PASS = 'PASS', '通過'
        WARNING = 'WARNING', '警告'
        ERROR = 'ERROR', '錯誤'
        INFO = 'INFO', '資訊'
    
    # 驗證規則關聯
    rule = models.ForeignKey(
        ValidationRule,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name='Validation Rule',
        help_text='驗證規則'
    )
    
    # 動態關聯到任何模型
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Content Type',
        help_text='內容類型'
    )
    object_id = models.PositiveIntegerField(
        'Object ID',
        null=True,
        blank=True,
        help_text='物件ID'
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
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
        help_text='驗證分數 - 驗證分數 (0-1)'
    )
    passed = models.BooleanField('Passed', default=False, help_text='是否通過')
    
    # 詳細結果
    message = models.TextField('Message', blank=True, help_text='驗證訊息')
    details = models.JSONField(
        'Details',
        default=dict,
        help_text='詳細結果 - 詳細的驗證結果，包含原始文字、實體識別結果等'
    )
    suggestions = models.JSONField(
        'Suggestions',
        default=list,
        help_text='修復建議 - 修復建議列表'
    )
    
    # NLP 處理結果
    extracted_entities = models.JSONField(
        'Extracted Entities',
        default=dict,
        help_text='提取實體 - spaCy 提取的實體結果'
    )
    similarity_scores = models.JSONField(
        'Similarity Scores',
        default=dict,
        help_text='相似度分數 - 與其他資料的相似度比較'
    )
    
    # 執行資訊
    execution_time = models.DecimalField(
        'Execution Time',
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='執行時間 - 執行時間 (秒)'
    )
    error_traceback = models.TextField(
        'Error Traceback',
        blank=True,
        help_text='錯誤追蹤 - 執行失敗時的錯誤訊息'
    )
    
    # 自動修復
    auto_fixed = models.BooleanField('Auto Fixed', default=False, help_text='自動修復')
    fix_applied = models.JSONField(
        'Fix Applied',
        default=dict,
        help_text='修復內容 - 自動修復的詳細內容'
    )
    
    # 時間戳記
    started_at = models.DateTimeField('Started At', null=True, blank=True, help_text='開始時間')
    completed_at = models.DateTimeField('Completed At', null=True, blank=True, help_text='完成時間')
    created_at = models.DateTimeField('Created At', auto_now_add=True, help_text='建立時間')
    
    class Meta:
        db_table = 'nlp_validation_results'
        verbose_name = 'NLP 驗證結果'
        verbose_name_plural = 'NLP 驗證結果'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rule', '-created_at'], name='results_rule_date_idx'),
            models.Index(fields=['status'], name='results_status_idx'),
            models.Index(fields=['result_type'], name='results_type_idx'),
            models.Index(fields=['content_type', 'object_id'], name='results_content_idx'),
            models.Index(fields=['passed'], name='results_passed_idx'),
            models.Index(fields=['-created_at'], name='results_created_idx'),
        ]
        # 避免重複驗證同一筆資料
        constraints = [
            models.UniqueConstraint(
                fields=['rule', 'content_type', 'object_id', 'created_at'],
                name='unique_rule_content_created'
            )
        ]
    
    def __str__(self):
        status_icon = {
            self.ResultType.PASS: '✅',
            self.ResultType.WARNING: '⚠️',
            self.ResultType.ERROR: '❌',
            self.ResultType.INFO: 'ℹ️',
        }
        icon = status_icon.get(self.result_type, '❓')
        return f"{icon} {self.rule.name} - {self.get_result_type_display()}"
    
    @property
    def duration(self):
        """計算驗證持續時間"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def is_completed(self):
        """檢查是否已完成"""
        return self.status in [self.Status.COMPLETED, self.Status.FAILED, self.Status.SKIPPED]
    
    @property
    def target_object_str(self):
        """取得目標物件的字串表示"""
        if self.content_object:
            return str(self.content_object)
        return f"{self.content_type} #{self.object_id}"
    
    def mark_started(self):
        """標記開始執行"""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, result_type, passed=False, score=None, message='', details=None):
        """標記完成並設定結果"""
        self.status = self.Status.COMPLETED
        self.result_type = result_type
        self.passed = passed
        self.score = score
        self.message = message
        self.details = details or {}
        self.completed_at = timezone.now()
        
        # 計算執行時間
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.execution_time = duration.total_seconds()
        
        self.save()
    
    def mark_failed(self, error_message, traceback=''):
        """標記執行失敗"""
        self.status = self.Status.FAILED
        self.result_type = self.ResultType.ERROR
        self.message = error_message
        self.error_traceback = traceback
        self.completed_at = timezone.now()
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.execution_time = duration.total_seconds()
        
        self.save()


class ValidationSession(models.Model):
    """驗證會話 - 批次驗證的記錄"""
    
    class SessionType(models.TextChoices):
        MANUAL = 'MANUAL', '手動觸發'
        SCHEDULED = 'SCHEDULED', '排程執行'
        AUTO = 'AUTO', '自動觸發'
        API = 'API', 'API 呼叫'
    
    # 會話資訊
    session_id = models.CharField('Session ID', max_length=50, unique=True, help_text='會話ID')
    session_type = models.CharField(
        'Session Type',
        max_length=10,
        choices=SessionType.choices,
        default=SessionType.MANUAL,
        help_text='會話類型'
    )
    name = models.CharField('Name', max_length=100, blank=True, help_text='會話名稱')
    description = models.TextField('Description', blank=True, help_text='會話描述')
    
    # 執行狀態
    total_rules = models.PositiveIntegerField('Total Rules', default=0, help_text='總規則數')
    completed_rules = models.PositiveIntegerField('Completed Rules', default=0, help_text='已完成規則數')
    failed_rules = models.PositiveIntegerField('Failed Rules', default=0, help_text='失敗規則數')
    
    total_objects = models.PositiveIntegerField('Total Objects', default=0, help_text='總物件數')
    processed_objects = models.PositiveIntegerField('Processed Objects', default=0, help_text='已處理物件數')
    
    # 統計結果
    pass_count = models.PositiveIntegerField('Pass Count', default=0, help_text='通過數')
    warning_count = models.PositiveIntegerField('Warning Count', default=0, help_text='警告數')
    error_count = models.PositiveIntegerField('Error Count', default=0, help_text='錯誤數')
    
    # 時間記錄
    started_at = models.DateTimeField('Started At', auto_now_add=True, help_text='開始時間')
    completed_at = models.DateTimeField('Completed At', null=True, blank=True, help_text='完成時間')
    
    # 觸發者
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Triggered By',
        help_text='觸發者'
    )
    
    class Meta:
        db_table = 'nlp_validation_sessions'
        verbose_name = 'NLP 驗證會話'
        verbose_name_plural = 'NLP 驗證會話'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at'], name='sessions_started_idx'),
            models.Index(fields=['session_type'], name='sessions_type_idx'),
        ]
    
    def __str__(self):
        return f"驗證會話 {self.session_id} ({self.get_session_type_display()})"
    
    @property
    def progress_percentage(self):
        """計算進度百分比"""
        if self.total_rules == 0:
            return 0
        return round((self.completed_rules / self.total_rules) * 100, 1)
    
    @property
    def is_completed(self):
        """檢查是否已完成"""
        return self.completed_at is not None
    
    @property
    def duration(self):
        """計算會話持續時間"""
        end_time = self.completed_at or timezone.now()
        return end_time - self.started_at
    
    def mark_completed(self):
        """標記會話完成"""
        self.completed_at = timezone.now()
        self.save(update_fields=['completed_at'])
    
    def update_progress(self):
        """更新進度統計"""
        results = ValidationResult.objects.filter(
            rule__in=self.results.values_list('rule', flat=True)
        )
        
        self.pass_count = results.filter(result_type=ValidationResult.ResultType.PASS).count()
        self.warning_count = results.filter(result_type=ValidationResult.ResultType.WARNING).count() 
        self.error_count = results.filter(result_type=ValidationResult.ResultType.ERROR).count()
        
        self.save(update_fields=['pass_count', 'warning_count', 'error_count'])


# 為了方便查詢，加入一些關聯
ValidationSession.add_to_class('results', models.ManyToManyField(
    ValidationResult, 
    through='ValidationSessionResult',
    verbose_name='驗證結果'
))


class ValidationSessionResult(models.Model):
    """驗證會話與結果的關聯表"""
    
    session = models.ForeignKey(
        ValidationSession,
        on_delete=models.CASCADE,
        verbose_name='Validation Session',
        help_text='驗證會話'
    )
    result = models.ForeignKey(
        ValidationResult,
        on_delete=models.CASCADE,
        verbose_name='Validation Result',
        help_text='驗證結果'
    )
    order = models.PositiveIntegerField('Order', default=0, help_text='執行順序')
    
    class Meta:
        db_table = 'nlp_validation_session_results'
        verbose_name = '會話結果關聯'
        verbose_name_plural = '會話結果關聯'
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'result'],
                name='unique_session_result'
            )
        ]