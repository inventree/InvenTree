clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

migrate:
	python3 InvenTree/manage.py makemigrations company
	python3 InvenTree/manage.py makemigrations part
	python3 InvenTree/manage.py makemigrations stock
	python3 InvenTree/manage.py makemigrations build
	python3 InvenTree/manage.py makemigrations order
	python3 InvenTree/manage.py migrate --run-syncdb
	python3 InvenTree/manage.py check

install:
	pip3 install -U -r requirements.txt
	python3 InvenTree/keygen.py

superuser:
	python3 InvenTree/manage.py createsuperuser

style:
	flake8 InvenTree

test:
	python3 InvenTree/manage.py check
	python3 InvenTree/manage.py test build company part stock order

coverage:
	python3 InvenTree/manage.py check
	coverage run InvenTree/manage.py test build company part stock order
	coverage html

documentation:
	pip3 install -U -r docs/requirements.txt
	cd docs & make html

backup:
	python3 InvenTree/manage.py dbbackup
	python3 InvenTree/manage.py mediabackup