#!/bin/bash
#
# packager.io preinstall/preremove script
#
PATH=${APP_HOME}/env/bin:${APP_HOME}/:/sbin:/bin:/usr/sbin:/usr/bin:

# Envs that should be passed to setup commands
export SETUP_ENVS=PATH,APP_HOME,INVENTREE_MEDIA_ROOT,INVENTREE_STATIC_ROOT,INVENTREE_BACKUP_DIR,INVENTREE_PLUGINS_ENABLED,INVENTREE_PLUGIN_FILE,INVENTREE_CONFIG_FILE,INVENTREE_SECRET_KEY_FILE,INVENTREE_DB_ENGINE,INVENTREE_DB_NAME,INVENTREE_DB_USER,INVENTREE_DB_PASSWORD,INVENTREE_DB_HOST,INVENTREE_DB_PORT,INVENTREE_ADMIN_USER,INVENTREE_ADMIN_EMAIL,INVENTREE_ADMIN_PASSWORD,SETUP_NGINX_FILE,SETUP_ADMIN_PASSWORD_FILE,SETUP_NO_CALLS,SETUP_DEBUG,SETUP_EXTRA_PIP,SETUP_PYTHON

if test -f "${APP_HOME}/env/bin/pip"; then
  # Check if clear-generated is available
  if sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && invoke clear-generated --help" > /dev/null 2>&1; then
    echo "# Clearing precompiled files"
    sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && invoke clear-generated"
  else
    echo "# Clearing precompiled files - skipping"
  fi
else
  echo "# No python environment found - skipping"
fi
