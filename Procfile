# Web process: gunicorn
web: env/bin/gunicorn --chdir $APP_HOME/src/backend/InvenTree -c src/backend/InvenTree/gunicorn.conf.py InvenTree.wsgi -b 0.0.0.0:$PORT
# Worker process: qcluster
worker: env/bin/python src/backendInvenTree/manage.py qcluster
# Invoke commands
invoke: echo "" | echo "" && . env/bin/activate && invoke
# CLI: Provided for backwards compatibility
cli: echo "" | echo "" && . env/bin/activate && invoke
