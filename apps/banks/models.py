from django.db import models

# Create your models here.

# 銀行資訊
class Bank(models.Model):
    name = models.CharField('銀行名稱', max_length=50)
    code = models.CharField('銀行代碼', max_length=10, unique=True)
    logo_url = models.URLField('Logo URL', blank=True)
    website_url = models.URLField('官方網站', blank=True)
    is_active = models.BooleanField('是否啟用', default=True)
    created_at = models.DateTimeField('建立時間', auto_now_add=True)

    class Meta:
        db_table = 'banks'
        verbose_name = '銀行'
        verbose_name_plural = '銀行'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    @property
    # 該銀行發行的信用卡數量
    # 可以用 Banks.credit_cards_count 獲得資料
    def credit_cards_count(self):
        return self.credit_cards.filter(is_active=True).count()