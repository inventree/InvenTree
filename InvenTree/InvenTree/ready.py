import sys


def canAppAccessDatabase():
    """
    Returns True if the apps.py file can access database records.

    There are some circumstances where we don't want the ready function in apps.py
    to touch the database
    """

    # If any of the following management commands are being executed,
    # prevent custom "on load" code from running!
    excluded_commands = [
        'flush',
        'loaddata',
        'dumpdata',
        'makemirations',
        'migrate',
        'check',
        'mediarestore',
        'shell',
        'createsuperuser',
        'wait_for_db',
        'prerender',
        'collectstatic',
        'makemessages',
        'compilemessages',
    ]

    for cmd in excluded_commands:
        if cmd in sys.argv:
            return False

    return True
