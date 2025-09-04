# Generated manually for PendingReward model updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingreward',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', '待審核'), 
                    ('REVIEWING', '審核中'), 
                    ('APPROVED', '已通過'), 
                    ('REJECTED', '已拒絕')
                ], 
                default='PENDING', 
                max_length=10, 
                verbose_name='審核狀態'
            ),
        ),
        migrations.AddField(
            model_name='pendingreward',
            name='soft_deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='軟刪除時間'),
        ),
    ]
