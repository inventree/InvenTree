clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

style:
	flake8

test:
	python InvenTree/manage.py check
	python InvenTree/manage.py test --noinput

migrate:
	python InvenTree/manage.py makemigrations company
	python InvenTree/manage.py makemigrations part
	python InvenTree/manage.py makemigrations stock
	python InvenTree/manage.py makemigrations build
	python InvenTree/manage.py migrate --run-syncdb
	python InvenTree/manage.py check

install:
	# TODO: replace this with a proper setup.py
	pip install -U -r requirements/base.txt

setup: install migrate

setup_ci:
	pip install -U -r requirements/build.txt

develop:
	pip install -U -r requirements/dev.txt

superuser:
	python InvenTree/manage.py createsuperuser
