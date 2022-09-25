web: cd ${APP_HOME} && ${APP_HOME}/env/bin/gunicorn -c gunicorn.conf.py InvenTree.wsgi -b 127.0.0.1:8000
worker: cd ${APP_HOME} && source env/bin/activate && inv worker