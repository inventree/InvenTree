#!/bin/bash
#
# packager.io postinstall script
#
PATH=/opt/inventree/env/bin:/opt/inventree/:/sbin:/bin:/usr/sbin:/usr/bin:

cd ${APP_HOME}
python -m venv env

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
