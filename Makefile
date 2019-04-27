clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

migrate:
	python InvenTree/manage.py makemigrations company
	python InvenTree/manage.py makemigrations part
	python InvenTree/manage.py makemigrations stock
	python InvenTree/manage.py makemigrations build
	python InvenTree/manage.py migrate --run-syncdb
	python InvenTree/manage.py check

install:
	pip install -U -r requirements.txt
	python InvenTree/keygen.py

superuser:
	python InvenTree/manage.py createsuperuser

style:
	flake8 InvenTree

test:
	python InvenTree/manage.py check
	python InvenTree/manage.py test build company part stock

coverage:
	python InvenTree/manage.py check
	coverage run InvenTree/manage.py test build company part stock
	coverage html

documentation:
	pip install -U -r docs/requirements.txt
	cd docs & make html

