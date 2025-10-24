import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AnalysisStatistics",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "total_time",
                    models.DecimalField(
                        decimal_places=3,
                        max_digits=8,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("analyzed_count", models.PositiveIntegerField()),
                (
                    "average_time",
                    models.DecimalField(
                        decimal_places=3,
                        max_digits=8,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
                ("errors", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "分析統計",
                "verbose_name_plural": "分析統計",
                "db_table": "analysis_statistics",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["-created_at"], name="analysis_stats_date_idx")
                ],
            },
        ),
    ]
