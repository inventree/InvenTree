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

requirements:
	pip3 install -U -r requirements.txt

setup:
	python3 InvenTree/setup.py

superuser:
	python3 InvenTree/manage.py createsuperuser

install: requirements setup migrate superuser

mysql:
	apt-get install mysql-server
	apt-get install libmysqlclient-dev
	pip3 install mysqlclient

style:
	flake8 InvenTree

test:
	python3 InvenTree/manage.py check
	python3 InvenTree/manage.py test build company part stock order

coverage:
	python3 InvenTree/manage.py check
	coverage run InvenTree/manage.py test build company part stock order InvenTree
	coverage html

documentation:
	pip3 install -U -r docs/requirements.txt
	cd docs & make html

backup:
	python3 InvenTree/manage.py dbbackup
	python3 InvenTree/manage.py mediabackup

.PHONY: clean migrate requirements setup superuser install mysql style test coverage documentation backup