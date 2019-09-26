clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

update: backup install migrate static

# Perform database migrations (after schema changes are made)
migrate:
	cd InvenTree && python3 manage.py makemigrations
	cd InvenTree && python3 manage.py migrate
	cd InvenTree && python3 manage.py migrate --run-syncdb
	cd InvenTree && python3 manage.py check

# Collect static files into the correct locations
static:
	cd InvenTree && python3 manage.py collectstatic

# Install all required packages
install:
	pip3 install -U -r requirements.txt
	cd InvenTree && python3 setup.py

# Create a superuser account
superuser:
	cd InvenTree && python3 manage.py createsuperuser

# Install pre-requisites for mysql setup
mysql:
	apt-get install mysql-server libmysqlclient-dev
	pip3 install mysqlclient

# Install pre-requisites for postgresql setup
postgresql:
	apt-get install postgresql postgresql-contrib libpq-dev
	pip3 install psycopg2

# Update translation files
translate:
	cd InvenTree && python3 manage.py makemessages
	cd InvenTree && python3 manage.py compilemessages

# Run PEP style checks against source code
style:
	flake8 InvenTree

# Run unit tests
test:
	cd InvenTree && python3 manage.py check
	cd InvenTree && python3 manage.py test build common company order part stock 

# Run code coverage
coverage:
	cd InvenTree && python3 manage.py check
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
	cd InvenTree && python3 manage.py dbbackup
	cd InvenTree && python3 manage.py mediabackup

.PHONY: clean migrate superuser install mysql postgresql translate static style test coverage docreqs docs backup update