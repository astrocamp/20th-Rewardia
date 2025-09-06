from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CrawledData",
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
                ("content", models.TextField(verbose_name="Crawled Content")),
                ("url", models.URLField(default=None, verbose_name="Crawled Website")),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Is Active"),
                ),
                (
                    "card_img",
                    models.URLField(blank=True, null=True, verbose_name="Card Image"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated At"),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Deleted At"
                    ),
                ),
            ],
            options={
                "verbose_name": "Crawled Card",
                "verbose_name_plural": "Crawled Cards",
                "db_table": "crawler_data",
            },
        ),
        migrations.CreateModel(
            name="CrawledRecord",
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
                        decimal_places=3, max_digits=8, verbose_name="Total Time"
                    ),
                ),
                ("total_cards", models.IntegerField(verbose_name="Total Cards")),
                (
                    "average_time",
                    models.DecimalField(
                        decimal_places=3, max_digits=8, verbose_name="Average Time"
                    ),
                ),
                ("errors", models.JSONField(verbose_name="Failed Cards")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
            ],
        ),
    ]
