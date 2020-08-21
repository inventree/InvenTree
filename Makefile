clean:
	find . -path '*/__pycache__/*' -delete
	find . -type d -name '__pycache__' -empty -delete
	find . -name *.pyc -o -name *.pyo -delete
	rm -rf *.egg-info
	rm -rf .cache
	rm -rf .tox
	rm -f .coverage

# Create a superuser account
superuser:
	cd InvenTree && python3 manage.py createsuperuser

# Install pre-requisites for mysql setup
mysql:
	sudo apt-get install mysql-server libmysqlclient-dev
	pip3 install mysqlclient

# Install pre-requisites for postgresql setup
postgresql:
	sudo apt-get install postgresql postgresql-contrib libpq-dev
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
	cd InvenTree && python3 manage.py test barcode build common company label order part report stock InvenTree


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
