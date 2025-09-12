#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=Rewardia.settings

echo "=== Docker 容器啟動開始 ==="
echo "時間: $(TZ=Asia/Taipei date)"

echo "等待 PostgreSQL 服務啟動..."
until pg_isready -h rewardia-postgres -p 5432 -U postgres > /dev/null 2>&1; do
    echo "PostgreSQL 尚未就緒，等待中..."
    sleep 2
done
echo "PostgreSQL 服務已就緒"

echo "等待 Redis 服務啟動..."
until redis-cli -h rewardia-redis ping > /dev/null 2>&1; do
    echo "Redis 尚未就緒，等待中..."
    sleep 2
done
echo "Redis 服務已就緒"

echo "檢查 Django 版本..."
python -m django --version

echo "執行資料庫遷移..."
if python manage.py migrate --run-syncdb --verbosity=2; then
    echo "資料庫遷移成功"
else
    echo "資料庫遷移失敗"
    exit 1
fi

echo "檢查資料庫連線..."
if python manage.py check --database default; then
    echo "資料庫連線檢查通過"
else
    echo "資料庫連線檢查失敗"
    exit 1
fi

echo "=== 所有初始化步驟完成 ==="
echo "啟動 Supervisor 管理所有服務..."
echo "時間: $(TZ=Asia/Taipei date)"

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
echo "時間: $(TZ=Asia/Taipei date)"