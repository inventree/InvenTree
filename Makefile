clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

# Perform database migrations (after schema changes are made)
migrate:
	python3 InvenTree/manage.py makemigrations company
	python3 InvenTree/manage.py makemigrations part
	python3 InvenTree/manage.py makemigrations stock
	python3 InvenTree/manage.py makemigrations build
	python3 InvenTree/manage.py makemigrations order
	python3 InvenTree/manage.py migrate --run-syncdb
	python3 InvenTree/manage.py check

# Install all required packages
install:
	pip3 install -U -r requirements.txt

# Perform initial database setup
setup:
	python3 InvenTree/setup.py
	$(MAKE) migrate
	$(MAKE) superuser

# Create a superuser account
superuser:
	python3 InvenTree/manage.py createsuperuser

# Install pre-requisites for mysql setup
mysql:
	apt-get install mysql-server
	apt-get install libmysqlclient-dev
	pip3 install mysqlclient

# Run PEP style checks against source code
style:
	flake8 InvenTree

# Run unit tests
test:
	python3 InvenTree/manage.py check
	python3 InvenTree/manage.py test build company part stock order

# Run code coverage
coverage:
	python3 InvenTree/manage.py check
	coverage run InvenTree/manage.py test build company part stock order InvenTree
	coverage html

# Install packages required to generate code docs
docreqs:
	pip3 install -U -r docs/requirements.txt

# Build code docs
documentation:
	cd docs && make html

# Make database backup
backup:
	python3 InvenTree/manage.py dbbackup
	python3 InvenTree/manage.py mediabackup

.PHONY: clean migrate requirements setup superuser install mysql style test coverage docreqs documentation backup