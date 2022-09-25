#!/bin/bash
#
# packager.io postinstall script
#

PATH=/opt/inventree/:/sbin:/bin:/usr/sbin:/usr/bin:

# import functions
. /opt/inventree/contrib/packager.io/functions

# Activate python virtual environment
cd ${APP_HOME}
python3 -m venv virt
. virt/bin/active

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
