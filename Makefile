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
