"""Check that there are no database migration files which have not been committed."""

import subprocess
import sys

print('Checking for unstaged migration files...')

cmd = ['git', 'ls-files', '--exclude-standard', '--others']

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

out, err = proc.communicate()

migrations = []

for line in str(out.decode()).split('\n'):
    if '/migrations/' in line:
        migrations.append(line)

if len(migrations) == 0:
    sys.exit(0)

print(f'There are {len(migrations)} unstaged migration files:')

for m in migrations:
    print(f' - {m}')

sys.exit(len(migrations))
