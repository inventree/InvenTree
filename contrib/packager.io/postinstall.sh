#!/bin/bash
#
# packager.io postinstall script
#
PATH=${APP_HOME}/env/bin:${APP_HOME}/:/sbin:/bin:/usr/sbin:/usr/bin:

# default config
export CONF_DIR=/etc/inventree
export DATA_DIR=${APP_HOME}/data
export INVENTREE_MEDIA_ROOT=${DATA_DIR}/media
export INVENTREE_STATIC_ROOT=${DATA_DIR}/static
export INVENTREE_PLUGINS_ENABLED=true
export INVENTREE_PLUGIN_FILE=${CONF_DIR}/plugins.txt
export INVENTREE_CONFIG_FILE=${CONF_DIR}/config.yaml
export INVENTREE_SECRET_KEY_FILE=${CONF_DIR}/secret_key.txt
export INVENTREE_DB_NAME=${DATA_DIR}/database.sqlite3
export INVENTREE_DB_ENGINE=sqlite3

# Setup variables
export SETUP_NGINX_FILE=/etc/nginx/sites-enabled/inventree.conf
export SETUP_ADMIN_PASSWORD_FILE=${CONF_DIR}/admin_password.txt
export SETUP_NO_CALLS=${SETUP_NO_CALLS:-no}
# Envs that should be passed to setup commands
export SETUP_ENVS=PATH,APP_HOME,INVENTREE_MEDIA_ROOT,INVENTREE_STATIC_ROOT,INVENTREE_PLUGINS_ENABLED,INVENTREE_PLUGIN_FILE,INVENTREE_CONFIG_FILE,INVENTREE_SECRET_KEY_FILE,INVENTREE_DB_NAME,INVENTREE_DB_ENGINE,INVENTREE_ADMIN_USER,INVENTREE_ADMIN_EMAIL,INVENTREE_ADMIN_PASSWORD

# import functions
. ${APP_HOME}/contrib/packager.io/functions.sh

# get base info
detect_docker
detect_initcmd
detect_ip

# create processes
create_initscripts
create_admin

# run updates
stop_inventree
update_or_install
set_env
start_inventree

# show info
final_message
