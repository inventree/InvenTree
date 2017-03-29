from __future__ import print_function

import subprocess
import argparse

def manage(*arg):
    args = ["python", "InvenTree/manage.py"]

    for a in arg:
        args.append(a)

    subprocess.call(args)

parser = argparse.ArgumentParser(description="Install InvenTree inventory management system")

parser.add_argument('-u', '--update', help='Update only, do not try to install required components', action='store_true')
    
args = parser.parse_args()

# If 'update' is specified, don't perform initial installation
if not args.update:
    # Install django requirements
    subprocess.call(["pip", "install", "django", "-q"])
    subprocess.call(["pip", "install", "djangorestframework", "-q"])

    # Initial database setup
    manage("migrate")

# Make migrations for all apps
manage("makemigrations", "part")
manage("makemigrations", "stock")
manage("makemigrations", "supplier")
manage("makemigrations", "project")
manage("makemigrations", "track")

# Update the database
manage("migrate")

# Check for errors
manage("check")

if not args.update:
    print("\n\nAdmin account:\nIf a superuser is not already installed,")
    print("run the command 'python InvenTree/manage.py createsuperuser'")
