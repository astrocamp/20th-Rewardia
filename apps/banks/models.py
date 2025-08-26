from django.db import models

# Create your models here.


# 銀行資訊
class Bank(models.Model):
    name = models.CharField("Bank Name", max_length=50)
    code = models.CharField(
        "Bank Code", max_length=10, unique=True, blank=True, null=True
    )
    logo_url = models.URLField("Logo URL", blank=True, null=True)
    website_url = models.URLField("URL", blank=True, null=True)
    is_active = models.BooleanField("Is Active", default=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        db_table = "banks"
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    # 該銀行發行的信用卡數量
    # 可以用 Banks.credit_cards_count 獲得資料
    def credit_cards_count(self):
        return self.credit_cards.filter(is_active=True).count()
