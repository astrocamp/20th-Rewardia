import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Rewardia.settings")

# 確保 Django 設定已載入
import django
from django.conf import settings

if not settings.configured:
    django.setup()

app = Celery("Rewardia")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
