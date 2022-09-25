#!/bin/bash
#
# packager.io postinstall script
#
PATH=${APP_HOME}/env/bin:${APP_HOME}/:/sbin:/bin:/usr/sbin:/usr/bin:

cd ${APP_HOME}
python3 -m venv env

# default config
export INVENTREE_MEDIA_ROOT=${APP_HOME}/data/media
export INVENTREE_STATIC_ROOT=${APP_HOME}/data/static
export INVENTREE_PLUGIN_FILE=${APP_HOME}/data/plugins.txt
export INVENTREE_CONFIG_FILE=${APP_HOME}/data/config.yaml
export INVENTREE_DB_ENGINE=sqlite3
export INVENTREE_DB_NAME=${APP_HOME}/data/database.sqlite3
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
start_inventree

final_message
