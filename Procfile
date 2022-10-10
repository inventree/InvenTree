web: env/bin/gunicorn -c gunicorn.conf.py InvenTree.wsgi -b 0.0.0..:$PORT
worker: env/bin/python InvenTree/manage.py qcluster
