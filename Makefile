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
	# Perform Django system checks
	python InvenTree/manage.py check

	# Run the test framework (through coverage script)
	coverage run InvenTree/manage.py test

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
	
	# Generate a secret key
	python InvenTree/key.py

setup: install migrate

setup_ci:
	pip install -U -r requirements/build.txt

superuser:
	python InvenTree/manage.py createsuperuser
