## Error Codes

InvenTree is starting to use error codes to help identify and diagnose issues. These are increasingly being added to the codebase. Error messages missing an error code should be reported on GitHub.
Error codes are prefixed with `INVE-` and are followed by a letter to indicate the type of error and a number to indicate the specific error. Once a code is used it might not be reassigned to a different error, it can be marked as stricken from the list.

### INVE-E (InvenTree Error)
Errors - These are critical errors which should be addressed as soon as possible.

#### INVE-E1
**No frontend included - Backend/web**

Only stable / production releases of InvenTree include the frontend panel. This is both a measure of resource-saving and attack surface reduction.

If you want to use the frontend panel, you can either:

- use a docker image that is version-tagged or the stable version
- use a package version that is from the stable or version stream - if you are and it is not working, run `sudo inventree run invoke update` to re-run the upgrade
- install node and yarn on the server to build the frontend with the [invoke](../start/invoke.md) task `int.frontend-build`

Raise an issue if none of these options work.

#### INVE-E2
**Wrong Invoke Path**

The used invoke executable is the wrong one. InvenTree needs to have
You probably have a reference to invoke or a directory with invoke in your PATH variable that is not in InvenTrees virtual environment. You can check this by running `which invoke` and `which python` in your installations base directory and compare the output. If they are not the same, you need to adjust your PATH variable to point to the correct virtual environment before it lists other directories with invoke.

#### INVE-E3
**Report Context use custom QuerySet**

As the `django.db.models.QuerySet` is not a generic class, we would loose type information without `django-stubs`. Therefore use the `report.mixins.QuerySet` generic class when typing a report context.

#### INVE-E4
**Model missing report_context return type annotation**

Models that implement the `InvenTreeReportMixin` must have an explicit return type annotation for the `report_context` function.

#### INVE-E5
**Rulesets have issues - Backend**

The rulesets used for managing user/group/oAuth permissions have an issue.
This might be caused by an addition or removal of models to the code base. Running the test suit should surface more logs with the error code indicating the exact infractions.

#### INVE-E6
**Scopes have issues - Backend**

The scopes used for oAuth permissions have an issue and do not match the rulesets.
This might be caused by an addition or removal of models to the code base or changes to the rulesets. Running the test suit should surface more logs with the error code indicating the exact infractions.

#### INVE-E7
**The host used does not match settings - Backend**

The settings for SITE_URL and ALLOWED_HOSTS do not match the host used to access the server. This might lead to issues with CSRF protection, CORS and other security features.
The settings must be adjusted.

#### INVE-E8
**Email log deletion is protected - Backend**

