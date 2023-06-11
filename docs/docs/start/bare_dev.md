---
title: Bare Metal Development Server
---

## Bare Metal Development Server

!!! warning "Installation"
    Before continuing, ensure that the [installation steps](./install.md) have been completed.

InvenTree includes a simple server application, suitable for use in a development environment.

!!! warning "Deployment"
    Refer to the [production server instructions](./bare_prod.md) to implement a much more robust server setup.

### Running on a Local Machine

To run the development server on a local machine, run the command:

```
(env) invoke server
```

This will launch the InvenTree web interface at `http://127.0.0.1:8000`.

A different port can be specified using the `-a` flag:

```
(env) invoke server -a 127.0.0.1:8123
```

Serving on the address `127.0.0.1` means that InvenTree will only be available *on that computer*. The server will be accessible from a web browser on the same computer, but not from any other computers on the local network.

### Running on a Local Network

To enable access to the InvenTree server from other computers on a local network, you need to know the IP of the computer running the server. For example, if the server IP address is `192.168.120.1`:

```
(env) invoke server -a 192.168.120.1:8000
```

## Background Worker

The background task manager must also be started. The InvenTree server is already running in the foreground, so open a *new shell window* to start the server.

### Activate Virtual Environment

```
cd /home/inventree
source ./env/bin/activate
```

### Start Background Worker

```
(env) invoke worker
```

This will start the background process manager in the current shell.
