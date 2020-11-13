"""
Configuration file for running tests against a MySQL database.
"""

from InvenTree.settings import *

# Override the 'test' database
if 'test' in sys.argv:
    print('InvenTree: Running tests - Using PostGreSQL test database')
    
    DATABASES['default'] = {
        # Ensure postgresql backend is being used
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'inventree_test_db',
        'USER': 'postgres',
        'PASSWORD': '',
    }
