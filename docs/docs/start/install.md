---
title: Install InvenTree
---

## Bare Metal Setup

These are the instructions for a manual install instructions on bare metal.  At the end you will be almost ready to run InvenTree locally, with some further steps start either a production or development server.

!!! tip "Installer"
      For a more automated installation method, we recommend using our [installer](./installer.md).

!!! tip "Docker Guide"
    If you want to install using Docker refer to the [Docker Setup Guide](./docker.md).

Follow the instructions below to install the required system packages, python modules, and InvenTree source code.

!!! warning "Experienced Users Only"
    The following instructions assume you are reasonably adept at Linux system administration.

!!! warning "OS Specific Requirements"
    These instructions have been tested with the following distros and versions:

      * Ubuntu 25.10
      * Debian FIXME

    The instructions may need to be tweaked for other distros and versions.

!!! tip "Root and non-root users"
    Commands which should be run as "root" (the privileged super user), are prefixed with `sudo`.  Commands _not_ prefixed with `sudo` should be run as the non-privileged user (see the `inventree` user created below).  In practice you might use ssh to get access to the server as root, then run `su -l inventree` to switch to the non-privileged user.  Or you might have two terminal windows open, one for root, and and one for the non-privileged user.  The `sudo` prefix in these instructions is your cue as to which account should run the command.

### Install System Packages
Install required system packages (as `root`, the super user):

```
sudo apt-get update
sudo apt-get install \
    python3 python3-dev python3-pip \
    git gcc g++ gettext gnupg \
    poppler-utils pango1.0-tools \
    libjpeg-dev webp
```



### User Accounts

!!! warning "Don't Run As Root"
    The InvenTree server should not be run by the root user. These installation instructions assume that InvenTree is installed and run using a user account called `inventree`.

!!! tip "Run programs as root more easily"
    To allow the `inventree` user to perform privileged actions during this installation via `sudo` with no root password, run this:

    ```
    echo 'inventree ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/inventree
    sudo chmod 0440 /etc/sudoers.d/inventree
    ```

    To revoke this:
    ```
    sudo rm /etc/sudoers.d/inventree
    ```

#### Create InvenTree User

To create the user account:

```
sudo useradd -m -U -s /bin/bash inventree
```

From here on, most commands should be run by the `inventree` user, so switch to them now:

```
sudo su -l inventree
```
Alternatively, use ssh to login as the `inventree` user.

### Set Up Directories

