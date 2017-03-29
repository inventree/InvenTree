import subprocess

subprocess.call(['pep8', '--exclude=migrations', '--ignore=EC04,W293,E501', 'InvenTree'])