#!/bin/bash
#
# packager.io postinstall script
#
PATH=/opt/inventree/env/bin:/opt/inventree/:/sbin:/bin:/usr/sbin:/usr/bin:

cd ${APP_HOME}
python3 -m venv env

# default config
INVENTREE_MEDIA_ROOT=/opt/inventree/data/media
INVENTREE_STATIC_ROOT=/opt/inventree/data/static
INVENTREE_PLUGIN_FILE=/opt/inventree/data/plugins.txt
INVENTREE_CONFIG_FILE=/opt/inventree/data/config.yaml

# import functions
. /opt/inventree/contrib/packager.io/functions

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
