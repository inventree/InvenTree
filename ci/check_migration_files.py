""" Check that there are no database migration files which have not been committed. """

import sys
import subprocess

print("Checking for unstaged migration files...")

cmd = ['git', 'ls-files', '--exclude-standard', '--others']

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

out, err = proc.communicate()

migrations = []

for line in str(out.decode()).split('\n'):
    if '/migrations/' in line:
        migrations.append(line)

if len(migrations) == 0:
    sys.exit(0)

print("There are {n} unstaged migration files:".format(n=len(migrations)))

for m in migrations:
    print(" - {m}".format(m=m))

sys.exit(len(migrations))