The email log is protected from deletion by a setting. This was set by an administrator to prevent accidental deletion of emails.
If you want to delete the email log, you need to get the [`INVENTREE_PROTECT_EMAIL_LOG`](../settings/global.md#server-settings) setting set to `False`.

#### INVE-E9
**Transition handler error - Backend**
An error occurred while discovering or executing a transition handler. This likely indicates a faulty or incompatible plugin.
This error is raised by a plugin with the `TransitionMixin` and can be debugged by looking into the logs for more information.

#### INVE-E10
**Plugin cannot be uninstalled or deactivated - Backend**
A plugin cannot be uninstalled if it is mandatory, a sample or a built-in plugin. Mandatory plugins can not be deactivated.

This is to prevent accidental removal of essential system or compliance functionality. If you want to remove/deactivate a mandatory plugin, you need to remove it from the `INVENTREE_PLUGINS_MANDATORY` [setting](../start/config.md#plugin-options). Sample and built-in plugins can not be uninstalled at all but might be deactivated.

See [Mandatory Plugins](../plugins/index.md#mandatory-plugins) for more information.

#### INVE-E11
**Plugin cannot override final method - Backend**
A plugin is not allowed to override a *final method* from the `InvenTreePlugin` class.

This is a security measure to prevent plugins from changing the core functionality of InvenTree. The code of the plugin must be changed to not override functions that are marked as *final*.

#### INVE-E12
**Plugin returned invalid machine type - Backend**

An error occurred when discovering or initializing a machine type from a plugin. This likely indicates a faulty or incompatible plugin.

#### INVE-E13

**Error reading InvenTree configuration file**

An error occurred while reading the InvenTree configuration file. This might be caused by a syntax error or invalid value in the configuration file.

#### INVE-E14

**Could not import Django**

Django is not installed in the current Python environment. This means that the InvenTree backend is not running within the correct [python virtual environment](../start/index.md#virtual-environment) or that the required Python packages were not installed correctly.

#### INVE-E15

**Python version not supported**

This error occurs attempting to run InvenTree on a version of Python which is older than the minimum required version. We [require Python {{ config.extra.min_python_version }} or newer](../start/index.md#python-requirements)

### INVE-W (InvenTree Warning)
Warnings - These are non-critical errors which should be addressed when possible.

#### INVE-W1
**Current branch could not be detected - Backend**

During startup of the backend InvenTree tries to detect branch, commit hash and commit date to surface on various points in the UI, through tags and in the API.
This information is not needed for operation but very helpful for debugging and support. These issues might be caused by running a deployment version that delivers without git information, not having git installed or not having dulwich installed.
You can ignore this warning if you are not interested in the git information.


#### INVE-W2
**Dulwich module not found - Backend**

See [INVE-W1](#inve-w1)


#### INVE-W3
**Could not detect git information - Backend**

See [INVE-W1](#inve-w1)


#### INVE-W4
**Server is running in debug mode - Backend**

InvenTree is running in debug mode. This is **not** recommended for production use, as it exposes sensitive information and makes the server more vulnerable to attacks. Debug mode is not intended for production/exposed instances, **even for short duration**.

It is recommended to run InvenTree in production mode for better security and performance. See [Debug Mode Information](../start/index.md#debug-mode).


#### INVE-W5
**Background worker process not running - Backend**

The background worker seems to not be running. This is detected by a heartbeat that runs all 5 minutes - this error triggers after not being run in the last 10 minutes.
Check if the process for background workers is running and reaching the database. Steps vary between deployment methods.
See [Background Worker Information](../start/processes.md#background-worker).


#### INVE-W6
**Server restart required - Backend**

The server needs a restart due to changes in settings. Steps very between deployment methods.


#### INVE-W7
**Email settings not configured - Backend**

Not all required settings for sending emails are configured. Not having an email provider configured might lead to degraded processes as password reset, update notifications and user notifications can not work. Setting up email is recommended.
See [Email information](../start/config.md#email-settings).


#### INVE-W8
**Database Migrations required - Backend**

There are database migrations waiting to be applied. This might lead to integrity and availability issues. Applying migrations as soon as possible is recommended.

Some deployment methods support [auto applying of updates](../start/config.md#auto-update). See also [Perform Database Migrations](../start/install.md#perform-database-migrations).
Steps very between deployment methods.


#### INVE-W9
**Wrong Invoke Environment - Backend**

The command that was used to run invoke is not the one that is recommended. This might be caused by a wrong PATH variable or by thinking you are using a different deployment method.
The warning text will show the recommended command for intended use.

#### INVE-W10
**Config not in recommended directory - Backend**

A configuration file is not in the recommended directory. This might lead to issues with the deployment method you are using. It might also lead to confusion.

The warning text will show the recommended directory for your deployment method.

#### INVE-W10
**Exception during mail delivery - Backend**

Collective exception for errors that occur during mail delivery. This might be caused by a misconfiguration of the email provider or a network issue.
These issues are raised directly from the mail backend so it is unlikely that the error is caused by django or InvenTree itself.
Check the logs for more information.

#### INVE-W11
**Registration cannot be enabled because of email settings - Backend**

Registration was enabled but the email settings are not configured correctly. This might lead to issues with user registration, password reset and other authentication features that require email.

Therefore the registration user interface elements will not be shown.


To enable registration, the email settings must be configured correctly. See  [email configuration](../start/config.md#email-settings).

### INVE-I (InvenTree Information)
Information — These are not errors but information messages. They might point out potential issues or just provide information.

#### INVE-I1
**Setting overridden - Backend**
Overriding a global setting with a different value than the current one.

See [Override global settings](../settings/global.md#override-global-settings) for more information.

#### INVE-I2
**Issue with filtering serializer or decorator - Backend**

An issue was detected with the application of a filtering serializer or decorator. This might lead to unexpected behaviour or performance issues. Therefore an issue is raised to make the developer aware of the possible issue. Look into the docstrings of enable_filter, FilterableSerializerField or FilterableSerializerMixin.

This warning should only be raised during development and not in production, if you recently installed a plugin you might want to contact the plugin author.

### INVE-M (InvenTree Miscellaneous)
Miscellaneous — These are information messages that might be used to mark debug information or other messages helpful for the InvenTree team to understand behaviour.
