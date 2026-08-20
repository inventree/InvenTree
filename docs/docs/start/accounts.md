---
title: Account Management
---

## User Accounts

By default, InvenTree does not ship with any user accounts. Configuring user accounts is the first step to login to the InvenTree server.

### Administrator Account

You can configure InvenTree to create an administrator account on the first run. This account will have full *superuser* access to the InvenTree server.

This account is created when you first run the InvenTree server instance. The username / password for this account can be configured in the configuration file, or environment variables.

!!! info "More Information"
    For more information on configuring the administrator account, refer to the [configuration documentation](./config.md#administrator-account).

### Create Superuser

Another way to create an administrator account is to use the `superuser` command (via [invoke](./invoke.md)). This will create a new superuser account with the specified username and password.

```bash
invoke superuser
```

Or, if you are running InvenTree in a Docker container:

```bash
docker exec -it inventree-server invoke superuser
```

### User Management

Once you have created an administrator account, you can create and manage additional user accounts from the InvenTree web interface.

## Password Management

### Reset Password via Command Line

If a password has been lost, and other backup options (such as email recovery) are unavailable, the system administrator can reset the password for a user account from the command line.

Log into the machine running the InvenTree server, and run the following command (from the top-level source directory):

```bash
cd src/backend/InvenTree
python ./manage.py changepassword <username>
```

The system will prompt you to enter a new password for the specified user account.
