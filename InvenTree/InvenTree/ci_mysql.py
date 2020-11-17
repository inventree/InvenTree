"""
Configuration file for running tests against a MySQL database.
"""

from InvenTree.settings import *

# Override the 'test' database
if 'test' in sys.argv:
    print('InvenTree: Running tests - Using MySQL test database')
    
    DATABASES['default'] = {
        # Ensure mysql backend is being used
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'inventree_test_db',
        'USER': 'travis',
        'PASSWORD': '',
        'HOST': '127.0.0.1'
    }
