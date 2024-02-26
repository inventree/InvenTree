---
title: Serving Static and Media Files
---

## Serving Files

In production, the InvenTree web server software *does not* provide hosting of static files, or user-uploaded (media) files.

When running in [production mode](./bare_prod.md) (i.e. the `INVENTREE_DEBUG` flag is disabled), a separate web server is required for serving *static* and *media* files. In `DEBUG` mode, the django webserver facilitates delivery of *static* and *media* files, but this is explicitly not suitable for a production environment.

!!! into "Read More"
    You can find further information in the [django documentation]({% include "django.html" %}/howto/static-files/deployment/).

There are *many* different ways that a sysadmin might wish to handle this - and it depends on your particular installation requirements.

The [docker production example](./docker_prod.md) provides an example using [Nginx](https://www.nginx.com/) to serve *static* and *media* files, and redirecting other requests to the InvenTree web server itself.

You may use this as a jumping off point, or use an entirely different server setup.

#### Static Files

Static files can be served without any need for authentication. In fact, they must be accessible *without* authentication, otherwise the unauthenticated views (such as the login screen) will not function correctly.

#### Media Files

It is highly recommended that the *media* files are served in such a way that user authentication is required.

Refer to the [docker production example](./docker_prod.md) for a demonstration of using nginx to serve media files only to authenticated users, and forward authentication requests to the InvenTree web server.
