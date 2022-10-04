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
export INVENTREE_PLUGIN_FILE=${CONF_DIR}/plugins.txt
export INVENTREE_CONFIG_FILE=${CONF_DIR}/config.yaml
export INVENTREE_SECRET_KEY_FILE=${CONF_DIR}/secret_key.txt
export INVENTREE_DB_NAME=${DATA_DIR}/database.sqlite3
export INVENTREE_DB_ENGINE=sqlite3
export INVENTREE_PLUGINS_ENABLED=true

# import functions
. ${APP_HOME}/contrib/packager.io/functions

# exec postinstall
debug
detect_os
detect_docker
detect_initcmd

create_initscripts

stop_inventree
update_or_install
set_env
start_inventree

final_message
