web: env/bin/gunicorn --chdir $APP_HOME/InvenTree -c InvenTree/gunicorn.conf.py InvenTree.wsgi -b 0.0.0.0:$PORT
worker: env/bin/python InvenTree/manage.py qcluster
