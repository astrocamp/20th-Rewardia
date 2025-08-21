test:
	uv run python manage.py test

check:
	uv run python manage.py check

collectstatic:
	uv run python manage.py collectstatic
	
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

sqlinstall_1:
	brew install pgadmin4 && brew install postgresql@16 && brew services start postgresql@16 && echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc

sqlinstall_2:
	createuser -s postgres && psql -U postgres

restart:
	npm i && uv run

ins_spacy:
	uv pip install pip && uv pip install https://github.com/explosion/spacy-models/releases/download/zh_core_web_md-3.7.0/zh_core_web_md-3.7.0-py3-none-any.whl