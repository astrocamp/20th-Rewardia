from django.db import models
from apps.cards.models import CreditCard

# Create your models here.
class CrawledData(models.Model):
    card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        related_name='crawled_data',
        verbose_name='Credit Card'
    )
    content = models.TextField('Crawled Content',null=False)
    url = models.URLField('Crawled Website',null=False)
    url_domain = models.URLField('Crawled Main Source', default=)
    created_at = models.DateTimeField('Created At', auto_now_add=True)

    class Meta:
        db_table = 'crawler_data'
        verbose_name = 'Crawled Card'
        verbose_name_plural = 'Crawled Cards'

    def __str__(self):
        return self.card.name