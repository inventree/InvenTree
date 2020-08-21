# -*- coding: utf-8 -*-

from invoke import task

import os

def localDir():
    """
    Returns the directory of *THIS* file.
    Used to ensure that the various scripts always run
    in the correct directory.
    """
    return os.path.dirname(os.path.abspath(__file__))

def managePyDir():
    """
    Returns the directory of the manage.py file
    """

    return os.path.join(localDir(), 'InvenTree')

def managePyPath():
    """
    Return the path of the manage.py file
    """

    return os.path.join(managePyDir, 'manage.py')

def manage(c, cmd):
    """
    Runs a given command against django's "manage.py" script.

    Args:
        c - Command line context
        cmd - django command to run
    """

    c.run('cd {path} && python3 manage.py {cmd}'.format(
        path=managePyDir(),
        cmd=cmd
    ))

@task
def migrate(c):
    """
    Performs database migrations.
    This is a critical step if the database schema have been altered!
    """

    print("Running InvenTree database migrations...")
    print("========================================")

    manage(c, "makemigrations")
    manage(c, "migrate")
    manage(c, "migrate --run-syncdb")
    manage(c, "check")

    print("========================================")
    print("InvenTree database migrations completed!")

@task
def test(c):
    print("hello!")