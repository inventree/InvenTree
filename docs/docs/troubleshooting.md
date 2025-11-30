---
title: Troubleshooting
---


## Troubleshooting Guide

If you are struggling with an issue which is not covered in the FAQ above, please refer to the following troubleshooting steps.

Even if you cannot immediately resolve the issue, the information below will be very useful when reporting the issue on GitHub.

## Error Codes

InvenTree uses a system of error codes to help identify specific issues. Each error code is prefixed with `INVE-`, followed by a letter indicating the error type, and a number.

Refer to the [error code documentation](./settings/error_codes.md) for more information on specific error codes.

## Recent Update

If you have recently updated your InvenTree instance, please ensure that you have followed all update instructions carefully. In particular, make sure that you have run any required database migrations using the `invoke update` command.

### Breaking Changes

Some updates may include breaking changes which require additional steps to resolve. Please refer to (and carefully read) the relevant release notes for more information. Breaking changes may require user intervention to resolve. In such instances, the release notes will clearly indicate the required steps.

## Common Troubleshooting Steps

### Run Update Step

If you have recently installed or updated your InvenTree instance, make sure that you have run the `invoke update` command, which will perform any required database migrations and other update tasks. This is a *critical step* after any system update.

#### Docker

If you are have installed InvenTree via Docker:

```bash
docker-compose exec inventree-server invoke update
```
#### Installer

If you have installed InvenTree via the installer script:

```bash
inventree run invoke update
```

### Logged Errors

Look at the logged error reports in the admin section - you will need to be an administrator to access this section. If a critical error has occurred, it may be logged here.

### GitHub Issues

Before raising a new issue, please check the [GitHub issues page](https://github.com/inventree/inventree) for reported issues. If your issue is a common one, it may already have been reported - and perhaps even resolved!

### Web Browser Console

If you are experiencing issues with the web interface, you can open the developer console in your web browser to check for error messages. This may vary slightly between web browsers, but there is a wealth of information available online if you need help.

Once the developer console is open, there are two places to check for error messages:

#### Console Tab

Navigate to the *Console* tab in the developer tools. Any error messages will be highlighted in red. They may indicate either a rendering issue, or a problem with a network request.

#### Network Tab

Navigate to the *Network* tab in the developer tools. Check for any requests which have a status code of 400 or greater (indicating an error). Click on the request to see more information about the error.

### Server Logs

Finally, you can check the server logs for error messages. The location of the server logs will depend on how you have installed InvenTree.

#### Docker

If you are using Docker, you can view the server logs with the following command:

To display logs for all running containers:

```bash
docker compose logs
```

Refer to the [docker documentation](./start/docker_install.md#viewing-logs) for more information.

#### Installer

If you are using the installer script, you can view the server logs with the following command:

```bash
inventree logs
```

Refer to the [installer documentation](./start/installer.md#viewing-logs) for more information.
