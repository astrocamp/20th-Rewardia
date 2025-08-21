from django.db import models
from apps.banks.models import Bank
from apps.cards.models import CreditCard

# Create your models here.
class CrawledData(models.Model):
    name = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name='crawled_data',
        verbose_name='Credit Card'
    )
    bank = models.ForeignKey(
        Bank,
        on_delete=models.CASCADE,
        related_name='credit_cards_crawled_data',
        verbose_name='Issuing Bank'
    )
    content = models.TextField('Crawled Content',null=False)
    url = models.CharField('Crawled Website',null=False)
    created_at = models.DateTimeField('Created At', auto_now_add=True)

    class Meta:
        db_table = 'crawler_data'
        verbose_name = 'Crawled Card'
        verbose_name_plural = 'Crawled Cards'

    def __str__(self):
        return self.name