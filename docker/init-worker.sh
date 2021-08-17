#!/bin/sh
echo "InvenTreeWorker: Starting..."

if [[ -n "$INVENTREE_DEV_VENV" ]]; then
    echo "InvenTreeWorker: Sourcing a virtual env in ${INVENTREE_HOME}"
    cd $INVENTREE_HOME
    source ./dev/env/bin/activate
fi

# Wait for the database to be ready
cd $INVENTREE_MNG_DIR
echo "InvenTreeWorker: Waiting for DB"
python3 manage.py wait_for_db

echo "InvenTreeWorker: DB ready, sleeping 10"
sleep 10

echo "InvenTreeWorker: Ready for CMD"

exec "$@"
