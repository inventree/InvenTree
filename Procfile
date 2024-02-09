# Web process: gunicorn
web: env/bin/gunicorn --chdir $APP_HOME/InvenTree -c InvenTree/gunicorn.conf.py InvenTree.wsgi -b 0.0.0.0:$PORT
# Worker process: qcluster
worker: env/bin/python InvenTree/manage.py qcluster
# Invoke commands
invoke: echo "" | echo "" && . env/bin/activate && invoke
# CLI: Provided for backwards compatibility
cli: echo "" | echo "" && . env/bin/activate && invoke
