.PHONY: install migrate convert build dev start selfcheck lint check 

MANAGE := poetry run python manage.py

install:
	poetry install --no-root


migrate:
	$(MANAGE) migrate

convert:
	$(MANAGE) collectstatic --no-input

build: install convert migrate

dev:
	$(MANAGE) runserver localhost:8050

create_superuser:
	$(MANAGE) createsuperuser

PORT ?= 8000
start:
	$(MANAGE) runserver 0.0.0.0:$(PORT)

selfcheck:
	poetry check

lint:
	poetry run flake8 hh_app --exclude=*migrations/

check: selfcheck lint
