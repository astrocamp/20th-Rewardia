from django.db import models

# Create your models here.

# 商家分類選擇
class Merchant(models.Model):
    # 商家/通路資訊
    
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
    
    name = models.CharField('商家名稱', max_length=100)
    domain = models.URLField('網域名稱', blank=True, help_text='用於 Chrome 擴展識別')
    category = models.CharField(
        '主要分類', 
        max_length=10, 
        choices=Category.choices,
        default=Category.OTHER
    )
    secondary_category = models.CharField('次要分類', max_length=30, blank=True)
    merchant_code = models.CharField(
        '商家代碼', 
        max_length=10, 
        unique=True, 
        blank=True,
        help_text='與銀行系統對接用'
    )
    logo_url = models.URLField('Logo URL', blank=True)
    is_active = models.BooleanField('是否啟用', default=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)

    def __str__(self):
        return self.name
    
    @property
    # 取得分類的中文顯示
    # 可以用 merchants.category_display得到分類中文顯示
    def category_display(self):
        return self.get_category_display()