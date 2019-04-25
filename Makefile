clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

style:
	flake8 InvenTree --ignore=C901,E501

test:
	python InvenTree/manage.py check
	python InvenTree/manage.py test build company part stock

migrate:
	python InvenTree/manage.py makemigrations company
	python InvenTree/manage.py makemigrations part
	python InvenTree/manage.py makemigrations stock
	python InvenTree/manage.py makemigrations build
	python InvenTree/manage.py migrate --run-syncdb
	python InvenTree/manage.py check

install:
	pip install -U -r requirements.txt
	
	# Generate a secret key
	python InvenTree/key.py

setup: install migrate

coverage:
	python InvenTree/manage.py check
	coverage run InvenTree/manage.py test build company part stock
	coverage html

superuser:
	python InvenTree/manage.py createsuperuser
