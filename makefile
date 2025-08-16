runserver:
	uv run python manage.py runserver

makemigrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

shell:
	uv run python manage.py shell

sqlstatus:
	brew services list

sqlstop:
	brew services stop postgresql@16

sqlstart:
	brew services start postgresql@16

# ----------------菜雞安裝請注意看-----------------
# windows => https://www.enterprisedb.com/downloads/postgres-postgresql-downloads (下載16版)
# 1. 先執行下面make指令
sqlinstall:
	brew install pgadmin4 && brew install postgresql@16 && brew services start postgresql@16 && createuser -s postgres && psql -U postgres
# windows 開啟 PostgreSQL server 沒意外再終端機輸入 psql -U postgres 後就可以從2開始了
# 2. 如果都沒問題應該會看到 "postgres=# "
# 3. 在"postgres=# "輸入 CREATE DATABASE rewardia_db; //;<-分號很重要請放在尾巴輸入
# 4. 如果想用預設(超級)帳號的話帳密都是postgres
# 4-1. 如不想使用預設帳號可以另外新增帳密，在"postgres=# "輸入 CREATE USER 「帳號」 WITH PASSWORD '「密碼」'; //;<-分號很重要請放在尾巴輸入
# 4-2. ALTER SCHEMA public OWNER TO 「帳號」;
# 5. 在"postgres=# "輸入 psql -U 「帳號」 -d my_database 出現 "rewardia_db=>" 表示成功 退出可以輸入 \q
# PS. .pg_service.conf 的 user 與 .pg_db_pass的 DBUSER:PASSWORD(帳號:密碼) 務必跟自己填的相同 以下預設為例
# EX. .pg_service.conf 的 user = postgres / .pg_db_pass的 (DBUSER:PASSWORD) = postgres:postgres
# PS2. make sqlinstall 有下載官方GUI軟體 pAgadmin4 沒意外可以直接完成以上動作可以試試看