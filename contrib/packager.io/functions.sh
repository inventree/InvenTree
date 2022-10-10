#!/bin/bash
#
# packager.io postinstall script functions
#

function detect_docker() {
  if [ -n "$(grep docker < /proc/1/cgroup)" ]; then
    DOCKER="yes"
  else
    DOCKER="no"
  fi
}

function detect_initcmd () {
  if [ -n "$(which systemctl 2> /dev/null)" ]; then
    INIT_CMD="systemctl"
  elif [ -n "$(which initctl 2> /dev/null)" ]; then
    INIT_CMD="initctl"
  else
    function sysvinit () {
      service $2 $1
    }
    INIT_CMD="sysvinit"
  fi

  if [ "${DOCKER}" == "yes" ]; then
    INIT_CMD="initctl"
  fi
}

function detect_ip () {
  # Get the IP address of the server

  if [ "${SETUP_NO_CALLS}" == "yes" ]; then
    # Use local IP address
    echo "# Getting the IP address of the first local IP address"
    export INVENTREE_IP=$(hostname -I | awk '{print $1}')
  else
    # Use web service to get the IP address
    echo "# Getting the IP address of the server via web service"
    export INVENTREE_IP=$(curl -s https://checkip.amazonaws.com)
  fi

  echo "IP address is ${INVENTREE_IP}"
}

function create_initscripts () {

  # Make sure python env exsists
  if test -f "${APP_HOME}/env"; then
    echo "# python enviroment already present - skipping"
  else
    echo "# Setting up python enviroment"
    sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && python3 -m venv env && pip install invoke"
  fi

  # Unlink default config if it exists
  if test -f "/etc/nginx/sites-enabled/default"; then
    echo "# Unlinking default nginx config\n# Old file still in /etc/nginx/sites-available/default"
    sudo unlink /etc/nginx/sites-enabled/default
  fi

  # Create InvenTree specific nginx config
  echo "# Stopping nginx"
  ${INIT_CMD} stop nginx
  echo "# Setting up nginx to ${SETUP_NGINX_FILE}"
  # Always use the latest nginx config; important if new headers are added / needed for security
  cp ${APP_HOME}/docker/production/nginx.prod.conf ${SETUP_NGINX_FILE}
  sed -i s/inventree-server:8000/localhost:6000/g ${SETUP_NGINX_FILE}
  sed -i s=var/www=opt/inventree/data=g ${SETUP_NGINX_FILE}
  # Start nginx
  echo "# Starting nginx"
  ${INIT_CMD} start nginx

  echo "# (Re)creating init scripts"
  # This reset scale parameters to a known state
  inventree scale web="1" worker="1"

  echo "# Enabling InvenTree on boot"
  ${INIT_CMD} enable inventree
}

function create_admin () {
  # Create data for admin user

  if test -f "${SETUP_ADMIN_PASSWORD_FILE}"; then
    echo "# Admin data already exists - skipping"
  else
    echo "# Creating admin user data"

    # Static admin data
    export INVENTREE_ADMIN_USER=${INVENTREE_ADMIN_USER:-admin}
    export INVENTREE_ADMIN_EMAIL=${INVENTREE_ADMIN_EMAIL:-admin@example.com}

    # Create password if not set
    if [ -z "${INVENTREE_ADMIN_PASSWORD}" ]; then
      openssl rand -base64 32 > ${SETUP_ADMIN_PASSWORD_FILE}
      export INVENTREE_ADMIN_PASSWORD=$(cat ${SETUP_ADMIN_PASSWORD_FILE})
    fi
  fi
}

function start_inventree () {
  echo "# Starting InvenTree"
  ${INIT_CMD} start inventree
}

function stop_inventree () {
  echo "# Stopping InvenTree"
  ${INIT_CMD} stop inventree
}

function update_or_install () {

    # Set permissions so app user can write there
    chown ${APP_USER}:${APP_GROUP} ${APP_HOME} -R

    # Run update as app user
    echo "# Updating InvenTree"
    sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && invoke update"

    # Make sure permissions are correct again
    echo "# Set permissions for data dir and media: ${DATA_DIR}"
    chown ${APP_USER}:${APP_GROUP} ${DATA_DIR} -R
    chown ${APP_USER}:${APP_GROUP} ${CONF_DIR} -R
}

function set_env () {
  echo "# Setting up InvenTree config values"

  inventree config:set INVENTREE_CONFIG_FILE=${INVENTREE_CONFIG_FILE}

  # Changing the config file
  echo "# Writing the settings to the config file ${INVENTREE_CONFIG_FILE}"
  # Media Root
  sed -i s=#media_root:\ \'/home/inventree/data/media\'=media_root:\ \'${INVENTREE_MEDIA_ROOT}\'=g ${INVENTREE_CONFIG_FILE}
  # Static Root
  sed -i s=#static_root:\ \'/home/inventree/data/static\'=static_root:\ \'${INVENTREE_STATIC_ROOT}\'=g ${INVENTREE_CONFIG_FILE}
  # Plugins enabled
  sed -i s=plugins_enabled:\ False=plugins_enabled:\ ${INVENTREE_PLUGINS_ENABLED}=g ${INVENTREE_CONFIG_FILE}
  # Plugin file
  sed -i s=#plugin_file:\ \'/path/to/plugins.txt\'=plugin_file:\ \'${INVENTREE_PLUGIN_FILE}\'=g ${INVENTREE_CONFIG_FILE}
  # Secret key file
  sed -i s=#secret_key_file:\ \'/etc/inventree/secret_key.txt\'=secret_key_file:\ \'${INVENTREE_SECRET_KEY_FILE}\'=g ${INVENTREE_CONFIG_FILE}
  # Database name
  sed -i s=#NAME:\ \'/path/to/database\'=NAME:\ \'${INVENTREE_DB_NAME}\'=g ${INVENTREE_CONFIG_FILE}
  # Database engine
  sed -i s=#ENGINE:\ sampleengine=ENGINE:\ ${INVENTREE_DB_ENGINE}=g ${INVENTREE_CONFIG_FILE}
  # Debug mode
  sed -i s=debug:\ True=debug:\ False=g ${INVENTREE_CONFIG_FILE}

  # Fixing the permissions
  chown ${APP_USER}:${APP_GROUP} ${DATA_DIR} ${INVENTREE_CONFIG_FILE}
}


function final_message () {
  echo -e "####################################################################################"
  echo -e "This InvenTree install uses nginx, the settings for the webserver can be found in"
  echo -e "${SETUP_NGINX_FILE}"
  echo -e "Try opening InvenTree with either\nhttp://localhost/ or http://${INVENTREE_IP}/\n"
  echo -e "Admin user data:"
  echo -e "   Email: ${INVENTREE_ADMIN_EMAIL}"
  echo -e "   Username: ${INVENTREE_ADMIN_USER}"
  echo -e "   Password: ${INVENTREE_ADMIN_PASSWORD}"
  echo -e "####################################################################################"
}