InvenTree requires a directory for storage of [static files](./config.md#static-file-storage), for [user uploaded files](./config.md#uploaded-file-storage), and for [database backups](./config.md#backup-file-storage).  We'll store these within a `data/` subdirectory.

```
cd
mkdir -p data/static data/media data/backup
```

Later, we'll tell InvenTree about the location of these directories via [configuration options](./config.md).

!!! info "Read More"
    For more information about static, media and backup files, please see the [proxy server documentation](./processes.md#proxy-server).

### Download Source Code

Download InvenTree source code into the `~/src` directory:

```
git clone --branch stable https://github.com/inventree/inventree src
```

!!! info "_Main Branch_ means _Development_"
    These instructions give you the latest `stable` version of InvenTree.  If you'd like to try the development branch, replace `stable` with `master`.  Please note the development version may have serious bugs, and the install instructions may have changed.

### Make A Minimal Configuration

Run these commands to create a minimal configuration file from the template.
```
ln -sf ../src/backend/InvenTree/config_template.yaml src/config/config.yaml.orig
cp src/config/config.yaml.orig src/config/config.yaml
```

For a minimally useful configuration, edit `src/config/config.yaml` and set these options, uncommenting them if necessary:

| Option name | Value |
|----------------|-------|
| ```debug``` | ```False``` |
| ```admin_enabled``` | ```True``` |
| ```admin_user``` | ```admin``` |
| ```plugins_enabled``` | ```True``` |
| ```media_root``` | ```/home/inventree/data/media``` |
| ```static_root``` | ```/home/inventree/data/static``` |
| ```backup_dir``` | ```/home/inventree/data/backup``` |
| ```background``` &raquo; ```workers``` | ```1``` |

Several more options need settings, but these depend on your particular installation.  Here is an example configuration for a site running at `https://itree.example.com/`, using a MariaDB database backend.  Choose values suitable for your installation.

| Option name | Value | Notes |
|-------------|-------|-------|
| `site_url` | `https://itree.example.com/` | Use http://localhost:8000 for local testing. |
| `database` &raquo; `ENGINE`<br>`database` &raquo; `NAME`<br>`database` &raquo; `USER`<br>`database` &raquo; `PASSWORD` | `mysql`<br>`inventree`<br>`dbuser`<br>`VeryC0mPLekSP4SS` | For configuring other databases, see [Database configuration for Django](https://docs.djangoproject.com/en/5.2/ref/databases/).  Database creation is covered below.|
| `admin_url` | `itree-admin` | Moves admin interface to `https://itree.example.com/itree-admin/`, to reduce scripted attacks. |
| `admin_email` | `itree-admin@example.com` | Who puzzled users should email.
| `admin_password` | `^TotalllllyUnge55ible` | Password for the admin user. |
| `language` | `en-US` | See this list of [language codes](http://www.i18nguy.com/unicode/language-identifiers.html). |
| `timezone` | `Australia/Hobart` | See this list of [timezone names](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). |
| `email` &raquo; `sender`<br>`email` &raquo; `host`<br>`email` &raquo; `port`<br>`email` &raquo; `username`<br>`email` &raquo; `password` | `itree@example.com`<br>`mail.unst0ppable-email.com`<br>`2525`<br>`itree`<br>`tHE_n4emOfMyCAT` | Credentials and connection details for your favorite email sending company.  See [Django email settings](https://docs.djangoproject.com/en/5.2/ref/settings/#email-backend). |
| `global_settings` &raquo; `INVENTREE_DEFAULT_CURRENCY` | `USD` | See this list of [currency codes](https://en.wikipedia.org/wiki/ISO_4217). |

!!! tip "Configuration Options"
    InvenTree configuration can be performed using environment variables, the `src/config/config.yaml` configuration file, or a combination of both.
    Refer to the [configuration guidelines](./config.md) for more detail.

### Create Virtual Environment

!!! info "Python Version"
    InvenTree requires a modern Python version.  To see the minimum version we support, search for `python-version` in [pyproj.toml]({{ sourcefile("pyproject.toml") }}) for the current minimums.  Run `python3 --version` to check your installed version.

Create a python virtual environment for installing required Python packages and binaries:

```
python3 -m venv env
source ./env/bin/activate
```

!!! info "(env) prefix"
    The shell prompt should now display the `(env)` prefix, showing that you are operating within the Python virtual environment.

### Install InvenTree Packages

Let's now use `pip` to install Python packages the InvenTree server needs into the virtual environment.

```
cd src
pip install --upgrade pip
pip install --upgrade --ignore-installed invoke
invoke install --skip-plugins
```

`--skip-plugins` is necessary because without it, `invoke` tries to access the db, which hasn't been set up yet.

!!! warning "Possible errors"
    If you run `invoke` and get a message `Can't find any collection named 'tasks'!`, then you need to run `cd ~/src` first, because invoke is sensitive to the directory it runs in.

## Create Database

Setting up the database depends on the database program you're using.

### PostgreSQL

Install the database system packages:

```
sudo apt-get install postgresql postgresql-contrib libpq-dev
sudo apt-get install postgresql-client
```

Then start the postgresql service:

```
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

#### Create Database and User

We need to create a new database, and a user who will access the database.  Start the database client:

```
sudo -u postgres psql
```

You should now be in an interactive database shell. Create a new database as follows:

```
postgres=# CREATE DATABASE inventree;
```

Create a new user with complete access to the database:

```
postgres=# CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypass';
postgres=# GRANT ALL PRIVILEGES ON DATABASE inventree TO myuser;
```

!!! info "Username / Password"
    You should change the username and password to the ones from your `src/config/config.yaml` file.

Exit the Postgres shell:

```
postgres=# EXIT;
```

#### Install Python Bindings

Install the python bindings for PostgreSQL into your virtual environment:

```
pip3 install psycopg pgcli
```

### MySQL / MariaDB

Install the database system packages:

```
sudo apt-get install mysql-server libmysqlclient-dev
sudo apt-get install mariadb-server libmysqlclient-dev
```

Then start the MariaDB service:

```
systemctl enable mariadb
systemctl start mariadb
```

#### Create Database and User

We need to create a new database, and a user who will access the database.  Start the database client:

```
sudo mysql -u root
```

You should now be in an interactive database shell. Create a new database as follows:

```
mysql> CREATE DATABASE inventree;
```

Create a new user with complete access to the database:

```
mysql> CREATE USER 'myuser'@'%' IDENTIFIED WITH mysql_native_password BY 'mypass';
mysql> GRANT ALL ON inventree.* TO 'myuser'@'%';
mysql> FLUSH PRIVILEGES;
```

!!! info "Username / Password"
    You should change the username and password to the ones from your `src/config/config.yaml` file.

Exit the MySQL/MariaDB shell:

```
mysql> EXIT;
```

#### Install Python Bindings

Install the python bindings for MySQL/Maria into your virtual environment:

```
pip3 install mysqlclient
```
## Initialising The Database

Run the following command to create the database tables and populate them with initial data:

```
cd ~/src
invoke update --skip-backup --no-frontend
```

### Create Admin Account

Create a superuser (admin) account for the InvenTree installation:

```
invoke superuser
```

## Download Front End Files

A front end app runs in the user's browser page.  Let's download the files for the app:
```
mkdir -p ~/src/src/backend/InvenTree/web/static
invoke frontend-download --tag=auto
invoke static
```

## Starting A Server

!!! success "Almost ready to serve!"
    The InvenTree database is now fully configured, and ready to go.

### Development Server

To do InvenTree evaluation, testing or development, follow the [development server instructions](./bare_dev.md) for a simple server you can start and stop from the command line.

### Production Server

To set InvenTree up for you and others to use on an intranet or on the Internet, follow the [production server instructions](./bare_prod.md).  These instructions will also ensure InvenTree restarts automatically when the server reboots.

## Updating InvenTree

!!! info "Stay up to date!"
    InvenTree is under very active development, with frequent fixes and new features.

!!! tip "Quick Update"
    If you've skipped everything above because you just want to update your existing InvenTree installation, run these commands first, as the `inventree` user:
    ```
    cd ~/src
    source ~/env/bin/activate
    ```

### Backing Up Your Data
!!! warning "Update Database"
	While InvenTree will make a backup before updating your database, you should first make sure you have backups to fall back on if there's a problem.  To view the current backups:

    ```
    invoke listbackups
    ```

    `.dump.gz` files are compressed SQL dumps, and `.tar.gz` files contain user uploaded "media" files.  For help backing up and restoring, see the [backing up](./backup.md) documentation.

### Updating Source Code

To update InvenTree to the latest stable version:

```
git pull origin stable
```

To update InvenTree to the latest development version:

```
git pull origin master
```

### Perform Database Migrations

This command performs the following steps:

* Ensures all the packages InvenTree requires are installed and up to date
* Performs schema changes to tables in the database
* Walks you through any steps which require interaction
* Collects any new or updated static files

```
invoke update
```

!!! info "Skip Backup"
    `invoke update` will first create a new database backup.  To skip this, add the `--skip-backup` flag

### Restart Server

After an update, you'll need to restart the InvenTree server processes.  See the development and production server instructions above for how to do this.

## Revoke Sudo Access

If you granted the `inventree` user passwordless `sudo` access during installation, you should revoke this now:

```
sudo rm /etc/sudoers.d/inventree
```

!!! success "All done!"
    If you've made it this far, congratulations!  You now have a working InvenTree installation.  If you had problems with the installation, please let us know so we can improve this documentation.
