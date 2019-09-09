clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

update: backup install migrate

# Perform database migrations (after schema changes are made)
migrate:
	python3 InvenTree/manage.py makemigrations common
	python3 InvenTree/manage.py makemigrations company
	python3 InvenTree/manage.py makemigrations part
	python3 InvenTree/manage.py makemigrations stock
	python3 InvenTree/manage.py makemigrations build
	python3 InvenTree/manage.py makemigrations order
	python3 InvenTree/manage.py makemigrations
	cd InvenTree && python3 manage.py migrate
	cd InvenTree && python3 manage.py migrate --run-syncdb
	python3 InvenTree/manage.py check
	cd InvenTree && python3 manage.py collectstatic

# Install all required packages
install:
	pip3 install -U -r requirements.txt
	python3 InvenTree/setup.py

# Create a superuser account
superuser:
	python3 InvenTree/manage.py createsuperuser

# Install pre-requisites for mysql setup
mysql:
	apt-get install mysql-server libmysqlclient-dev
	pip3 install mysqlclient

# Install pre-requisites for postgresql setup
postgresql:
	apt-get install postgresql postgresql-contrib libpq-dev
	pip3 install psycopg2

# Run PEP style checks against source code
style:
	flake8 InvenTree

# Run unit tests
test:
	python3 InvenTree/manage.py check
	python3 InvenTree/manage.py test build common company order part stock 

# Run code coverage
coverage:
	python3 InvenTree/manage.py check
	coverage run InvenTree/manage.py test build common company order part stock InvenTree
	coverage html

# Install packages required to generate code docs
docreqs:
	pip3 install -U -r docs/requirements.txt

# Build code docs
docs:
	cd docs && make html

# Make database backup
backup:
	python3 InvenTree/manage.py dbbackup
	python3 InvenTree/manage.py mediabackup

.PHONY: clean migrate superuser install mysql postgresql style test coverage docreqs docs backup update