from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CreditCard",
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
                ("name", models.TextField(verbose_name="信用卡名稱")),
                ("bank", models.CharField(max_length=20, verbose_name="銀行名稱")),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Is Active"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated At"),
                ),
            ],
            options={
                "verbose_name": "Credit Card",
                "verbose_name_plural": "Credit Cards",
                "db_table": "credit_cards",
                "indexes": [
                    models.Index(
                        fields=["bank", "is_active"], name="cards_bank_active_idx"
                    )
                ],
            },
        ),
    ]
