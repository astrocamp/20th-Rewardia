from django.db import models


# Create your models here.
class CrawledData(models.Model):
    content = models.TextField("Crawled Content", null=False)
    url = models.URLField("Crawled Website", default=None)
    is_active = models.BooleanField("Is Active", default=True)
    card_img = models.URLField("Card Image", blank=True, null=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)
    deleted_at = models.DateTimeField("Deleted At", blank=True, null=True)

    class Meta:
        db_table = "crawler_data"
        verbose_name = "Crawled Card"
        verbose_name_plural = "Crawled Cards"


class CrawledRecord(models.Model):
    total_time = models.DecimalField("Total Time", max_digits=8, decimal_places=3)
    total_cards = models.IntegerField("Total Cards")
    average_time = models.DecimalField("Average Time", max_digits=8, decimal_places=3)
    errors = models.JSONField("Failed Cards")
    created_at = models.DateTimeField("Created At", auto_now_add=True)
