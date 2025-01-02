---
title: InvenTree Processes
---

## InvenTree Processes

InvenTree is a complex application, and there are a number of processes which must be running in order for the system to operate correctly. Typically, these processes are started automatically when the InvenTree application stack is launched. However, in some cases, it may be necessary to start these processes manually.

System administrators should be aware of the following processes when configuring an InvenTree installation:

### Database

At the core of the InvenTree application is the SQL database. The database is responsible for storing all of the persistent data which is used by the InvenTree application.

InvenTree supports a [number of database backends]({% include "django.html" %}/ref/databases) - which typically require their own process to be running.

Refer to the [database configuration guide](./config.md#database-options) for more information on selecting and configuring the database backend.

In running InvenTree via [docker compose](./docker_install.md), the database process is managed by the `inventree-db` service which provides a [Postgres docker container](https://hub.docker.com/_/postgres).

### Web Server

The InvenTree web server is responsible for serving the InvenTree web interface to users. The web server is a [Django](https://www.djangoproject.com/) application, which is run using the [Gunicorn](https://gunicorn.org/) WSGI server.

The web server interfaces with the backend database and provides a [REST API](../api/api.md) (via the [Django REST framework](https://www.django-rest-framework.org/)) which is used by the frontend web interface.

In running InvenTree via [docker compose](./docker_install.md), the web server process is managed by the `inventree-server` service, which runs from a custom docker image.

### Proxy Server

In a production installation, the InvenTree web server application *does not* provide hosting of static files, or user-uploaded (media) files. Instead, these files should be served by a separate web server, such as [Caddy](https://caddyserver.com/), [Nginx](https://www.nginx.com/), or [Apache](https://httpd.apache.org/).

!!! info "Debug Mode"
    When running in [production mode](./bare_prod.md) (i.e. the `INVENTREE_DEBUG` flag is disabled), a separate web server is required for serving *static* and *media* files. In `DEBUG` mode, the django webserver facilitates delivery of *static* and *media* files, but this is explicitly not suitable for a production environment.

!!! tip "Read More"
    You can find further information in the [django documentation]({% include "django.html" %}/howto/static-files/deployment/).

A proxy server is required to store and serve static files (such as images, documents, etc) which are used by the InvenTree application. As django is not designed to serve static files in a production environment, a separate file server is required. For our docker compose setup, we use the `inventree-proxy` service, which runs a [Caddy](https://caddyserver.com/) proxy server to serve static files.

In addition to serving static files, the proxy server also provides a reverse proxy to the InvenTree web server, allowing the InvenTree web interface to be accessed via a standard HTTP/HTTPS port.

Further, it provides an authentication endpoint for accessing files in the `/static/` and `/media/` directories.

Finally, it provides a [Let's Encrypt](https://letsencrypt.org/) endpoint for automatic SSL certificate generation and renewal.

### Proxy Functionality

#### API and Web Requests

All API and web requests are reverse-proxied to the InvenTree django server. This allows the InvenTree web server to be accessed via a standard HTTP/HTTPS port, and allows the proxy server to handle SSL termination.

#### Static Files

Static files can be served without any need for authentication. In fact, they must be accessible *without* authentication, otherwise the unauthenticated views (such as the login screen) will not function correctly.

#### Media Files

It is highly recommended that the *media* files are served behind an authentication layer. This is because the media files are user-uploaded, and may contain sensitive information. Most modern web servers provide a way to serve files behind an authentication layer.

### Proxy Configuration

We provide some *sample* configuration files for getting your proxy server off the ground. The exact setup and configuration of your proxy server will depend on your specific requirements, and the software you choose to use. You may be integrating InvenTree with an existing web server, and the configuration may be different to the provided examples.

#### Example Configurations

**Caddy**

The [docker production example](./docker.md) provides an example using [Caddy](https://caddyserver.com) to serve *static* and *media* files, and redirecting other requests to the InvenTree web server itself. Caddy is a modern web server which is easy to configure and provides a number of useful features, including automatic SSL certificate generation.

You can find the sample Caddy configuration [here]({{ sourcefile("contrib/container/Caddyfile") }}).

**Nginx**

An alternative is to run nginx as the reverse proxy. A sample configuration file is provided [here]({{ sourcefile("contrib/container/nginx.conf") }}).

#### Extending the Proxy Configuration

You may wish to extend the proxy configuration to include additional features, based on your particular requirements. Some examples of where additional configuration may be required include:

- **Upstream Proxy**: You may be running the InvenTree server behind another proxy server, and need to configure the proxy server to forward requests to the upstream proxy.
- **Authentication**: You may wish to add an authentication layer to the proxy server, to restrict access to the InvenTree web interface.
- **SSL Termination**: You may wish to terminate SSL connections at the proxy server, and forward unencrypted traffic to the InvenTree web server.
- **Load Balancing**: You may wish to run multiple instances of the InvenTree web server, and use the proxy server to load balance between them.
- **Custom Error Pages**: You may wish to provide custom error pages for certain HTTP status codes.

!!! warning "No Support"
    We do not provide support for configuring your proxy server. The configuration of the proxy server is outside the scope of this documentation. If you require assistance with configuring your proxy server, please refer to the documentation for the specific software you are using.

#### Integrating with Existing Proxy

You may wish to integrate the InvenTree web server with an existing reverse proxy server. This is possible, but requires careful configuration to ensure that the static and media files are served correctly.

*Note: A custom configuration of the proxy server is outside the scope of this documentation!*

### Background Worker

The InvenTree background worker is responsible for handling [asynchronous tasks](../settings/tasks.md) which are not suitable for the main web server process. This includes tasks such as sending emails, generating reports, and other long-running tasks.

InvenTree uses the [django-q2](https://django-q2.readthedocs.io/en/master/) package to manage background tasks.

The background worker process is managed by the `inventree-worker` service in the [docker compose](./docker_install.md) setup. Note that this services runs a duplicate copy of the `inventree-server` container, but with a different entrypoint command which starts the background worker process.

#### Important Information

If the background worker process is not running, InvenTree will not be able to perform background tasks. This can lead to issues such as emails not being sent, or reports not being generated. Additionally, certain data may not be updated correctly if the background worker is not running.

!!! warning "Background Worker"
    The background worker process is a critical part of the InvenTree application stack. It is important that this process is running correctly in order for the InvenTree application to operate correctly.

#### Limitations

If the [cache server](#cache-server) is not running, the background worker will be limited to running a single threaded worker. This is because the background worker uses the cache server to manage task locking, and without a global cache server to communicate between processes, concurrency issues can occur.

### Cache Server

The InvenTree cache server is used to store temporary data which is shared between the InvenTree web server and the background worker processes. The cache server is also used to store task information, and to manage task locking between the background worker processes.

Using a cache server can significantly improve the performance of the InvenTree application, as it reduces the need to query the database for frequently accessed data.

InvenTree uses the [Redis](https://redis.io/) cache server to manage cache data. When running in docker, we use the official [redis image](https://hub.docker.com/_/redis).

!!! info "Redis on Docker"
    Docker adds an additional network layer - that might lead to lower performance than bare metal.
    To optimize and configure your redis deployment follow the [official docker guide](https://redis.io/docs/getting-started/install-stack/docker/#configuration).

!!! tip "Enable Cache"
    While a redis container is provided in the default configuration, by default it is not enabled in the InvenTree server. You can enable redis cache support by following the [caching configuration guide](./config.md#caching)
