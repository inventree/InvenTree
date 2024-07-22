#!/bin/bash
#
# packager.io postinstall script functions
#
Color_Off='\033[0m'
On_Red='\033[41m'
PYTHON_FROM=9
PYTHON_TO=12

function detect_docker() {
  if [ -n "$(grep docker </proc/1/cgroup)" ]; then
    DOCKER="yes"
  else
    DOCKER="no"
  fi
}

function detect_initcmd() {
  if [ -n "$(which systemctl 2>/dev/null)" ]; then
    INIT_CMD="systemctl"
  elif [ -n "$(which initctl 2>/dev/null)" ]; then
    INIT_CMD="initctl"
  else
    function sysvinit() {
      service $2 $1
    }
    INIT_CMD="sysvinit"
  fi

  if [ "${DOCKER}" == "yes" ]; then
    INIT_CMD="initctl"
  fi
}

function detect_ip() {
  # Get the IP address of the server

  if [ "${SETUP_NO_CALLS}" == "true" ]; then
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

function detect_python() {
  # Detect if there is already a python version installed in /opt/inventree/env/lib
  if test -f "${APP_HOME}/env/bin/python"; then
    echo "# Python environment already present"
    # Extract earliest python version initialised from /opt/inventree/env/lib
    SETUP_PYTHON=$(ls -1 ${APP_HOME}/env/bin/python* | sort | head -n 1)
    echo "# Found earlier used version: ${SETUP_PYTHON}"
  else
    echo "# No python environment found - using environment variable: ${SETUP_PYTHON}"
  fi

  # Try to detect a python between 3.9 and 3.12 in reverse order
  if [ -z "$(which ${SETUP_PYTHON})" ]; then
    echo "# Trying to detecting python3.${PYTHON_FROM} to python3.${PYTHON_TO} - using newest version"
    for i in $(seq $PYTHON_TO -1 $PYTHON_FROM); do
      echo "# Checking for python3.${i}"
      if [ -n "$(which python3.${i})" ]; then
        SETUP_PYTHON="python3.${i}"
        echo "# Found python3.${i} installed - using for setup ${SETUP_PYTHON}"
        break
      fi
    done
  fi

  # Ensure python can be executed - abort if not
  if [ -z "$(which ${SETUP_PYTHON})" ]; then
    echo "${On_Red}"
    echo "# Python ${SETUP_PYTHON} not found - aborting!"
    echo "# Please ensure python can be executed with the command '$SETUP_PYTHON' by the current user '$USER'."
    echo "# If you are using a different python version, please set the environment variable SETUP_PYTHON to the correct command - eg. 'python3.10'."
    echo "${Color_Off}"
    exit 1
  fi
}

function get_env() {
  envname=$1

  pid=$$
  while [ -z "${!envname}" -a $pid != 1 ]; do
      ppid=`ps -oppid -p$pid|tail -1|awk '{print $1}'`
      env=`strings /proc/$ppid/environ`
      export $envname=`echo "$env"|awk -F= '$1 == "'$envname'" { print $2; }'`
      pid=$ppid
  done

  if [ -n "${SETUP_DEBUG}" ]; then
    echo "Done getting env $envname: ${!envname}"
  fi
}

function detect_local_env() {
  # Get all possible envs for the install

  if [ -n "${SETUP_DEBUG}" ]; then
    echo "# Printing local envs - before #++#"
    printenv
  fi

  for i in ${SETUP_ENVS//,/ }
  do
      get_env $i
  done

  if [ -n "${SETUP_DEBUG}" ]; then
    echo "# Printing local envs - after #++#"
    printenv
  fi
}

function detect_envs() {
  # Detect all envs that should be passed to setup commands

  echo "# Setting base environment variables"

  export INVENTREE_CONFIG_FILE=${INVENTREE_CONFIG_FILE:-${CONF_DIR}/config.yaml}

  if test -f "${INVENTREE_CONFIG_FILE}"; then
    echo "# Using existing config file: ${INVENTREE_CONFIG_FILE}"

    # Install parser
    pip install --require-hashes -r ${APP_HOME}/contrib/dev_reqs/requirements.txt -q

    # Load config
    export INVENTREE_CONF_DATA=$(cat ${INVENTREE_CONFIG_FILE} | jc --yaml)

    # Parse the config file
    export INVENTREE_MEDIA_ROOT=$(jq -r '.[].media_root' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_STATIC_ROOT=$(jq -r '.[].static_root' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_BACKUP_DIR=$(jq -r '.[].backup_dir' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_PLUGINS_ENABLED=$(jq -r '.[].plugins_enabled' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_PLUGIN_FILE=$(jq -r '.[].plugin_file' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_SECRET_KEY_FILE=$(jq -r '.[].secret_key_file' <<< ${INVENTREE_CONF_DATA})

    export INVENTREE_DB_ENGINE=$(jq -r '.[].database.ENGINE' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_NAME=$(jq -r '.[].database.NAME' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_USER=$(jq -r '.[].database.USER' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_PASSWORD=$(jq -r '.[].database.PASSWORD' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_HOST=$(jq -r '.[].database.HOST' <<< ${INVENTREE_CONF_DATA})
    export INVENTREE_DB_PORT=$(jq -r '.[].database.PORT' <<< ${INVENTREE_CONF_DATA})
  else
    echo "# No config file found: ${INVENTREE_CONFIG_FILE}, using envs or defaults"

    if [ -n "${SETUP_DEBUG}" ]; then
      echo "# Print current envs"
      printenv | grep INVENTREE_
      printenv | grep SETUP_
    fi

    export INVENTREE_MEDIA_ROOT=${INVENTREE_MEDIA_ROOT:-${DATA_DIR}/media}
    export INVENTREE_STATIC_ROOT=${DATA_DIR}/static
    export INVENTREE_BACKUP_DIR=${DATA_DIR}/backup
    export INVENTREE_PLUGINS_ENABLED=true
    export INVENTREE_PLUGIN_FILE=${CONF_DIR}/plugins.txt
    export INVENTREE_SECRET_KEY_FILE=${CONF_DIR}/secret_key.txt

    export INVENTREE_DB_ENGINE=${INVENTREE_DB_ENGINE:-sqlite3}
    export INVENTREE_DB_NAME=${INVENTREE_DB_NAME:-${DATA_DIR}/database.sqlite3}
    export INVENTREE_DB_USER=${INVENTREE_DB_USER:-sampleuser}
    export INVENTREE_DB_PASSWORD=${INVENTREE_DB_PASSWORD:-samplepassword}
    export INVENTREE_DB_HOST=${INVENTREE_DB_HOST:-samplehost}
    export INVENTREE_DB_PORT=${INVENTREE_DB_PORT:-123456}

    export SETUP_CONF_LOADED=true
  fi

  # For debugging pass out the envs
  echo "# Collected environment variables:"
  echo "#    INVENTREE_MEDIA_ROOT=${INVENTREE_MEDIA_ROOT}"
  echo "#    INVENTREE_STATIC_ROOT=${INVENTREE_STATIC_ROOT}"
  echo "#    INVENTREE_BACKUP_DIR=${INVENTREE_BACKUP_DIR}"
  echo "#    INVENTREE_PLUGINS_ENABLED=${INVENTREE_PLUGINS_ENABLED}"
  echo "#    INVENTREE_PLUGIN_FILE=${INVENTREE_PLUGIN_FILE}"
  echo "#    INVENTREE_SECRET_KEY_FILE=${INVENTREE_SECRET_KEY_FILE}"
  echo "#    INVENTREE_DB_ENGINE=${INVENTREE_DB_ENGINE}"
  echo "#    INVENTREE_DB_NAME=${INVENTREE_DB_NAME}"
  echo "#    INVENTREE_DB_USER=${INVENTREE_DB_USER}"
  if [ -n "${SETUP_DEBUG}" ]; then
    echo "#    INVENTREE_DB_PASSWORD=${INVENTREE_DB_PASSWORD}"
  fi
  echo "#    INVENTREE_DB_HOST=${INVENTREE_DB_HOST}"
  echo "#    INVENTREE_DB_PORT=${INVENTREE_DB_PORT}"
}

function create_initscripts() {

  # Make sure python env exists
  if test -f "${APP_HOME}/env"; then
    echo "# python environment already present - skipping"
  else
    echo "# Setting up python environment"
    sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && ${SETUP_PYTHON} -m venv env"
    sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && env/bin/pip install invoke wheel"

    # Check INSTALLER_EXTRA exists and load it
    if test -f "${APP_HOME}/INSTALLER_EXTRA"; then
      echo "# Loading extra packages from INSTALLER_EXTRA"
      source ${APP_HOME}/INSTALLER_EXTRA
    fi

    if [ -n "${SETUP_EXTRA_PIP}" ]; then
      echo "# Installing extra pip packages"
      if [ -n "${SETUP_DEBUG}" ]; then
        echo "# Extra pip packages: ${SETUP_EXTRA_PIP}"
      fi
      sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && env/bin/pip install ${SETUP_EXTRA_PIP}"
      # Write extra packages to INSTALLER_EXTRA
      echo "SETUP_EXTRA_PIP='${SETUP_EXTRA_PIP}'" >>${APP_HOME}/INSTALLER_EXTRA
    fi
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
  cp ${APP_HOME}/contrib/packager.io/nginx.prod.conf ${SETUP_NGINX_FILE}
  sed -i s/inventree-server:8000/localhost:6000/g ${SETUP_NGINX_FILE}
  sed -i s=var/www=opt/inventree/data=g ${SETUP_NGINX_FILE}
  # Start nginx
  echo "# Starting nginx"
  ${INIT_CMD} start nginx

  echo "# (Re)creating init scripts"
  # This resets scale parameters to a known state
  inventree scale web="1" worker="1"

  echo "# Enabling InvenTree on boot"
  ${INIT_CMD} enable inventree
}

function create_admin() {
  # Create data for admin users - stop with setting SETUP_ADMIN_NOCREATION to true
  if [ "${SETUP_ADMIN_NOCREATION}" == "true" ]; then
    echo "# Admin creation is disabled - skipping"
    return
  fi

  if test -f "${SETUP_ADMIN_PASSWORD_FILE}"; then
    echo "# Admin data already exists - skipping"
  else
    echo "# Creating admin user data"

    # Static admin data
    export INVENTREE_ADMIN_USER=${INVENTREE_ADMIN_USER:-admin}
    export INVENTREE_ADMIN_EMAIL=${INVENTREE_ADMIN_EMAIL:-admin@example.com}

    # Create password if not set
    if [ -z "${INVENTREE_ADMIN_PASSWORD}" ]; then
      openssl rand -base64 32 >${SETUP_ADMIN_PASSWORD_FILE}
      export INVENTREE_ADMIN_PASSWORD=$(cat ${SETUP_ADMIN_PASSWORD_FILE})
    fi
  fi
}

function start_inventree() {
  echo "# Starting InvenTree"
  ${INIT_CMD} start inventree
}

function stop_inventree() {
  echo "# Stopping InvenTree"
  ${INIT_CMD} stop inventree
}

function update_or_install() {

  # Set permissions so app user can write there
  chown ${APP_USER}:${APP_GROUP} ${APP_HOME} -R

  # Run update as app user
  echo "# Updating InvenTree"
  sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && pip install wheel"
  sudo -u ${APP_USER} --preserve-env=$SETUP_ENVS bash -c "cd ${APP_HOME} && invoke update | sed -e 's/^/# inv update| /;'"

  # Make sure permissions are correct again
  echo "# Set permissions for data dir and media: ${DATA_DIR}"
  chown ${APP_USER}:${APP_GROUP} ${DATA_DIR} -R
  chown ${APP_USER}:${APP_GROUP} ${CONF_DIR} -R
}

function set_env() {
  echo "# Setting up InvenTree config values"

  inventree config:set INVENTREE_CONFIG_FILE=${INVENTREE_CONFIG_FILE}

  # Changing the config file
  echo "# Writing the settings to the config file ${INVENTREE_CONFIG_FILE}"
  # Media Root
  sed -i s=#media_root:\ \'/home/inventree/data/media\'=media_root:\ \'${INVENTREE_MEDIA_ROOT}\'=g ${INVENTREE_CONFIG_FILE}
  # Static Root
  sed -i s=#static_root:\ \'/home/inventree/data/static\'=static_root:\ \'${INVENTREE_STATIC_ROOT}\'=g ${INVENTREE_CONFIG_FILE}
  # Backup dir
  sed -i s=#backup_dir:\ \'/home/inventree/data/backup\'=backup_dir:\ \'${INVENTREE_BACKUP_DIR}\'=g ${INVENTREE_CONFIG_FILE}
  # Plugins enabled
  sed -i s=plugins_enabled:\ False=plugins_enabled:\ ${INVENTREE_PLUGINS_ENABLED}=g ${INVENTREE_CONFIG_FILE}
  # Plugin file
  sed -i s=#plugin_file:\ \'/path/to/plugins.txt\'=plugin_file:\ \'${INVENTREE_PLUGIN_FILE}\'=g ${INVENTREE_CONFIG_FILE}
  # Secret key file
  sed -i s=#secret_key_file:\ \'/etc/inventree/secret_key.txt\'=secret_key_file:\ \'${INVENTREE_SECRET_KEY_FILE}\'=g ${INVENTREE_CONFIG_FILE}
  # Debug mode
  sed -i s=debug:\ True=debug:\ False=g ${INVENTREE_CONFIG_FILE}

  # Database engine
  sed -i s=#\ ENGINE:\ Database\ engine.\ Selection\ from:=ENGINE:\ ${INVENTREE_DB_ENGINE}=g ${INVENTREE_CONFIG_FILE}
  # Database name
  sed -i s=#\ NAME:\ Database\ name=NAME:\ \'${INVENTREE_DB_NAME}\'=g ${INVENTREE_CONFIG_FILE}
  # Database user
  sed -i s=#\ USER:\ Database\ username\ \(if\ required\)=USER:\ ${INVENTREE_DB_USER}=g ${INVENTREE_CONFIG_FILE}
  # Database password
  sed -i s=#\ PASSWORD:\ Database\ password\ \(if\ required\)=PASSWORD:\ ${INVENTREE_DB_PASSWORD}=g ${INVENTREE_CONFIG_FILE}
  # Database host
  sed -i s=#\ HOST:\ Database\ host\ address\ \(if\ required\)=HOST:\ ${INVENTREE_DB_HOST}=g ${INVENTREE_CONFIG_FILE}
  # Database port
  sed -i s=#\ PORT:\ Database\ host\ port\ \(if\ required\)=PORT:\ ${INVENTREE_DB_PORT}=g ${INVENTREE_CONFIG_FILE}

  # Fixing the permissions
  chown ${APP_USER}:${APP_GROUP} ${DATA_DIR} ${INVENTREE_CONFIG_FILE}
}

function set_site() {
  # Ensure IP is known
  if [ -z "${INVENTREE_IP}" ]; then
    echo "# No IP address found - skipping"
    return
  fi

  # Check if INVENTREE_SITE_URL in inventree config
  if [ -z "$(inventree config:get INVENTREE_SITE_URL)" ]; then
    echo "# Setting up InvenTree site URL"
    inventree config:set INVENTREE_SITE_URL=http://${INVENTREE_IP}
  fi
}

function final_message() {
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


function update_checks() {
  echo "# Running upgrade"
  local old_version=$1
  local old_version_rev=$(echo ${old_version} | cut -d'-' -f1 | cut -d'.' -f2)
  echo "# Old version is: ${old_version} - release: ${old_version_rev}"

  local ABORT=false
  function check_config_value() {
    local env_key=$1
    local config_key=$2
    local name=$3

    local value=$(inventree config:get ${env_key})
    if [ -z "${value}" ] || [ "$value" == "null" ]; then
      value=$(jq -r ".[].${config_key}" <<< ${INVENTREE_CONF_DATA})
    fi
    if [ -z "${value}" ] || [ "$value" == "null" ]; then
      echo "# No setting for ${name} found - please set it manually either in ${INVENTREE_CONFIG_FILE} under '${config_key}' or with 'inventree config:set ${env_key}=value'"
      ABORT=true
    else
      echo "# Found setting for ${name} - ${value}"
    fi
  }

  # Custom checks if old version is below 0.8.0
  if [ "${old_version_rev}" -lt "9" ]; then
    echo "# Old version is below 0.9.0 - You might be missing some configs"

    # Check for BACKUP_DIR and SITE_URL in INVENTREE_CONF_DATA and config
    check_config_value "INVENTREE_SITE_URL" "site_url" "site URL"
    check_config_value "INVENTREE_BACKUP_DIR" "backup_dir" "backup dir"

    if [ "${ABORT}" = true ]; then
      echo "# Aborting - please set the missing values and run the update again"
      exit 1
    fi
    echo "# All checks passed - continuing with the update"
  fi
}
