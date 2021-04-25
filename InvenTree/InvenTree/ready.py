import sys

def canAppAccessDatabase():
    """
    Returns True if the apps.py file can access database records.

    There are some circumstances where we don't want the ready function in apps.py
    to touch the database:

    - "flush" command
    - "loaddata" command
    - "migrate" command
    """

    if 'flush' in sys.argv:
        return False
    
    if 'loaddata' in sys.argv:
        return False

    if 'migrate' in sys.argv:
        return False

    return True
