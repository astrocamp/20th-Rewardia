#!/bin/bash
set -e

echo "等待服務啟動..."
sleep 15

echo "執行資料庫遷移..."
python manage.py migrate --verbosity=2

echo "收集靜態檔案..."
python manage.py collectstatic --noinput --verbosity=2

echo "檢查服務狀態..."
python manage.py check

echo "確保 Django 完全載入..."
python manage.py shell -c "from django.apps import apps; print('Django apps loaded:', apps.ready)"

echo "啟動所有服務..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf