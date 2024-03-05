---
title: Serving Static and Media Files
---

## Serving Files

In a production installation, the InvenTree web server application *does not* provide hosting of static files, or user-uploaded (media) files. Instead, these files should be served by a separate web server, such as [Caddy](https://caddyserver.com/), [Nginx](https://www.nginx.com/), or [Apache](https://httpd.apache.org/).

!!! info "Debug Mode"
    When running in [production mode](./bare_prod.md) (i.e. the `INVENTREE_DEBUG` flag is disabled), a separate web server is required for serving *static* and *media* files. In `DEBUG` mode, the django webserver facilitates delivery of *static* and *media* files, but this is explicitly not suitable for a production environment.

!!! tip "Read More"
    You can find further information in the [django documentation]({% include "django.html" %}/howto/static-files/deployment/).

There are *many* different ways that a sysadmin might wish to handle this - and it depends on your particular installation requirements.

### Static Files

Static files can be served without any need for authentication. In fact, they must be accessible *without* authentication, otherwise the unauthenticated views (such as the login screen) will not function correctly.

### Media Files

It is highly recommended that the *media* files are served behind an authentication layer. This is because the media files are user-uploaded, and may contain sensitive information. Most modern web servers provide a way to serve files behind an authentication layer.

### Example Configuration

The [docker production example](./docker.md) provides an example using [Caddy](https://caddyserver.com) to serve *static* and *media* files, and redirecting other requests to the InvenTree web server itself.

Caddy is a modern web server which is easy to configure and provides a number of useful features, including automatic SSL certificate generation.
