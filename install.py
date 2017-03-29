from __future__ import print_function

import subprocess

def manage(*arg):
    args = ["python", "InvenTree/manage.py"]

    for a in arg:
        args.append(a)

    subprocess.call(args)

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

print("\n\nAdmin account:\nIf a superuser is not already installed,")
print("run the command 'python InvenTree/manage.py createsuperuser'")
