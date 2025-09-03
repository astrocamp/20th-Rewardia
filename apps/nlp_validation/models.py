from django.db import models
from django.core.validators import MinValueValidator


class AnalysisStatistics(models.Model):
    total_time = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        validators=[MinValueValidator(0)],
    )
    analyzed_count = models.PositiveIntegerField()
    average_time = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        validators=[MinValueValidator(0)],
    )
    errors = models.JSONField(
        default=dict,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analysis_statistics"
        verbose_name = "分析統計"
        verbose_name_plural = "分析統計"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"], name="analysis_stats_date_idx"),
        ]

    def __str__(self):
        return f"分析統計 {self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.analyzed_count}項 ({self.total_time:.3f}秒)"
